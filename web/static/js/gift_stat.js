// gift_stat.js - 礼物统计页面逻辑

class GiftStatManager {
    constructor() {
        this.currentMonth = '';
        this.availableMonths = [];
        this.currentBlindBox = null;
        this.blindBoxList = [];
        this.userRankList = [];

        // 绑定事件
        this.bindEvents();
    }

    // ========== 工具函数 ==========
    showLoading() {
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"></div>';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

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

    formatPrice(price) {
        if (price === undefined || price === null) return '0.00';
        return parseFloat(price).toFixed(2);
    }

    // ========== API 调用 ==========
    async loadMonths() {
        try {
            const resp = await fetch('/api/months');
            const data = await resp.json();
            if (data.code === 0) {
                this.availableMonths = data.data;
                this.renderMonthSelect();
                if (this.availableMonths.length > 0 && !this.currentMonth) {
                    this.currentMonth = this.availableMonths[0];
                    await this.loadAllData();
                }
            }
        } catch (error) {
            console.error('加载月份失败:', error);
            this.showMessage('加载月份失败', true);
        }
    }

    async loadSummary() {
        try {
            const resp = await fetch(`/api/summary?month=${this.currentMonth}`);
            const data = await resp.json();
            if (data.code === 0) {
                this.renderSummary(data.data);
            } else {
                this.showMessage(data.message, true);
            }
        } catch (error) {
            console.error('加载汇总失败:', error);
            this.showMessage('加载汇总失败', true);
        }
    }

    async loadBlindBoxes() {
        try {
            const resp = await fetch(`/api/blind_boxes?month=${this.currentMonth}`);
            const data = await resp.json();
            if (data.code === 0) {
                this.blindBoxList = data.data;
                this.renderBlindBoxList();
            }
        } catch (error) {
            console.error('加载盲盒列表失败:', error);
            this.showMessage('加载盲盒列表失败', true);
        }
    }

    async loadUserRank(blindGiftId) {
        try {
            const resp = await fetch(`/api/user_rank?month=${this.currentMonth}&blind_gift_id=${blindGiftId}`);
            const data = await resp.json();
            if (data.code === 0) {
                this.userRankList = data.data;
                this.renderUserRankList();
            } else {
                this.userRankList = [];
                this.renderUserRankList();
            }
        } catch (error) {
            console.error('加载用户排名失败:', error);
            this.userRankList = [];
            this.renderUserRankList();
        }
    }

    async loadAllData() {
        if (!this.currentMonth) return;

        this.showLoading();
        try {
            await Promise.all([
                this.loadSummary(),
                this.loadBlindBoxes()
            ]);
        } finally {
            this.hideLoading();
        }
    }

    // ========== 渲染函数 ==========
    renderMonthSelect() {
        const select = document.getElementById('monthSelect');
        if (!select) return;

        select.innerHTML = this.availableMonths.map(month =>
            `<option value="${month}" ${this.currentMonth === month ? 'selected' : ''}>${month}</option>`
        ).join('');
    }

    renderSummary(data) {
        // 区域1：礼物总数和总价值
        document.getElementById('giftTotalNum').textContent = data.gift_total_num || 0;
        document.getElementById('giftTotalCny').textContent = `¥${this.formatPrice(data.gift_total_cny)}`;

        // 区域2：盲盒统计
        document.getElementById('blindGiftNum').textContent = data.blind_gift_num || 0;
        document.getElementById('blindGiftTotal').textContent = `¥${this.formatPrice(data.blind_gift_total_cny)}`;

        const scopeElement = document.getElementById('blindGiftScope');
        const scopeValue = data.blind_gift_scope_cny || 0;
        scopeElement.textContent = `¥${this.formatPrice(Math.abs(scopeValue))}`;
        scopeElement.className = scopeValue >= 0 ? 'stat-card-value positive' : 'stat-card-value negative';

        // 区域3：投喂榜首
        const firstUser = data.first_user;
        const firstUserContainer = document.getElementById('firstUserInfo');
        if (firstUser && firstUser.uid) {
            firstUserContainer.innerHTML = `
                <div class="user-card">
                    <div class="user-avatar-large">
                        ${firstUser.face ? `<img src="${firstUser.face}" alt="头像" onerror="this.parentElement.innerHTML='👤'">` : '👤'}
                    </div>
                    <div class="user-info-large">
                        <div class="user-name-large">${this.escapeHtml(firstUser.name)}</div>
                        <div class="user-uid-large">UID: ${firstUser.uid}</div>
                    </div>
                    <div class="user-value-large">¥${this.formatPrice(firstUser.total_cny)}</div>
                </div>
            `;
        } else {
            firstUserContainer.innerHTML = '<div class="no-user-tip">暂无数据</div>';
        }

        // 区域4：盲盒盈亏榜首
        const blindFirstUser = data.blind_first_user;
        const blindFirstContainer = document.getElementById('blindFirstUserInfo');
        if (blindFirstUser && blindFirstUser.uid) {
            blindFirstContainer.innerHTML = `
                <div class="user-card">
                    <div class="user-avatar-large">
                        ${blindFirstUser.face ? `<img src="${blindFirstUser.face}" alt="头像" onerror="this.parentElement.innerHTML='👤'">` : '👤'}
                    </div>
                    <div class="user-info-large">
                        <div class="user-name-large">${this.escapeHtml(blindFirstUser.name)}</div>
                        <div class="user-uid-large">UID: ${blindFirstUser.uid}</div>
                    </div>
                    <div class="user-value-large ${blindFirstUser.scope_cny >= 0 ? 'positive' : 'negative'}">
                        ¥${this.formatPrice(Math.abs(blindFirstUser.scope_cny))}
                    </div>
                </div>
            `;
        } else {
            blindFirstContainer.innerHTML = '<div class="no-user-tip">暂无数据</div>';
        }
    }

    renderBlindBoxList() {
        const container = document.getElementById('blindBoxList');
        if (!container) return;

        if (!this.blindBoxList.length) {
            container.innerHTML = '<div class="empty-tip">暂无盲盒数据</div>';
            return;
        }

        container.innerHTML = this.blindBoxList.map(box => `
            <div class="blind-item ${this.currentBlindBox === box.blind_gift_id ? 'active' : ''}"
                 data-id="${box.blind_gift_id}"
                 onclick="giftStatManager.selectBlindBox(${box.blind_gift_id})">
                <div class="blind-name">${this.escapeHtml(box.blind_gift_name || '未知盲盒')}</div>
                <div class="blind-id">ID: ${box.blind_gift_id}</div>
                <div class="blind-stats">
                    <span>数量: ${box.total_num}</span>
                    <span>投入: ¥${this.formatPrice(box.total_input_cny)}</span>
                    <span>产出: ¥${this.formatPrice(box.total_output_cny)}</span>
                    <span>盈亏: <span class="scope-value ${box.scope_cny >= 0 ? 'positive' : 'negative'}">¥${this.formatPrice(Math.abs(box.scope_cny))}</span></span>
                </div>
            </div>
        `).join('');
    }

    renderUserRankList() {
        const container = document.getElementById('userRankList');
        if (!container) return;

        if (!this.userRankList.length) {
            container.innerHTML = '<div class="empty-tip">请先选择盲盒</div>';
            return;
        }

        container.innerHTML = this.userRankList.map((user, index) => {
            const rank = index + 1;
            let rankClass = '';
            if (rank === 1) rankClass = 'top1';
            else if (rank === 2) rankClass = 'top2';
            else if (rank === 3) rankClass = 'top3';

            return `
                <div class="rank-item">
                    <div class="rank-number ${rankClass}">${rank}</div>
                    <div class="rank-avatar">
                        ${user.face ? `<img src="${user.face}" alt="头像" onerror="this.parentElement.innerHTML='👤'">` : '👤'}
                    </div>
                    <div class="rank-info">
                        <div class="rank-name">${this.escapeHtml(user.name)}</div>
                        <div class="rank-uid">UID: ${user.uid}</div>
                    </div>
                    <div class="rank-stats">
                        <div class="rank-num">数量: ${user.gift_num}</div>
                        <div class="rank-value">投入: ¥${this.formatPrice(user.total_input_cny)}</div>
                        <div class="rank-value">产出: ¥${this.formatPrice(user.total_output_cny)}</div>
                        <div class="rank-value ${user.scope_cny >= 0 ? 'positive' : 'negative'}">
                            盈亏: ¥${this.formatPrice(Math.abs(user.scope_cny))}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ========== 交互函数 ==========
    async selectBlindBox(blindGiftId) {
        this.currentBlindBox = blindGiftId;
        this.renderBlindBoxList();

        this.showLoading();
        try {
            await this.loadUserRank(blindGiftId);
        } finally {
            this.hideLoading();
        }
    }

    async onMonthChange() {
        const select = document.getElementById('monthSelect');
        this.currentMonth = select.value;
        this.currentBlindBox = null;
        await this.loadAllData();
        this.renderUserRankList();
    }

    async refresh() {
        this.currentBlindBox = null;
        await this.loadAllData();
        this.renderUserRankList();
        this.showMessage('数据已刷新');
    }

    // ========== 事件绑定 ==========
    bindEvents() {
        // 月份选择器变化
        const monthSelect = document.getElementById('monthSelect');
        if (monthSelect) {
            monthSelect.onchange = () => this.onMonthChange();
        }

        // 刷新按钮
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.refresh();
        }
    }

    // ========== 初始化 ==========
    async init() {
        await this.loadMonths();
        // 如果没有数据，显示空状态
    }
}

// 全局实例
let giftStatManager = null;

document.addEventListener('DOMContentLoaded', () => {
    giftStatManager = new GiftStatManager();
    giftStatManager.init();
});