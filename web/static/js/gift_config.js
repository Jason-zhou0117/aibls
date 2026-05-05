// gift_config.js - 礼物特效配置页面逻辑

class GiftConfigManager {
    constructor() {
        this.currentGift = null;
        this.activeGifts = [];
        this.inactiveGifts = [];
        this.activeFilter = '';
        this.inactiveFilter = '';
    }

    // ========== 工具函数 ==========
    showMessage(msg, isError = false) {
        const toast = document.createElement('div');
        toast.textContent = (isError ? '❌ ' : '✅ ') + msg;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: ${isError ? '#f44336' : '#4CAF50'};
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 14px;
            animation: fadeOut 3s ease forwards;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatPrice(priceCny) {
        if (!priceCny) return '0.00';
        return parseFloat(priceCny).toFixed(2);
    }

    // ========== 筛选函数 ==========
    filterGifts(gifts, keyword) {
        if (!keyword) return gifts;
        const lowerKeyword = keyword.toLowerCase();
        return gifts.filter(gift => 
            gift.gift_name.toLowerCase().includes(lowerKeyword) ||
            String(gift.gift_id).includes(lowerKeyword)
        );
    }

    // ========== API 调用 ==========
    async loadActiveGifts() {
        try {
            const resp = await fetch('/api/gifts/active');
            const data = await resp.json();
            if (data.code === 0) {
                this.activeGifts = data.data;
                this.renderActiveGiftList();
                const countEl = document.getElementById('activeCount');
                if (countEl) countEl.innerText = `(${this.activeGifts.length})`;
            }
        } catch (error) {
            console.error('加载上架礼物失败:', error);
        }
    }

    async loadInactiveGifts() {
        try {
            const resp = await fetch('/api/gifts/inactive');
            const data = await resp.json();
            if (data.code === 0) {
                this.inactiveGifts = data.data;
                this.renderInactiveGiftList();
                const countEl = document.getElementById('inactiveCount');
                if (countEl) countEl.innerText = `(${this.inactiveGifts.length})`;
            }
        } catch (error) {
            console.error('加载下架礼物失败:', error);
        }
    }

    async moveToActive(giftId) {
        try {
            const resp = await fetch(`/api/gifts/${giftId}/move_to_active`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage('已移动到上架列表');
                await this.loadActiveGifts();
                await this.loadInactiveGifts();
                return true;
            } else {
                this.showMessage(data.message, true);
                return false;
            }
        } catch (error) {
            this.showMessage('操作失败: ' + error.message, true);
            return false;
        }
    }

    async moveToInactive(giftId) {
        try {
            const resp = await fetch(`/api/gifts/${giftId}/move_to_inactive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage('已移动到下架列表');
                await this.loadActiveGifts();
                await this.loadInactiveGifts();
                if (this.currentGift && this.currentGift.gift_id === giftId) {
                    this.clearDetailPanel();
                }
                return true;
            } else {
                this.showMessage(data.message, true);
                return false;
            }
        } catch (error) {
            this.showMessage('操作失败: ' + error.message, true);
            return false;
        }
    }

    async loadGiftDetail(giftId) {
        try {
            const resp = await fetch(`/api/gifts/${giftId}`);
            const data = await resp.json();
            if (data.code === 0) {
                return data.data;
            }
            return null;
        } catch (error) {
            console.error('加载礼物详情失败:', error);
            return null;
        }
    }

    async loadGiftVideos(giftId) {
        try {
            const resp = await fetch(`/api/gifts/${giftId}/videos`);
            const data = await resp.json();
            if (data.code === 0) {
                this.renderVideoList(data.data);
                return data.data;
            }
            return [];
        } catch (error) {
            console.error('加载视频列表失败:', error);
            return [];
        }
    }

    async addGift(giftId, giftName, priceOrigin) {
        try {
            const resp = await fetch('/api/gifts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gift_id: parseInt(giftId),
                    gift_name: giftName,
                    price_origin: parseFloat(priceOrigin),
                    is_active: '1'
                })
            });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage('添加成功');
                await this.loadActiveGifts();
                return true;
            } else {
                this.showMessage(data.message, true);
                return false;
            }
        } catch (error) {
            this.showMessage('添加失败: ' + error.message, true);
            return false;
        }
    }

    async addVideo(giftId, title, url, path) {
        try {
            const resp = await fetch('/api/gift/videos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gift_id: parseInt(giftId),
                    title: title,
                    url: url,
                    path: path
                })
            });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage('视频添加成功');
                await this.loadGiftVideos(giftId);
                await this.loadActiveGifts();
                await this.loadInactiveGifts();
                // 刷新当前选中礼物的详情
                if (this.currentGift && this.currentGift.gift_id === giftId) {
                    const updatedGift = await this.loadGiftDetail(giftId);
                    if (updatedGift) this.updateDetailPanel(updatedGift);
                }
                return true;
            } else {
                this.showMessage(data.message, true);
                return false;
            }
        } catch (error) {
            this.showMessage('添加视频失败: ' + error.message, true);
            return false;
        }
    }

    async deleteVideo(videoUuid, giftId) {
        if (!confirm('确定删除这个特效视频吗？')) return;

        try {
            const resp = await fetch(`/api/gift/videos/${videoUuid}`, { method: 'DELETE' });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage('删除成功');
                await this.loadGiftVideos(giftId);
                await this.loadActiveGifts();
                await this.loadInactiveGifts();
                if (this.currentGift && this.currentGift.gift_id === giftId) {
                    const updatedGift = await this.loadGiftDetail(giftId);
                    if (updatedGift) this.updateDetailPanel(updatedGift);
                }
            } else {
                this.showMessage(data.message, true);
            }
        } catch (error) {
            this.showMessage('删除失败: ' + error.message, true);
        }
    }

    async testPlayVideo(giftId, videoId = null) {
        try {
            const body = { gift_id: parseInt(giftId) };
            if (videoId) body.video_id = videoId;
            
            const resp = await fetch('/api/gift/video/test_play', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await resp.json();
            if (data.code === 0) {
                this.showMessage(data.message);
            } else {
                this.showMessage(data.message, true);
            }
        } catch (error) {
            this.showMessage('测试播放失败: ' + error.message, true);
        }
    }

    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('video', file);

        try {
            const resp = await fetch('/api/upload/gift_video', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.code === 0) {
                return data.data;
            } else {
                this.showMessage(data.message, true);
                return null;
            }
        } catch (error) {
            this.showMessage('上传失败: ' + error.message, true);
            return null;
        }
    }

    // ========== 渲染函数 ==========
    renderActiveGiftList() {
        const container = document.getElementById('activeGiftList');
        if (!container) return;

        const filtered = this.filterGifts(this.activeGifts, this.activeFilter);

        if (!filtered.length) {
            container.innerHTML = '<div class="empty-tip">暂无上架礼物<br>点击 [+] 添加</div>';
            return;
        }

        container.innerHTML = filtered.map(gift => `
            <div class="gift-item ${this.currentGift?.gift_id === gift.gift_id ? 'active' : ''}"
                 data-gift-id="${gift.gift_id}"
                 onclick="giftManager.selectGift(${gift.gift_id})">
                <div class="gift-icon">
                    ${gift.gift_icon ? `<img src="${gift.gift_icon}" alt="icon">` : '🎁'}
                </div>
                <div class="gift-info">
                    <div class="gift-name">${this.escapeHtml(gift.gift_name)}</div>
                    <div class="gift-id">ID: ${gift.gift_id}</div>
                    <div class="gift-price">¥${this.formatPrice(gift.price_cny)}</div>
                    ${gift.has_video === '1' ? '<div class="gift-badge">🎬 有特效</div>' : ''}
                </div>
                <div class="gift-actions">
                    <button class="move-btn move-down-btn" onclick="event.stopPropagation(); giftManager.moveToInactive(${gift.gift_id})" title="下架">⬇️ 下架</button>
                </div>
            </div>
        `).join('');
    }

    renderInactiveGiftList() {
        const container = document.getElementById('inactiveGiftList');
        if (!container) return;

        const filtered = this.filterGifts(this.inactiveGifts, this.inactiveFilter);

        if (!filtered.length) {
            container.innerHTML = '<div class="empty-tip">暂无下架礼物</div>';
            return;
        }

        container.innerHTML = filtered.map(gift => `
            <div class="gift-item ${this.currentGift?.gift_id === gift.gift_id ? 'active' : ''}"
                 data-gift-id="${gift.gift_id}"
                 onclick="giftManager.selectGift(${gift.gift_id})">
                <div class="gift-icon">
                    ${gift.gift_icon ? `<img src="${gift.gift_icon}" alt="icon">` : '🎁'}
                </div>
                <div class="gift-info">
                    <div class="gift-name">${this.escapeHtml(gift.gift_name)}</div>
                    <div class="gift-id">ID: ${gift.gift_id}</div>
                    <div class="gift-price">¥${this.formatPrice(gift.price_cny)}</div>
                    ${gift.has_video === '1' ? '<div class="gift-badge">🎬 有特效</div>' : ''}
                </div>
                <div class="gift-actions">
                    <button class="move-btn move-up-btn" onclick="event.stopPropagation(); giftManager.moveToActive(${gift.gift_id})" title="上架">⬆️ 上架</button>
                </div>
            </div>
        `).join('');
    }

    renderVideoList(videos) {
        const container = document.getElementById('videoList');
        if (!container) return;
        
        if (!videos || videos.length === 0) {
            container.innerHTML = '<div class="empty-tip">暂无特效视频<br>点击 [+] 添加</div>';
            return;
        }

        container.innerHTML = videos.map(video => `
            <div class="video-item">
                <div class="video-item-header">
                    <span class="video-name">🎥 ${this.escapeHtml(video.title)}</span>
                    <button class="video-delete" onclick="giftManager.deleteVideo('${video.id}', ${video.gift_id})" title="删除">🗑</button>
                </div>
                <div class="video-url">URL: ${this.escapeHtml(video.url)}</div>
                ${video.path ? `<div class="video-path">路径: ${this.escapeHtml(video.path)}</div>` : ''}
                <button class="test-play-btn" onclick="giftManager.testPlayVideo(${video.gift_id}, '${video.id}')">▶ 测试播放</button>
            </div>
        `).join('');
    }

    updateDetailPanel(gift) {
        const profileIcon = document.getElementById('profileIcon');
        const profileName = document.getElementById('profileName');
        const profileId = document.getElementById('profileId');
        const profilePrice = document.getElementById('profilePrice');

        if (profileIcon) {
            profileIcon.innerHTML = gift.gift_icon ? `<img src="${gift.gift_icon}" alt="icon">` : '<span style="font-size: 48px;">🎁</span>';
        }
        if (profileName) profileName.textContent = gift.gift_name;
        if (profileId) profileId.textContent = `礼物ID: ${gift.gift_id}`;
        if (profilePrice) profilePrice.textContent = `价格: ¥${this.formatPrice(gift.price_cny)} (${gift.price_gold} 电池)`;
    }

    clearDetailPanel() {
        const profileIcon = document.getElementById('profileIcon');
        const profileName = document.getElementById('profileName');
        const profileId = document.getElementById('profileId');
        const profilePrice = document.getElementById('profilePrice');
        const videoList = document.getElementById('videoList');

        if (profileIcon) profileIcon.innerHTML = '<span style="font-size: 48px;">🎁</span>';
        if (profileName) profileName.textContent = '未选择礼物';
        if (profileId) profileId.textContent = '';
        if (profilePrice) profilePrice.textContent = '';
        if (videoList) videoList.innerHTML = '<div class="empty-tip">请先选择礼物，然后添加视频</div>';
        this.currentGift = null;
    }

    // ========== 交互函数 ==========
    async selectGift(giftId) {
        console.log('点击选中礼物 ID:', giftId);

        if (!giftId) {
            console.error('礼物ID无效');
            return;
        }

        try {
            const resp = await fetch(`/api/gifts/${giftId}`);
            const data = await resp.json();

            if (data.code === 0) {
                this.currentGift = data.data;
                this.updateDetailPanel(data.data);
                await this.loadGiftVideos(giftId);
                // 刷新列表高亮
                this.renderActiveGiftList();
                this.renderInactiveGiftList();
            } else {
                console.error('加载失败:', data.message);
                this.showMessage(data.message, true);
            }
        } catch (error) {
            console.error('加载礼物详情失败:', error);
            this.showMessage('加载礼物详情失败', true);
        }
    }

    onActiveSearch(e) {
        this.activeFilter = e.target.value;
        this.renderActiveGiftList();
    }

    onInactiveSearch(e) {
        this.inactiveFilter = e.target.value;
        this.renderInactiveGiftList();
    }

    showAddGiftModal() {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">📝 添加礼物</div>
                <div class="modal-form-group">
                    <label class="modal-label">礼物ID</label>
                    <input type="number" class="modal-input" id="giftIdInput" placeholder="请输入礼物ID（数字）">
                </div>
                <div class="modal-form-group">
                    <label class="modal-label">礼物名称</label>
                    <input type="text" class="modal-input" id="giftNameInput" placeholder="请输入礼物名称">
                </div>
                <div class="modal-form-group">
                    <label class="modal-label">礼物原价（电池）</label>
                    <input type="number" step="1" class="modal-input" id="priceOriginInput" placeholder="请输入礼物原价（电池）">
                </div>
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                    <button class="modal-btn modal-btn-primary" id="confirmBtn">添加</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const close = () => overlay.remove();

        overlay.querySelector('#confirmBtn').onclick = async () => {
            const giftId = overlay.querySelector('#giftIdInput').value.trim();
            const giftName = overlay.querySelector('#giftNameInput').value.trim();
            const priceOrigin = overlay.querySelector('#priceOriginInput').value.trim();

            if (!giftId || !giftName || !priceOrigin) {
                this.showMessage('请填写完整信息', true);
                return;
            }

            close();
            await this.addGift(giftId, giftName, priceOrigin);
        };
        overlay.querySelector('#cancelBtn').onclick = close;
        overlay.onclick = (e) => { if (e.target === overlay) close(); };
    }

    showAddVideoModal() {
        if (!this.currentGift) {
            this.showMessage('请先选择礼物', true);
            return;
        }

        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">📤 添加入场特效视频</div>
                <div class="modal-form-group">
                    <label class="modal-label">选择视频文件</label>
                    <div class="file-input-wrapper">
                        <input type="file" id="videoFile" accept="video/mp4,video/webm">
                        <div class="file-input-display" id="fileDisplay">点击选择文件</div>
                    </div>
                </div>
                <div class="modal-form-group">
                    <label class="modal-label">视频名称</label>
                    <input type="text" class="modal-input" id="videoNameInput" placeholder="请输入视频名称">
                </div>
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                    <button class="modal-btn modal-btn-primary" id="confirmBtn">上传并添加</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const fileInput = overlay.querySelector('#videoFile');
        const fileDisplay = overlay.querySelector('#fileDisplay');
        const videoNameInput = overlay.querySelector('#videoNameInput');

        fileInput.onchange = () => {
            if (fileInput.files.length > 0) {
                fileDisplay.textContent = fileInput.files[0].name;
                if (!videoNameInput.value) {
                    videoNameInput.value = fileInput.files[0].name.replace(/\.[^/.]+$/, '');
                }
            } else {
                fileDisplay.textContent = '点击选择文件';
            }
        };

        const close = () => overlay.remove();

        overlay.querySelector('#confirmBtn').onclick = async () => {
            const file = fileInput.files[0];
            let videoName = videoNameInput.value.trim();

            if (!file) {
                this.showMessage('请选择视频文件', true);
                return;
            }
            if (!videoName) {
                videoName = file.name.replace(/\.[^/.]+$/, '');
            }

            this.showMessage('上传中...');
            const uploadResult = await this.uploadVideo(file);
            if (!uploadResult) return;

            await this.addVideo(this.currentGift.gift_id, videoName, uploadResult.url, uploadResult.path);
            close();
        };
        overlay.querySelector('#cancelBtn').onclick = close;
    }

    async syncGiftInfos(){
            try {
                const response = await fetch('/api/gift/refresh');

                const data = await response.json();

                if (data.code === 0) {
                    this.showMessage(`✅ 同步B站礼物信息成功`, false);
                } else {
                    this.showMessage(`❌ 同步B站礼物信息失败: ${data.message}`, true);
                }
            } catch (error) {
                console.error('同步B站礼物信息失败:', error);
                this.showMessage('❌ 请求失败: ' + error.message, true);
            }
        }

    // ========== 初始化 ==========
    async init() {
        await this.loadActiveGifts();
        await this.loadInactiveGifts();
        this.bindEvents();
    }

    bindEvents() {
//        const addGiftBtn = document.getElementById('addGiftBtn');
        const addVideoBtn = document.getElementById('addVideoBtn');
        const selectGiftBtn = document.getElementById('selectGiftBtn');
        const activeSearch = document.getElementById('activeSearch');
        const inactiveSearch = document.getElementById('inactiveSearch');

//        if (addGiftBtn) addGiftBtn.onclick = () => this.showAddGiftModal();
        if (addVideoBtn) addVideoBtn.onclick = () => this.showAddVideoModal();
        if (selectGiftBtn) selectGiftBtn.onclick = () => this.syncGiftInfos();
        if (activeSearch) activeSearch.oninput = (e) => this.onActiveSearch(e);
        if (inactiveSearch) inactiveSearch.oninput = (e) => this.onInactiveSearch(e);
    }
}

let giftManager = null;

document.addEventListener('DOMContentLoaded', () => {
    giftManager = new GiftConfigManager();
    giftManager.init();
});