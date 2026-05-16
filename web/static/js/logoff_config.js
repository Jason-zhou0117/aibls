// ========== 全局变量 ==========
let currentUser = null;      // 当前选中的用户
let logoffUsers = [];         // 挂机用户列表
let pollTimer = null;         // 二维码轮询定时器
let isPolling = false;        // 是否正在轮询

// ========== 工具函数 ==========
function showMessage(msg, isError = false) {
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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(timeStr) {
    if (!timeStr) return '未设置';
    if (timeStr.length === 5) return timeStr;
    return timeStr.substring(0, 5);
}

// 清空右侧面板
function clearRightPanel() {
    const profileAvatar = document.getElementById('profileAvatar');
    const profileName = document.getElementById('profileName');
    const profileUid = document.getElementById('profileUid');
    const toggleSwitch = document.getElementById('isOpenToggle');
    const toggleStatus = document.getElementById('toggleStatus');

    if (profileAvatar) profileAvatar.innerHTML = '<span style="font-size: 40px;">👤</span>';
    if (profileName) profileName.textContent = '未选择用户';
    if (profileUid) profileUid.textContent = '';
    if (toggleSwitch) toggleSwitch.checked = false;
    if (toggleStatus) toggleStatus.textContent = '否';

    const logoffList = document.getElementById('logoffList');
    if (logoffList) logoffList.innerHTML = '<div class="empty-tip">请先选择用户</div>';

    currentUser = null;
}

// 获取 is_open 的布尔值（后端返回 "Y" 或 "N"）
function getIsOpenValue(user) {
    if (!user || user.is_open === undefined) return false;
    // 后端返回 "Y" 表示是，"N" 表示否
    return user.is_open === "Y" || user.is_open === "y" || user.is_open === true || user.is_open === 1;
}

// 将布尔值转换为后端需要的 "Y"/"N"
function getIsOpenString(isChecked) {
    return isChecked ? "Y" : "N";
}

// 选中用户（核心函数）
function selectUser(user) {
    console.log('========== selectUser 被调用 ==========');
    console.log('用户对象:', user);
    console.log('user.is_open 原始值:', user.is_open, '类型:', typeof user.is_open);

    if (!user) {
        console.warn('用户对象为空');
        return;
    }

    currentUser = user;

    // 更新左侧选中状态
    document.querySelectorAll('.user-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.uid == user.userid) {
            item.classList.add('active');
        }
    });

    // 更新右侧用户信息
    const profileAvatar = document.getElementById('profileAvatar');
    const profileName = document.getElementById('profileName');
    const profileUid = document.getElementById('profileUid');
    const toggleSwitch = document.getElementById('isOpenToggle');
    const toggleStatus = document.getElementById('toggleStatus');

    if (profileAvatar) {
        if (user.face && user.face.startsWith('http')) {
            profileAvatar.innerHTML = `<img src="${user.face}" alt="头像" onerror="this.parentElement.innerHTML='<span style=\'font-size:40px;\'>👤</span>'">`;
        } else {
            profileAvatar.innerHTML = `<span style="font-size: 40px;">${(user.name || user.nickname || '?').charAt(0)}</span>`;
        }
    }

    if (profileName) profileName.textContent = user.name || user.nickname || '未知用户';
    if (profileUid) profileUid.textContent = `UID: ${user.userid}`;

    // 计算 is_open 布尔值（兼容 "Y"/"N"）
    const isOpen = getIsOpenValue(user);
    console.log('计算后的开关状态:', isOpen);

    if (toggleSwitch) {
        toggleSwitch.checked = isOpen;
    }
    if (toggleStatus) {
        toggleStatus.textContent = isOpen ? '是' : '否';
    }

    // 加载挂机设定列表
    loadUserLogoffs(user.userid);
}

// 通过ID选中用户
function selectUserById(uid) {
    console.log('selectUserById 被调用, uid:', uid);
    const user = logoffUsers.find(u => u.userid == uid);
    if (user) {
        selectUser(user);
    } else {
        console.warn('未找到用户:', uid);
    }
}

// ========== API 调用 ==========

// 获取挂机用户列表
async function loadUserList() {
    try {
        const resp = await fetch('/logoff_api/users');
        const data = await resp.json();
        console.log('用户列表返回:', data);
        if (data.code === 0) {
            logoffUsers = data.data || [];
            renderUserList();
        } else {
            showMessage(data.message || '加载用户列表失败', true);
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
        showMessage('加载用户列表失败', true);
    }
}

// 渲染用户列表
function renderUserList() {
    const container = document.getElementById('userList');
    if (!container) return;

    if (!logoffUsers.length) {
        container.innerHTML = '<div class="empty-tip">暂无挂机用户<br>点击 [+] 添加</div>';
        return;
    }

    container.innerHTML = logoffUsers.map(user => {
        const isActive = (currentUser && currentUser.userid == user.userid);
        const userName = user.name || user.nickname || '未知';
        const displayName = userName.length > 12 ? userName.substring(0, 12) + '...' : userName;
        const avatarHtml = (user.face && user.face.startsWith('http')) ?
            `<img src="${user.face}" alt="头像" onerror="this.parentElement.innerHTML='<span>${(userName.charAt(0))}</span>'">` :
            `<span>${userName.charAt(0)}</span>`;

        return `
            <div class="user-item ${isActive ? 'active' : ''}" data-uid="${user.userid}" onclick="window.logoffConfig.selectUserById('${user.userid}')">
                <div class="user-avatar-small">
                    ${avatarHtml}
                </div>
                <div class="user-info-small">
                    <div class="user-name-small">${escapeHtml(displayName)}</div>
                    <div class="user-uid-small">UID: ${user.userid}</div>
                </div>
                <div class="user-actions">
                    <button class="action-icon delete" onclick="event.stopPropagation(); window.logoffConfig.deleteUser('${user.userid}', '${escapeHtml(userName)}')" title="删除">🗑</button>
                </div>
            </div>
        `;
    }).join('');
}

// 删除用户
async function deleteUser(uid, name) {
    if (!confirm(`确定删除用户 "${name}" 的所有配置吗？`)) return;

    try {
        const resp = await fetch(`/logoff_api/users/${uid}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.code === 0) {
            showMessage('删除成功');
            if (currentUser && currentUser.userid == uid) {
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

// 提交修改（是否启动挂机）- 提交 "Y"/"N" 字符串
async function submitUserConfig() {
    if (!currentUser) {
        showMessage('请先选择用户', true);
        return;
    }

    const toggleSwitch = document.getElementById('isOpenToggle');
    const isChecked = toggleSwitch ? toggleSwitch.checked : false;
    // 转换为后端需要的 "Y" 或 "N"
    const isOpenValue = getIsOpenString(isChecked);

    console.log('提交修改 - 用户:', currentUser.userid, 'is_open:', isOpenValue);

    try {
        const resp = await fetch(`/logoff_api/users/${currentUser.userid}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_open: isOpenValue })
        });
        const data = await resp.json();
        console.log('提交修改返回:', data);

        if (data.code === 0) {
            showMessage('保存成功');
            // 更新本地数据的 is_open 值（保持 "Y"/"N" 格式）
            if (currentUser) {
                currentUser.is_open = isOpenValue;
            }
            // 同时更新列表中的用户数据
            const listUser = logoffUsers.find(u => u.userid == currentUser.userid);
            if (listUser) {
                listUser.is_open = isOpenValue;
            }
        } else {
            showMessage(data.message || '保存失败', true);
        }
    } catch (error) {
        console.error('保存失败:', error);
        showMessage('保存失败: ' + error.message, true);
    }
}

// 获取用户的挂机设定列表
async function loadUserLogoffs(uid) {
    try {
        const resp = await fetch(`/logoff_api/users/${uid}/logoffs`);
        const data = await resp.json();
        console.log('挂机设定返回:', data);
        if (data.code === 0) {
            renderLogoffList(data.data || []);
        } else {
            showMessage(data.message, true);
        }
    } catch (error) {
        console.error('加载挂机设定失败:', error);
        showMessage('加载挂机设定失败', true);
    }
}

// 渲染挂机设定列表（添加滑块开关）
function renderLogoffList(logoffs) {
    const container = document.getElementById('logoffList');
    if (!container) return;

    if (!logoffs || logoffs.length === 0) {
        container.innerHTML = '<div class="empty-tip">暂无挂机设定<br>点击 [+] 添加</div>';
        return;
    }

    container.innerHTML = logoffs.map(logoff => {
        const coverHtml = logoff.cover_url ?
            `<img src="${logoff.cover_url}" alt="封面" onerror="this.parentElement.innerHTML='<div class=\'cover-placeholder\'>🎬</div>'">` :
            `<div class="cover-placeholder">🎬</div>`;

        // 获取 is_open 状态（后端返回 "Y" 或 "N"）
        const isOpen = logoff.is_open === "Y" || logoff.is_open === true;

        return `
            <div class="logoff-item" data-logoff-id="${logoff.id}">
                <div class="logoff-cover">
                    ${coverHtml}
                </div>
                <div class="logoff-info">
                    <div class="logoff-owner">${escapeHtml(logoff.owner_name || logoff.title || '未知直播间')}</div>
                    <div class="logoff-time">⏰ ${formatTime(logoff.start_time)} - ${formatTime(logoff.end_time)}</div>
                    <div class="logoff-roomid">房间号: ${logoff.room_id}</div>
                </div>
                <div class="logoff-actions">
                    <label class="logoff-switch">
                        <input type="checkbox" class="logoff-toggle" data-id="${logoff.id}" ${isOpen ? 'checked' : ''}>
                        <span class="logoff-slider"></span>
                    </label>
                    <button class="logoff-edit" data-id="${logoff.id}" title="编辑">✏️</button>
                    <button class="logoff-delete" data-id="${logoff.id}" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join('');

    // 绑定滑块开关事件
    container.querySelectorAll('.logoff-toggle').forEach(toggle => {
        toggle.onchange = async (e) => {
            e.stopPropagation();
            const logoffId = toggle.dataset.id;
            const isChecked = toggle.checked;
            await updateLogoffStatus(logoffId, isChecked);
        };
    });

    // 绑定编辑按钮事件
    container.querySelectorAll('.logoff-edit').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const logoffId = btn.dataset.id;
            const logoff = logoffs.find(l => l.id == logoffId);
            if (logoff) {
                showEditLogoffModal(logoff);
            }
        };
    });

    // 绑定删除按钮事件
    container.querySelectorAll('.logoff-delete').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const logoffId = btn.dataset.id;
            deleteLogoff(logoffId);
        };
    });
}

// 更新挂机设定的开关状态
async function updateLogoffStatus(logoffId, isChecked) {
    const isOpenValue = isChecked ? "Y" : "N";

    console.log('更新开关状态:', { logoffId, isOpen: isOpenValue });

    try {
        const resp = await fetch(`/logoff_api/logoff/${logoffId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_open: isOpenValue })
        });
        const data = await resp.json();
        console.log('更新开关状态返回:', data);

        if (data.code === 0) {
            showMessage(isChecked ? '已开启挂机' : '已关闭挂机');
            // 刷新列表
            if (currentUser) {
                await loadUserLogoffs(currentUser.userid);
            }
        } else {
            showMessage(data.message || '更新失败', true);
            // 恢复开关状态
            const toggle = document.querySelector(`.logoff-toggle[data-id="${logoffId}"]`);
            if (toggle) {
                toggle.checked = !isChecked;
            }
        }
    } catch (error) {
        console.error('更新开关状态失败:', error);
        showMessage('更新失败: ' + error.message, true);
        // 恢复开关状态
        const toggle = document.querySelector(`.logoff-toggle[data-id="${logoffId}"]`);
        if (toggle) {
            toggle.checked = !isChecked;
        }
    }
}

// 显示编辑挂机设定弹窗
async function showEditLogoffModal(logoff) {
    if (!currentUser) {
        showMessage('请先选择用户', true);
        return;
    }

    const rooms = await getRoomList();
    if (rooms.length === 0) {
        showMessage('暂无可用房间，请先在弹幕页面添加房间', true);
        return;
    }

    // 提取时间（去掉秒数，只保留 HH:MM）
    let startTime = logoff.start_time || '';
    let endTime = logoff.end_time || '';
    if (startTime && startTime.length > 5) {
        startTime = startTime.substring(0, 5);
    }
    if (endTime && endTime.length > 5) {
        endTime = endTime.substring(0, 5);
    }

    // 获取 is_open 状态
    const isOpen = logoff.is_open === "Y" || logoff.is_open === true;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-title">✏️ 编辑挂机设定</div>
            <div class="modal-form-group">
                <label class="modal-label">选择房间</label>
                <select class="modal-select" id="roomSelect">
                    <option value="">请选择直播间</option>
                    ${rooms.map(room => `
                        <option value="${room.room_id}" ${room.room_id == logoff.room_id ? 'selected' : ''}>
                            ${escapeHtml(room.owner_name || room.title)}（${room.room_id}）
                        </option>
                    `).join('')}
                </select>
            </div>
            <div class="time-row">
                <div class="modal-form-group">
                    <label class="modal-label">开始时间</label>
                    <input type="time" class="modal-input" id="startTime" value="${startTime}">
                </div>
                <span class="time-separator">—</span>
                <div class="modal-form-group">
                    <label class="modal-label">结束时间</label>
                    <input type="time" class="modal-input" id="endTime" value="${endTime}">
                </div>
            </div>
            <div class="modal-form-group">
                <label class="modal-label" style="display: flex; align-items: center; gap: 12px;">
                    <span>是否启用挂机：</span>
                    <label class="modal-toggle-switch">
                        <input type="checkbox" id="isOpenToggle" ${isOpen ? 'checked' : ''}>
                        <span class="modal-toggle-slider"></span>
                    </label>
                    <span id="isOpenStatus" style="font-size: 12px; color: #aaa;">${isOpen ? '已启用' : '已禁用'}</span>
                </label>
            </div>
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                <button class="modal-btn modal-btn-primary" id="confirmBtn">确认修改</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    // 绑定弹窗内的开关状态显示
    const modalToggle = overlay.querySelector('#isOpenToggle');
    const modalStatus = overlay.querySelector('#isOpenStatus');
    if (modalToggle && modalStatus) {
        modalToggle.onchange = () => {
            modalStatus.textContent = modalToggle.checked ? '已启用' : '已禁用';
        };
    }

    const close = () => overlay.remove();

    const confirmBtn = overlay.querySelector('#confirmBtn');
    if (confirmBtn) {
        confirmBtn.onclick = async () => {
            const roomSelect = overlay.querySelector('#roomSelect');
            const roomId = roomSelect ? roomSelect.value : '';
            let startTimeVal = overlay.querySelector('#startTime') ? overlay.querySelector('#startTime').value : '';
            let endTimeVal = overlay.querySelector('#endTime') ? overlay.querySelector('#endTime').value : '';
            const isOpenChecked = modalToggle ? modalToggle.checked : false;
            const isOpenValue = isOpenChecked ? "Y" : "N";

            if (!roomId) {
                showMessage('请选择房间', true);
                return;
            }
            if (!startTimeVal || !endTimeVal) {
                showMessage('请填写挂机时段', true);
                return;
            }

            // 确保时间格式正确
            if (startTimeVal && startTimeVal.length === 5) {
                startTimeVal = startTimeVal + ':00';
            }
            if (endTimeVal && endTimeVal.length === 5) {
                endTimeVal = endTimeVal + ':00';
            }

            console.log('编辑提交数据:', {
                logoff_id: logoff.id,
                room_id: parseInt(roomId),
                start_time: startTimeVal,
                end_time: endTimeVal,
                is_open: isOpenValue
            });

            try {
                const resp = await fetch(`/logoff_api/logoff/${logoff.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        room_id: parseInt(roomId),
                        start_time: startTimeVal,
                        end_time: endTimeVal,
                        is_open: isOpenValue
                    })
                });
                const data = await resp.json();
                console.log('编辑挂机设定返回:', data);

                if (data.code === 0) {
                    showMessage('修改成功');
                    close();
                    await loadUserLogoffs(currentUser.userid);
                    await loadUserList();
                } else {
                    showMessage(data.message || '修改失败', true);
                }
            } catch (error) {
                console.error('修改失败:', error);
                showMessage('修改失败: ' + error.message, true);
            }
        };
    }

    const cancelBtn = overlay.querySelector('#cancelBtn');
    if (cancelBtn) cancelBtn.onclick = close;

    overlay.onclick = (e) => { if (e.target === overlay) close(); };
}


// 删除挂机设定
async function deleteLogoff(logoffId) {
    if (!confirm('确定删除这个挂机设定吗？')) return;

    try {
        const resp = await fetch(`/logoff_api/logoff/${logoffId}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.code === 0) {
            showMessage('删除成功');
            if (currentUser) {
                await loadUserLogoffs(currentUser.userid);
            }
        } else {
            showMessage(data.message, true);
        }
    } catch (error) {
        showMessage('删除失败: ' + error.message, true);
    }
}

// ========== 二维码登录（新增用户） ==========

// 显示二维码登录弹窗
function showQrcodeModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay qrcode-modal';
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-title">📱 扫码添加用户</div>
            <div class="qrcode-content">
                <img class="qrcode-image" id="qrcodeImg" src="" alt="加载二维码...">
                <div class="qrcode-tip">
                    <span>1. 打开B站App</span><br>
                    <span>2. 点击右上角扫一扫</span><br>
                    <span>3. 扫描二维码确认登录</span>
                </div>
                <div class="qrcode-expired-tip" id="qrcodeTip">正在生成二维码...</div>
                <button class="qrcode-refresh-btn" id="qrcodeRefreshBtn">🔄 刷新二维码</button>
            </div>
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-secondary" id="closeModalBtn">关闭</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    stopPolling();
    loadQrcode();

    const refreshBtn = overlay.querySelector('#qrcodeRefreshBtn');
    if (refreshBtn) {
        refreshBtn.onclick = () => {
            stopPolling();
            loadQrcode();
        };
    }

    const closeBtn = overlay.querySelector('#closeModalBtn');
    if (closeBtn) {
        closeBtn.onclick = () => {
            stopPolling();
            overlay.remove();
        };
    }

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            stopPolling();
            overlay.remove();
        }
    };
}

// 加载二维码
async function loadQrcode() {
    const qrcodeImg = document.getElementById('qrcodeImg');
    const qrcodeTip = document.getElementById('qrcodeTip');

    if (!qrcodeImg) return;

    if (qrcodeTip) {
        qrcodeTip.textContent = '正在生成二维码...';
        qrcodeTip.style.color = '#aaa';
    }

    try {
        const resp = await fetch('/logoff_api/qrcode');
        const data = await resp.json();

        if (data.code === 0 && data.img_url) {
            qrcodeImg.src = data.img_url;
            if (qrcodeTip) {
                qrcodeTip.textContent = '请使用B站App扫码登录';
                qrcodeTip.style.color = '#4CAF50';
            }
            startPolling();
        } else {
            if (qrcodeTip) {
                qrcodeTip.textContent = data.message || '生成二维码失败，请重试';
                qrcodeTip.style.color = '#f44336';
            }
        }
    } catch (error) {
        console.error('加载二维码失败:', error);
        if (qrcodeTip) {
            qrcodeTip.textContent = '加载失败，请点击刷新';
            qrcodeTip.style.color = '#f44336';
        }
    }
}

// 开始轮询扫码状态
function startPolling() {
    if (isPolling) return;
    isPolling = true;

    function poll() {
        fetch('/logoff_api/poll')
            .then(response => response.json())
            .then(data => {
                const qrcodeTip = document.getElementById('qrcodeTip');
                if (!qrcodeTip) {
                    stopPolling();
                    return;
                }

                qrcodeTip.textContent = data.text || '等待扫码...';

                if (data.code === 0) {
                    qrcodeTip.style.color = '#4CAF50';
                    qrcodeTip.textContent = '✅ 登录成功！';
                    showMessage('用户添加成功');
                    stopPolling();
                    const overlay = document.querySelector('.modal-overlay');
                    if (overlay) overlay.remove();
                    loadUserList();
                } else if (data.code === 86038 || data.code === 1102) {
                    qrcodeTip.style.color = '#FF9800';
                    qrcodeTip.textContent = '⚠️ ' + (data.text || '二维码已过期，请刷新');
                    stopPolling();
                    isPolling = false;
                } else {
                    if (isPolling) {
                        pollTimer = setTimeout(poll, 1500);
                    }
                }
            })
            .catch(error => {
                console.error('轮询失败:', error);
                const qrcodeTip = document.getElementById('qrcodeTip');
                if (qrcodeTip) {
                    qrcodeTip.textContent = '轮询失败，请刷新重试';
                }
                stopPolling();
                isPolling = false;
            });
    }

    poll();
}

// 停止轮询
function stopPolling() {
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
    isPolling = false;
}

// ========== 新增挂机设定弹窗 ==========

// 获取房间列表
async function getRoomList() {
    try {
        const resp = await fetch('/api/searchrooms');
        const data = await resp.json();
        console.log('房间列表返回:', data);
        if (data.code === 0 && data.rooms) {
            return data.rooms;
        }
        return [];
    } catch (error) {
        console.error('获取房间列表失败:', error);
        return [];
    }
}

// 显示新增挂机设定弹窗
// 显示新增挂机设定弹窗
async function showAddLogoffModal() {
    if (!currentUser) {
        showMessage('请先选择用户', true);
        return;
    }

    const rooms = await getRoomList();
    if (rooms.length === 0) {
        showMessage('暂无可用房间，请先在弹幕页面添加房间', true);
        return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-title">➕ 新增挂机设定</div>
            <div class="modal-form-group">
                <label class="modal-label">选择房间</label>
                <select class="modal-select" id="roomSelect">
                    <option value="">请选择直播间</option>
                    ${rooms.map(room => `<option value="${room.room_id}">${escapeHtml(room.owner_name || room.title)}（${room.room_id}）</option>`).join('')}
                </select>
            </div>
            <div class="time-row">
                <div class="modal-form-group">
                    <label class="modal-label">开始时间</label>
                    <input type="time" class="modal-input" id="startTime" value="09:00">
                </div>
                <span class="time-separator">—</span>
                <div class="modal-form-group">
                    <label class="modal-label">结束时间</label>
                    <input type="time" class="modal-input" id="endTime" value="18:00">
                </div>
            </div>
            <div class="modal-buttons">
                <button class="modal-btn modal-btn-secondary" id="cancelBtn">取消</button>
                <button class="modal-btn modal-btn-primary" id="confirmBtn">确认添加</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    const close = () => overlay.remove();

    const confirmBtn = overlay.querySelector('#confirmBtn');
    if (confirmBtn) {
        confirmBtn.onclick = async () => {
            const roomSelect = overlay.querySelector('#roomSelect');
            const roomId = roomSelect ? roomSelect.value : '';
            let startTime = overlay.querySelector('#startTime') ? overlay.querySelector('#startTime').value : '';
            let endTime = overlay.querySelector('#endTime') ? overlay.querySelector('#endTime').value : '';

            if (!roomId) {
                showMessage('请选择房间', true);
                return;
            }
            if (!startTime || !endTime) {
                showMessage('请填写挂机时段', true);
                return;
            }

            // 确保时间格式正确，添加秒数（后端可能需要 HH:MM:SS 格式）
            // 如果只有 HH:MM，补充 :00
            if (startTime && startTime.length === 5) {
                startTime = startTime + ':00';
            }
            if (endTime && endTime.length === 5) {
                endTime = endTime + ':00';
            }

            console.log('提交数据:', {
                uid: parseInt(currentUser.userid),
                room_id: parseInt(roomId),
                start_time: startTime,
                end_time: endTime
            });

            try {
                const resp = await fetch('/logoff_api/videos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        uid: parseInt(currentUser.userid),
                        room_id: parseInt(roomId),
                        start_time: startTime,
                        end_time: endTime
                    })
                });
                const data = await resp.json();
                console.log('添加挂机设定返回:', data);

                if (data.code === 0) {
                    showMessage('添加成功');
                    close();
                    await loadUserLogoffs(currentUser.userid);
                    await loadUserList();
                } else {
                    showMessage(data.message || '添加失败', true);
                }
            } catch (error) {
                console.error('添加失败:', error);
                showMessage('添加失败: ' + error.message, true);
            }
        };
    }

    const cancelBtn = overlay.querySelector('#cancelBtn');
    if (cancelBtn) cancelBtn.onclick = close;

    overlay.onclick = (e) => { if (e.target === overlay) close(); };
}

// 开关状态变化时的处理
function onToggleChange() {
    const toggleSwitch = document.getElementById('isOpenToggle');
    const toggleStatus = document.getElementById('toggleStatus');
    if (toggleSwitch && toggleStatus) {
        const isChecked = toggleSwitch.checked;
        toggleStatus.textContent = isChecked ? '是' : '否';
        console.log('开关状态变化:', isChecked ? '开启' : '关闭');
    }
}

// ========== 事件绑定 ==========
function bindEvents() {
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) addUserBtn.onclick = showQrcodeModal;

    const addLogoffBtn = document.getElementById('addLogoffBtn');
    if (addLogoffBtn) addLogoffBtn.onclick = showAddLogoffModal;

    const submitBtn = document.getElementById('submitConfigBtn');
    if (submitBtn) submitBtn.onclick = submitUserConfig;

    const toggleSwitch = document.getElementById('isOpenToggle');
    if (toggleSwitch) {
        toggleSwitch.onchange = onToggleChange;
    }
}

// ========== 初始化 ==========
async function init() {
    console.log('页面初始化开始');
    bindEvents();
    await loadUserList();
    clearRightPanel();
    console.log('页面初始化完成');
}

// 暴露全局方法供 onclick 调用
window.logoffConfig = {
    selectUserById: selectUserById,
    deleteUser: deleteUser,
    deleteLogoff: deleteLogoff,
    showQrcodeModal: showQrcodeModal,
    showAddLogoffModal: showAddLogoffModal,
    selectUser: selectUser
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);