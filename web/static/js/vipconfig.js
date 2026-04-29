 // ========== 全局变量 ==========
        let currentUser = null;      // 当前选中的用户
        let vipUsers = [];            // VIP用户列表

        // ========== 工具函数 ==========
        function showMessage(msg, isError = false) {
            // 创建临时提示
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

        function clearRightPanel() {
            // 清空右侧用户信息
            const profileAvatar = document.getElementById('profileAvatar');
            const profileName = document.getElementById('profileName');
            const profileUid = document.getElementById('profileUid');

            profileAvatar.innerHTML = '<span style="font-size: 40px;">👤</span>';
            profileName.textContent = '未选择用户';
            profileUid.textContent = '';

            // 清空视频列表
            const videoList = document.getElementById('videoList');
            videoList.innerHTML = '<div class="empty-tip">请先选择用户，然后添加视频</div>';

            currentUser = null;
        }

        function selectUser(user) {
            currentUser = user;

            // 更新左侧选中状态
            document.querySelectorAll('.user-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.uid === user.userid) {
                    item.classList.add('active');
                }
            });

            // 更新右侧用户信息
            const profileAvatar = document.getElementById('profileAvatar');
            const profileName = document.getElementById('profileName');
            const profileUid = document.getElementById('profileUid');

            if (user.face && user.face.startsWith('http')) {
                profileAvatar.innerHTML = `<img src="${user.face}" alt="头像">`;
            } else {
                profileAvatar.innerHTML = `<span style="font-size: 40px;">${user.name?.charAt(0) || '👤'}</span>`;
            }
            profileName.textContent = user.name || user.nickname || '未知用户';
            profileUid.textContent = `UID: ${user.userid}`;

            // 加载视频列表
            loadUserVideos(user.userid);
        }

        // ========== API 调用 ==========
        async function loadUserList() {
            try {
                const resp = await fetch('/api/vip/users');
                const data = await resp.json();
                if (data.code === 0) {
                    vipUsers = data.data;
                    renderUserList();
                }
            } catch (error) {
                console.error('加载用户列表失败:', error);
                showMessage('加载用户列表失败', true);
            }
        }

        async function loadUserVideos(uid) {
            try {
                const resp = await fetch(`/api/vip/users/${uid}/videos`);
                const data = await resp.json();
                if (data.code === 0) {
                    renderVideoList(data.data);
                }
            } catch (error) {
                console.error('加载视频列表失败:', error);
                showMessage('加载视频列表失败', true);
            }
        }

        async function addUserFromBili(uid) {
            try {
                showMessage('正在获取用户信息...');
//                const resp = await fetch(`/api/bili/user/${uid}`);
//                const data = await resp.json();
//
//                if (data.code !== 0) {
//                    showMessage(data.message, true);
//                    return false;
//                }

//                const userInfo = data.data;
                const addResp = await fetch('/api/vip/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        uid: uid
                    })
                });
                const addData = await addResp.json();

                if (addData.code === 0) {
                    showMessage(`成功添加用户: ${addData.data.uname}`);
                    await loadUserList();
                    // 自动选中新添加的用户
                    const newUser = vipUsers.find(u => u.userid === addData.data.userid);
                    if (newUser) {
                        selectUser(newUser);
                    }
                    return true;
                } else {
                    showMessage(addData.message, true);
                    return false;
                }
            } catch (error) {
                showMessage('添加失败: ' + error.message, true);
                return false;
            }
        }

        async function deleteUser(uid, name) {
            if (!confirm(`确定删除用户 "${name}" 的所有配置吗？`)) return;

            try {
                const resp = await fetch(`/api/vip/users/${uid}`, { method: 'DELETE' });
                const data = await resp.json();
                if (data.code === 0) {
                    showMessage('删除成功');
                    if (currentUser && currentUser.userid === uid) {
                        clearRightPanel();
                    }
                    await loadUserList();
                } else {
                    showMessage(data.message, true);
                }
            } catch (error) {
                showMessage('删除失败: ' + error.message, true);
            }
        }

        async function deleteVideo(videoId) {
            if (!confirm('确定删除这个视频吗？')) return;

            try {
                const resp = await fetch(`/api/vip/videos/${videoId}`, { method: 'DELETE' });
                const data = await resp.json();
                if (data.code === 0) {
                    showMessage('删除成功');
                    if (currentUser) {
                        await loadUserVideos(currentUser.userid);
                    }
                } else {
                    showMessage(data.message, true);
                }
            } catch (error) {
                showMessage('删除失败: ' + error.message, true);
            }
        }

        // ========== 弹窗 ==========
        function showAddUserPrompt() {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal">
                    <div class="modal-title">📝 添加VIP用户</div>
                    <div class="modal-form-group">
                        <label class="modal-label">用户UID</label>
                        <input type="text" class="modal-input" id="uidInput" placeholder="请输入B站用户UID">
                    </div>
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                        <button class="modal-btn modal-btn-primary" id="confirmBtn">获取并添加</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            const input = overlay.querySelector('#uidInput');
            input.focus();

            const close = () => overlay.remove();

            overlay.querySelector('#confirmBtn').onclick = async () => {
                const uid = input.value.trim();
                if (!uid) {
                    showMessage('请输入UID', true);
                    return;
                }
                close();
                await addUserFromBili(uid);
            };
            overlay.querySelector('#cancelBtn').onclick = close;
            overlay.onclick = (e) => { if (e.target === overlay) close(); };
        }

        function showUploadModal() {
            if (!currentUser) {
                showMessage('请先选择用户', true);
                return;
            }

            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal">
                    <div class="modal-title">📤 新增入场视频</div>
                    <div class="modal-form-group">
                        <label class="modal-label">选择视频文件</label>
                        <div class="file-input-wrapper">
                            <input type="file" id="videoFile" accept="video/mp4,video/webm,video/avi,video/mov,video/mkv">
                            <div class="file-input-display" id="fileDisplay">点击选择文件</div>
                        </div>
                    </div>
                    <div class="modal-form-group">
                        <label class="modal-label">视频名称</label>
                        <input type="text" class="modal-input" id="videoName" placeholder="例如：VIP欢迎视频">
                    </div>
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                        <button class="modal-btn modal-btn-primary" id="confirmBtn">提交</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            const fileInput = overlay.querySelector('#videoFile');
            const fileDisplay = overlay.querySelector('#fileDisplay');
            const videoNameInput = overlay.querySelector('#videoName');

            fileInput.onchange = () => {
                if (fileInput.files.length > 0) {
                    fileDisplay.textContent = fileInput.files[0].name;
                } else {
                    fileDisplay.textContent = '点击选择文件';
                }
            };

            const close = () => overlay.remove();

            overlay.querySelector('#confirmBtn').onclick = async () => {
                const file = fileInput.files[0];
                let videoName = videoNameInput.value.trim();

                if (!file) {
                    showMessage('请选择视频文件', true);
                    return;
                }

                // 如果没有填写视频名称，使用文件名（不含扩展名）
                if (!videoName) {
                    videoName = file.name.replace(/\.[^/.]+$/, '');
                }

                // 上传文件
                const formData = new FormData();
                formData.append('video', file);

                try {
                    showMessage('上传中...');
                    const uploadResp = await fetch('/api/upload/video', {
                        method: 'POST',
                        body: formData
                    });
                    const uploadData = await uploadResp.json();

                    if (uploadData.code !== 0) {
                        showMessage(uploadData.message, true);
                        return;
                    }

                    // 添加视频记录
                    const addResp = await fetch('/api/vip/videos', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            uid: currentUser.userid,
                            video_name: videoName,
                            video_url: uploadData.data.url,
                            video_path: uploadData.data.path
                        })
                    });
                    const addData = await addResp.json();

                    if (addData.code === 0) {
                        showMessage('添加成功');
                        close();
                        if (currentUser) {
                            await loadUserVideos(currentUser.userid);
                        }
                        // 刷新左侧列表（更新视频计数）
                        await loadUserList();
                    } else {
                        showMessage(addData.message, true);
                    }
                } catch (error) {
                    showMessage('操作失败: ' + error.message, true);
                }
            };
            overlay.querySelector('#cancelBtn').onclick = close;
            overlay.onclick = (e) => { if (e.target === overlay) close(); };
        }

        // ========== 渲染函数 ==========
        function renderUserList() {
            const container = document.getElementById('userList');
            if (!vipUsers.length) {
                container.innerHTML = '<div class="empty-tip">暂无VIP用户配置<br>点击 [+] 添加</div>';
                return;
            }

            container.innerHTML = vipUsers.map(user => `
                <div class="user-item ${currentUser?.userid === user.userid ? 'active' : ''}" data-uid="${user.userid}">
                    <div class="user-avatar-small">
                        ${user.face && user.face.startsWith('http') ?
                            `<img src="${user.face}" alt="头像">` :
                            `<span style="font-size: 20px;">${user.name?.charAt(0) || '👤'}</span>`}
                    </div>
                    <div class="user-info-small" onclick="selectUserById('${user.userid}')">
                        <div class="user-name">${escapeHtml(user.name || user.nickname || '未知')}</div>
                        <div class="user-uid">UID: ${user.userid}</div>
                    </div>
                    <div class="user-actions">
                        <button class="action-icon delete" onclick="event.stopPropagation(); deleteUser('${user.userid}', '${escapeHtml(user.name || user.userid)}')" title="删除">🗑</button>
                    </div>
                </div>
            `).join('');
        }

        function renderVideoList(videos) {
            const container = document.getElementById('videoList');
            if (!videos || videos.length === 0) {
                container.innerHTML = '<div class="empty-tip">暂无入场视频<br>点击 [+] 添加</div>';
                return;
            }

            container.innerHTML = videos.map(video => `
                <div class="video-item">
                    <div class="video-item-header">
                        <span class="video-name" onclick="testPlayVideo('${escapeHtml(video.url)}','${escapeHtml(video.id)}',  '${escapeHtml(video.title || video.name)}')" style="cursor: pointer;">
                        🎥 ${escapeHtml(video.title || video.name)} &nbsp;&nbsp;[点我可以测试播放视频]</span>
                        <button class="video-delete" onclick="deleteVideo('${video.id}')" title="删除">🗑</button>
                    </div>
                    <div class="video-url">URL: ${escapeHtml(video.url || '')}</div>
                    ${video.path ? `<div class="video-path">路径: ${escapeHtml(video.path)}</div>` : ''}
                </div>
            `).join('');
        }

        // 测试播放函数
        async function testPlayVideo(videoUrl, videoid,videoName) {
            console.log('测试播放:', videoName, videoUrl);

            // 显示加载提示
            showMessage(`正在发送播放指令: ${videoName}...`, false);

            try {
                const response = await fetch('/api/video/test_play', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        video_url: videoUrl,
                        videoid:videoid,
                        video_name: videoName
                    })
                });

                const data = await response.json();

                if (data.code === 0) {
                    showMessage(`✅ 正在播放: ${videoName}`, false);
                } else {
                    showMessage(`❌ 播放失败: ${data.message}`, true);
                }
            } catch (error) {
                console.error('测试播放失败:', error);
                showMessage('❌ 请求失败: ' + error.message, true);
            }
        }

        function selectUserById(uid) {
            const user = vipUsers.find(u => u.userid === uid);
            if (user) {
                selectUser(user);
            }
        }

        function editUser(uid) {
            const user = vipUsers.find(u => u.userid === uid);
            if (user) {
                selectUser(user);
                showMessage(`正在编辑用户: ${user.name}，可在右侧修改信息`, false);
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function openVideoPlayer() {
            window.open('/static/video_player.html', 'VideoPlayer', 'width=800,height=600');
        }

        // ========== 事件绑定 ==========
        function bindEvents() {
            document.getElementById('addUserBtn').onclick = showAddUserPrompt;
            document.getElementById('addVideoBtn').onclick = showUploadModal;
            document.getElementById('selectUserBtn').onclick = changeUser;
        }

        function changeUser(){

        }

        // ========== 初始化 ==========
        async function init() {
            bindEvents();
            await loadUserList();
        }
