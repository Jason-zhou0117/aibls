const danmuJs = {
        socket: null,
        roomId: null,
        isRunning: false,
        roomTitle: '',
        counts: { gift: 0, danmaku: 0, welcome: 0 },
        collapsedColumns: { gift: false, welcome: false },
        currentPersonality: null,  // 当前性格
        robotEnabled: true,        // 机器人启用状态
        personalities: []         // 性格列表
}

danmuJs.init = function () {

    danmuJs.connect_socket()
    danmuJs.danmuCount = 0;
    danmuJs.currentFilter = 'all';
    danmuJs.messageCounts = {total: 0, danmaku: 0, gift: 0, welcome: 0, guard: 0, super_chat: 0};

    // 新增：初始化机器人
    danmuJs.initRobot();
}

/**链接WebSocket**/
danmuJs.connect_socket = function () {
    if (danmuJs.socket && danmuJs.socket.connected) {
        console.log('已经连接，无需重复连接');
        return;
    }

    danmuJs.socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        timeout: 20000
    });

    // 监听连接事件
    danmuJs.socket.on('connect', function () {
        console.log('Socket.IO连接成功');
    });
    // 监听连接事件
    danmuJs.socket.on('disconnect', function () {
        console.log('Socket.IO连接断开');
    });
    // 重连尝试事件
    danmuJs.socket.on('reconnect_attempt', function (attempt) {
        console.log('重连尝试 #' + attempt);
    });

    // 重连成功事件
    danmuJs.socket.on('reconnect', function () {
        console.log('重连成功');
    });

    // 重连失败事件
    danmuJs.socket.on('reconnect_failed', function () {
        console.log('重连失败');
    });

    // 监听所有事件（调试用）
    danmuJs.socket.onAny((eventName, ...args) => {
        console.log(`事件 ${eventName}:`, args);
    });

    // 欢迎事件
    danmuJs.socket.on('welcome', (data) => danmuJs.addWelcome(data));

    //弹幕
    danmuJs.socket.on('danmaku', (data) => danmuJs.addDanmaku(data));

    // 礼物事件
    danmuJs.socket.on('gift', (data) => danmuJs.addGift(data));

    // 上舰事件
    danmuJs.socket.on('guard', (data) => danmuJs.addGuard(data));

    // 上舰事件
    danmuJs.socket.on('super_chat', (data) => danmuJs.addSuperChat(data));
}

/**添加聊天弹幕**/
danmuJs.addDanmaku = function(data) {
    const container = document.getElementById('danmaku_messages');
    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_username = '<div><span class="message-user">' + danmuJs.escapeHtml(data.sender_name) +':</span></div>';
    const div_msg = '<div class="message-content">' + danmuJs.escapeHtml(data.message)+'</div>';
    const msgDiv = danmuJs.createMessageDiv('danmaku', div_time + div_username + div_msg);
    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.danmaku++;
    document.getElementById('danmaku_count').innerText = danmuJs.counts.danmaku;
    danmuJs.limitMessages(container);
}

/**添加礼物弹幕**/
danmuJs.addGift = function(data) {
    const container = document.getElementById('gift_messages');
    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_username = '<div><span class="message-user">' + danmuJs.escapeHtml(data.sender_name) +':</span></div>';
    const div_msg = '<div class="message-content">送了' + data.gift_num+ '个 <span class="gift-name">' + danmuJs.escapeHtml(data.gift_name)+'</span></div>';
    const msgDiv = danmuJs.createMessageDiv('gift', div_time + div_username + div_msg);
    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.gift++;
    document.getElementById('gift_count').innerText = danmuJs.counts.gift;
    danmuJs.limitMessages(container);
}

/**添加上舰消息**/
danmuJs.addGuard = function(data) {
    const container = document.getElementById('gift_messages');
    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_username = '<div><span class="message-user">' + danmuJs.escapeHtml(data.sender_name) +':</span></div>';
    const div_msg = '<div class="message-content">🏆 购买了 '+ danmuJs.escapeHtml(data.gift_num) + '个月  <span class="gift-name">' + danmuJs.escapeHtml(data.guard_name) + '</span></div>';
    const msgDiv = danmuJs.createMessageDiv('guard', div_time + div_username + div_msg);
    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.gift++;
    document.getElementById('gift_count').innerText = danmuJs.counts.gift;
    danmuJs.limitMessages(container);
}

/**添加醒目消息消息**/
danmuJs.addSuperChat = function(data) {

    const container = document.getElementById('danmaku_messages');

    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_username = '<div><span class="message-user">✨ ' + danmuJs.escapeHtml(data.sender_name) +':</span></div>';
    const div_msg = '<div class="message-content">💰' + danmuJs.escapeHtml(data.message) + '</div>';
    const msgDiv = danmuJs.createMessageDiv('super-chat', div_time + div_username + div_msg);

    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.danmaku++;
    document.getElementById('danmaku_count').innerText = danmuJs.counts.danmaku;
    danmuJs.limitMessages(container);
}

/**添加入场消息**/
danmuJs.addWelcome = function(data) {
    const container = document.getElementById('welcome_messages');

    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_guard = '<div class="message-content">⭐ [' + danmuJs.escapeHtml(data.guard_name) + danmuJs.escapeHtml(data.uname) + '] 进入直播间</div>';
    const div_normal = '<div class="message-content">👋 [' + danmuJs.escapeHtml(data.uname) +'] 进入直播间</div>';

    const msgDiv = danmuJs.createMessageDiv('welcome', div_time + (data.guard_name ? div_guard : div_normal));

    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.welcome++;
    document.getElementById('welcome_count').innerText = danmuJs.counts.welcome;
    danmuJs.limitMessages(container);
}

/**生成消息体**/
danmuJs.createMessageDiv = function(type, innerHtml) {
    const div = document.createElement('div');
    div.className = `message-item ${type}-item`;
    div.innerHTML = innerHtml;
    return div;
}

/**自动滚动到底部**/
danmuJs.scrollToBottom = function(container) {
    setTimeout(() => { container.scrollTop = container.scrollHeight; }, 10);
}

/**消息超限后清除前面的消息**/
danmuJs.limitMessages = function(container, maxCount = 200) {
    while (container.children.length > maxCount) {
        container.removeChild(container.firstChild);
    }
}

/**清除所有的消息**/
danmuJs.clearAllMessages = function() {
    document.getElementById('gift_messages').innerHTML = '';
    document.getElementById('danmaku_messages').innerHTML = '';
    document.getElementById('welcome_messages').innerHTML = '';
    danmuJs.counts = { gift: 0, danmaku: 0, welcome: 0 };
    document.getElementById('gift_count').innerText = '0';
    document.getElementById('danmaku_count').innerText = '0';
    document.getElementById('welcome_count').innerText = '0';
}

/**优化文本**/
danmuJs.escapeHtml = function(text) {
    if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
    return div.innerHTML;
}

/*切换列*/
danmuJs.toggleColumn = function(column) {
    const columnMap = { 'gift': 'column_gift', 'welcome': 'column_welcome' };
    const colElement = document.getElementById(columnMap[column]);
    if (!colElement) return;

    danmuJs.collapsedColumns[column] = !danmuJs.collapsedColumns[column];

    if (danmuJs.collapsedColumns[column]) {
        colElement.classList.add('collapsed');
    } else {
        colElement.classList.remove('collapsed');
    }

//    danmuJs.updateCollapseButtons();
}

/**收起所有的列**/
danmuJs.toggleAllColumns = function() {
    danmuJs.toggleColumn('gift');
    danmuJs.toggleColumn('welcome');
}

/**更新收放按钮的状态**/
danmuJs.updateCollapseButtons=function() {
    const giftCol = document.getElementById('column_gift');
    const welcomeCol = document.getElementById('column_welcome');
    const giftBtn = giftCol?.querySelector('.collapse-btn');
    const welcomeBtn = welcomeCol?.querySelector('.collapse-btn');
    console.log(giftBtn);
    console.log("礼物栏状态" +danmuJs.collapsedColumns.gift)
    if (giftBtn) {
        giftBtn.textContent  = danmuJs.collapsedColumns.gift ? '▶' : '◀';
        // 强制设置样式
        giftBtn.style.color = '#ffffff';
        giftBtn.style.fontSize = '16px';
        giftBtn.style.fontWeight = 'bold';
        giftBtn.style.opacity = '1';
        giftBtn.style.visibility = 'visible';

    };
    if (welcomeBtn) {
        welcomeBtn.innerHTML = (danmuJs.collapsedColumns.welcome ? '◀' : '▶');

    };
}


/*开始监听*/
danmuJs.startStop = function (event) {
    var target = event.target;
    room_id = target.dataset.roomid;
    is_running = target.dataset.running;
    if (room_id) {
        url = '/danmu/start/' + room_id;
        if (is_running == "1") {
            url = '/danmu/stop/' + room_id;
        }
        console.log("启停，url=" + url);
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.code == 0) {
                    //danmuJs.socket.emit('join_room', { room_id: parseInt(room_id) });
                    danmuJs.setRoomStatus(data)
                } else {
                    alert(data.text);
                    console.error('Error:', data.text);
                }
            })
            .catch(error => console.error('Error:', error))
            .finally(() => {
            });
    }
}

//更新房间链接状态
danmuJs.setRoomStatus = function (data) {
    const roomId = document.getElementById('room_id_display');
    const roomTitle = document.getElementById('room_title_display');
    const span_status = document.getElementById('status_text_display');
    const status_dot = document.getElementById('status_dot');
    if (data.type == '1'){
        status_dot.classList.add("connected");
        span_status.innerText="正在监听";
    }
    else{
        status_dot.classList.remove("connected");
        span_status.innerText="未监听";
    }
    span_status.setAttribute("data-running", data.type);
}

//筛选消息
danmuJs.filterMessages = function (type) {
    danmuJs.currentFilter = type;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    danmuJs.applyFilter();
}

// 应用筛选和搜索
danmuJs.applyFilter = function () {
    const allItems = document.querySelectorAll('.message');

    allItems.forEach(item => {
        const itemType = item.getAttribute('data-type');

        // 类型筛选
        let typeMatch = (danmuJs.currentFilter === 'all' || itemType === danmuJs.currentFilter);

        // 通过添加/移除hidden类来控制显示
        if (typeMatch) {
            item.classList.remove('hidden'); // 显示
        } else {
            item.classList.add('hidden'); // 隐藏
        }
    });
}

// danmu.js - 添加弹框相关方法和重写 changeRoom

// 在 danmuJs 对象中添加以下属性和方法

danmuJs.modalOverlay = null;  // 弹框遮罩层引用

/**
 * 创建弹框的 HTML 结构（动态生成）
 */
danmuJs.createModalHTML = function() {
    // 检查是否已存在弹框
    if (document.getElementById('roomModal')) {
        danmuJs.modalOverlay = document.getElementById('roomModal');
        return;
    }

    const modalHTML = `
        <div class="modal-overlay" id="roomModal">
            <div class="modal-container">
                <div class="modal-header">
                    <h3>切换直播间</h3>
                    <button class="modal-close" id="modalCloseBtn">✕</button>
                </div>
                <div class="modal-body">
                    <div class="modal-search">
                        <input type="text" id="roomSearchInput" placeholder="🔍 搜索房间号或主播名..." autocomplete="off">
                    </div>

                    <div class="modal-section">
                        <div class="modal-section-title">已保存的房间</div>
                        <div class="room-list-container" id="roomListContainer">
                            <div class="room-list-empty">加载中...</div>
                        </div>
                    </div>

                    <div class="modal-divider">
                        <span>或</span>
                    </div>

                    <div class="modal-new-room">
                        <input type="text" id="newRoomIdInput" placeholder="输入新房间号" autocomplete="off">
                        <div class="modal-hint">例如：123456</div>
                    </div>

                    <div class="modal-error" id="modalErrorMsg"></div>

                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-cancel" id="modalCancelBtn">取消</button>
                        <button class="modal-btn modal-btn-confirm" id="modalConfirmBtn">确认</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    danmuJs.modalOverlay = document.getElementById('roomModal');
};

/**
 * 显示弹框
 */
danmuJs.showModal = async function() {
    // 创建弹框（如果不存在）
    danmuJs.createModalHTML();

    // 确保 modalOverlay 存在
    if (!danmuJs.modalOverlay) {
        console.error('弹框创建失败');
        return;
    }

    // 加载房间列表
    await danmuJs.loadRoomList();

    // 显示弹框
    danmuJs.modalOverlay.classList.add('active');

    // 绑定事件
    danmuJs.bindModalEvents();
};

/**
 * 隐藏弹框
 */
danmuJs.hideModal = function() {
    if (danmuJs.modalOverlay) {
        danmuJs.modalOverlay.classList.remove('active');
        // 清空输入框和错误提示
        const newRoomInput = document.getElementById('newRoomIdInput');
        const searchInput = document.getElementById('roomSearchInput');
        const errorMsg = document.getElementById('modalErrorMsg');
        if (newRoomInput) newRoomInput.value = '';
        if (searchInput) searchInput.value = '';
        if (errorMsg) errorMsg.classList.remove('show');
        // 清空选中状态
        danmuJs.selectedRoomId = null;
    }
};

/**
 * 加载房间列表
 */
danmuJs.loadRoomList = async function() {
    const container = document.getElementById('roomListContainer');
    if (!container) return;

    container.innerHTML = '<div class="room-list-empty">加载中...</div>';

    try {
        const response = await fetch('/api/searchrooms');
        const data = await response.json();

        if (data.code === 0 && data.rooms && data.rooms.length > 0) {
            // 保存房间列表到全局
            danmuJs.roomList = data.rooms;
            // 获取当前房间号
            danmuJs.currentRoomId = danmuJs.getCurrentRoomIdFromPage();
            // 渲染列表
            danmuJs.renderRoomList(danmuJs.roomList);
        } else {
            container.innerHTML = '<div class="room-list-empty">暂无已保存的房间</div>';
        }
    } catch (error) {
        console.error('加载房间列表失败:', error);
        container.innerHTML = '<div class="room-list-empty">加载失败，请重试</div>';
    }
};

/**
 * 从页面获取当前房间号
 */
danmuJs.getCurrentRoomIdFromPage = function() {
    const roomIdSpan = document.getElementById('room_id_display');
    if (roomIdSpan) {
        const text = roomIdSpan.innerText;
        const match = text.match(/\[(\d+)\]/);
        return match ? parseInt(match[1]) : null;
    }
    return null;
};

/**
 * 渲染房间列表（带删除按钮）
 */
danmuJs.renderRoomList = function(rooms) {
    const container = document.getElementById('roomListContainer');
    if (!container) return;

    if (!rooms || rooms.length === 0) {
        container.innerHTML = '<div class="room-list-empty">暂无已保存的房间</div>';
        return;
    }

    let html = '';
    rooms.forEach(room => {
        const roomId = room.room_id || room.id;
        const ownerName = room.owner_name || room.title || '未知主播';
        const isDefault = room.is_default === '1' || roomId === danmuJs.currentRoomId;
        const selectedClass = (danmuJs.selectedRoomId === roomId) ? 'selected' : '';

        // 当前房间不显示删除按钮，或者显示禁用状态的删除按钮
        const deleteBtnHtml = isDefault
            ? '<button class="room-delete-btn disabled" disabled title="不能删除当前房间">🚫</button>'
            : '<button class="room-delete-btn" data-room-id="' + roomId + '" title="删除房间">🗑️</button>';

        html += `
            <div class="room-option ${selectedClass}" data-room-id="${roomId}" data-room-name="${ownerName}">
                <div class="room-option-radio"></div>
                <div class="room-option-info">
                    <div class="room-option-id">房间 ${roomId}</div>
                    <div class="room-option-name">${danmuJs.escapeHtml(ownerName)}</div>
                </div>
                ${isDefault ? '<span class="room-option-current">当前</span>' : ''}
                ${deleteBtnHtml}
            </div>
        `;
    });

    container.innerHTML = html;

    // 绑定点击选择事件
    container.querySelectorAll('.room-option').forEach(option => {
        option.addEventListener('click', (e) => {
            // 防止点击删除按钮时触发选中
            if (e.target.classList.contains('room-delete-btn')) {
                return;
            }
            const roomId = parseInt(option.dataset.roomId);
            danmuJs.selectRoom(roomId);
        });
    });

    // 绑定删除按钮事件（仅对非禁用按钮）
    container.querySelectorAll('.room-delete-btn:not(.disabled)').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const roomId = btn.dataset.roomId;
            await danmuJs.deleteRoom(roomId);
        });
    });
};

/**
 * 删除房间
 */
danmuJs.deleteRoom = async function(roomId) {
    // 检查是否为当前房间
    if (roomId == danmuJs.currentRoomId) {
        danmuJs.showModalError('不能删除当前正在使用的房间，请先切换到其他房间');
        return;
    }

    // 确认删除
    if (!confirm(`确定要删除房间 ${roomId} 吗？\n删除后该房间将从列表中移除。`)) {
        return;
    }

    // 显示删除中状态
    const btn = document.querySelector(`.room-delete-btn[data-room-id="${roomId}"]`);
    const originalText = btn ? btn.innerHTML : '🗑️';
    if (btn) {
        btn.innerHTML = '⏳';
        btn.disabled = true;
    }

    try {
        const response = await fetch(`/api/room/${roomId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();

        if (data.code === 0) {
            // 删除成功，刷新房间列表
            await danmuJs.loadRoomList();
            // 清空选中状态
            danmuJs.selectedRoomId = null;
            // 清空错误提示
            const errorMsg = document.getElementById('modalErrorMsg');
            if (errorMsg) errorMsg.classList.remove('show');
        } else {
            danmuJs.showModalError(data.message || '删除失败，请重试');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    } catch (error) {
        console.error('删除房间失败:', error);
        danmuJs.showModalError('网络错误，请稍后重试');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
};

/**
 * 选中房间
 */
danmuJs.selectRoom = function(roomId) {
    danmuJs.selectedRoomId = roomId;

    // 更新样式
    document.querySelectorAll('.room-option').forEach(option => {
        const optRoomId = parseInt(option.dataset.roomId);
        if (optRoomId === roomId) {
            option.classList.add('selected');
        } else {
            option.classList.remove('selected');
        }
    });

    // 清空新房间号输入框
    const newRoomInput = document.getElementById('newRoomIdInput');
    if (newRoomInput) newRoomInput.value = '';

    // 清空错误提示
    const errorMsg = document.getElementById('modalErrorMsg');
    if (errorMsg) errorMsg.classList.remove('show');
};

/**
 * 搜索过滤房间列表
 */
danmuJs.filterRoomList = function(keyword) {
    if (!danmuJs.roomList) return;

    if (!keyword.trim()) {
        danmuJs.renderRoomList(danmuJs.roomList);
        return;
    }

    const filtered = danmuJs.roomList.filter(room => {
        const roomId = String(room.room_id || room.id);
        const ownerName = (room.owner_name || room.title || '').toLowerCase();
        const kw = keyword.toLowerCase();
        return roomId.includes(kw) || ownerName.includes(kw);
    });

    danmuJs.renderRoomList(filtered);
};

/**
 * 提交房间切换
 */
danmuJs.submitRoomChange = async function() {
    let roomId = null;

    // 1. 获取选中的房间或输入的新房间号
    if (danmuJs.selectedRoomId) {
        roomId = danmuJs.selectedRoomId;
    } else {
        const newRoomInput = document.getElementById('newRoomIdInput');
        const newRoomId = newRoomInput ? newRoomInput.value.trim() : '';
        if (newRoomId) {
            roomId = parseInt(newRoomId);
            if (isNaN(roomId)) {
                danmuJs.showModalError('请输入数字房间号');
                return;
            }
        }
    }

    if (!roomId) {
        danmuJs.showModalError('请选择或输入房间号');
        return;
    }

    // 2. 如果选择的房间就是当前房间，直接关闭
    if (roomId === danmuJs.currentRoomId) {
        danmuJs.hideModal();
        return;
    }

    // 3. 显示加载状态
    const confirmBtn = document.getElementById('modalConfirmBtn');
    const originalText = confirmBtn ? confirmBtn.innerText : '确认';
    if (confirmBtn) {
        confirmBtn.innerText = '提交中...';
        confirmBtn.disabled = true;
    }

    try {
        const formData = new FormData();
        formData.append('room_id', roomId);

        const response = await fetch('/api/update_room', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.code === 0) {
            // 刷新页面
            location.reload();
        } else {
            danmuJs.showModalError(data.message || '切换失败，请重试');
            if (confirmBtn) {
                confirmBtn.innerText = originalText;
                confirmBtn.disabled = false;
            }
        }
    } catch (error) {
        console.error('切换房间失败:', error);
        danmuJs.showModalError('网络错误，请稍后重试');
        if (confirmBtn) {
            confirmBtn.innerText = originalText;
            confirmBtn.disabled = false;
        }
    }
};

/**
 * 显示弹框错误提示
 */
danmuJs.showModalError = function(message) {
    const errorMsg = document.getElementById('modalErrorMsg');
    if (errorMsg) {
        errorMsg.innerText = message;
        errorMsg.classList.add('show');
    }
};

/**
 * 绑定弹框事件
 */
danmuJs.bindModalEvents = function() {
    // 关闭按钮
    const closeBtn = document.getElementById('modalCloseBtn');
    if (closeBtn) {
        closeBtn.onclick = () => danmuJs.hideModal();
    }

    // 取消按钮
    const cancelBtn = document.getElementById('modalCancelBtn');
    if (cancelBtn) {
        cancelBtn.onclick = () => danmuJs.hideModal();
    }

    // 确认按钮
    const confirmBtn = document.getElementById('modalConfirmBtn');
    if (confirmBtn) {
        confirmBtn.onclick = () => danmuJs.submitRoomChange();
    }

    // 搜索输入
    const searchInput = document.getElementById('roomSearchInput');
    if (searchInput) {
        searchInput.oninput = (e) => danmuJs.filterRoomList(e.target.value);
    }

    // 新房间号输入
    const newRoomInput = document.getElementById('newRoomIdInput');
    if (newRoomInput) {
        newRoomInput.onfocus = () => {
            // 清空选中状态
            danmuJs.selectedRoomId = null;
            document.querySelectorAll('.room-option').forEach(opt => {
                opt.classList.remove('selected');
            });
        };
        newRoomInput.onkeypress = (e) => {
            if (e.key === 'Enter') {
                danmuJs.submitRoomChange();
            }
        };
    }

    // 点击遮罩层关闭
    if (danmuJs.modalOverlay) {
        danmuJs.modalOverlay.onclick = (e) => {
            if (e.target === danmuJs.modalOverlay) {
                danmuJs.hideModal();
            }
        };
    }
};

/**
 * 获取当前性格（从 Session 或默认）
 */
danmuJs.getCurrentPersonality = async function() {
    try {
        const response = await fetch('/robot/status');
        const data = await response.json();
        if (data.code !== -1) {
            danmuJs.currentPersonality = data.personality_id;
            danmuJs.robotEnabled = data.enabled;
        } else {
            // 如果机器人未初始化，使用默认
            danmuJs.currentPersonality = 'sycophant';
        }
    } catch (error) {
        console.error('获取机器人状态失败:', error);
        danmuJs.currentPersonality = 'sycophant';
    }
    return danmuJs.currentPersonality;
};

/**
 * 获取性格列表
 */
danmuJs.getPersonalities = async function() {
    try {
        const response = await fetch('/robot/get_personalities');
        const data = await response.json();
        if (data.code === 0) {
            danmuJs.personalities = data.personalities;
            return danmuJs.personalities;
        }
    } catch (error) {
        console.error('获取性格列表失败:', error);
    }
    return [];
};

/**
 * 打开机器人配置弹框
 */
danmuJs.openRobotConfig = async function() {
    // 获取当前状态和性格列表
    await danmuJs.getCurrentPersonality();
    await danmuJs.getPersonalities();

    // 创建弹框（如果不存在）
    danmuJs.createRobotModalHTML();

    // 渲染性格列表
    danmuJs.renderPersonalityList();

    // 渲染状态信息
    danmuJs.renderRobotStatus();

    // 显示弹框
    const modal = document.getElementById('robotModal');
    if (modal) {
        modal.classList.add('active');
    }

    // 绑定事件
    danmuJs.bindRobotModalEvents();
};

/**
 * 创建机器人配置弹框 HTML
 */
danmuJs.createRobotModalHTML = function() {
    if (document.getElementById('robotModal')) {
        return;
    }

    const modalHTML = `
        <div class="modal-overlay" id="robotModal">
            <div class="modal-container modal-sm">
                <div class="modal-header">
                    <h3>🤖 机器人设置</h3>
                    <button class="modal-close" id="robotModalCloseBtn">✕</button>
                </div>
                <div class="modal-body">
                    <div class="robot-personality-list" id="robotPersonalityList">
                        <div class="room-list-empty">加载中...</div>
                    </div>
                    <div class="robot-status-info" id="robotStatusInfo">
                        <!-- 状态信息 -->
                    </div>
                    <div class="modal-error" id="robotModalErrorMsg"></div>
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-cancel" id="robotModalCancelBtn">取消</button>
                        <button class="modal-btn modal-btn-confirm" id="robotModalConfirmBtn">确认</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
};

/**
 * 渲染性格列表
 */
danmuJs.renderPersonalityList = function() {
    const container = document.getElementById('robotPersonalityList');
    if (!container) return;

    if (!danmuJs.personalities || danmuJs.personalities.length === 0) {
        container.innerHTML = '<div class="room-list-empty">暂无可用性格</div>';
        return;
    }

    // 性格描述映射
    const descMap = {
        'tsundere': '傲娇大小姐，毒舌但善良，喜欢用"哼"、"才不是"',
        'flattering': '温柔小可爱，说话甜甜的，喜欢夸赞观众',
        'sycophant': '主播头号场控，无脑吹捧，热情带节奏'
    };

    let html = '';
    danmuJs.personalities.forEach(personality => {
        const selectedClass = (danmuJs.currentPersonality === personality.id) ? 'selected' : '';
        const desc = descMap[personality.id] || '有趣的机器人性格';

        html += `
            <div class="robot-personality-option ${selectedClass}" data-personality-id="${personality.id}">
                <div class="robot-personality-radio"></div>
                <div class="robot-personality-info">
                    <div class="robot-personality-name">${danmuJs.escapeHtml(personality.name)}</div>
                    <div class="robot-personality-desc">${desc}</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    // 绑定点击选择事件
    container.querySelectorAll('.robot-personality-option').forEach(option => {
        option.addEventListener('click', () => {
            const personalityId = option.dataset.personalityId;
            danmuJs.selectPersonality(personalityId);
        });
    });
};

/**
 * 选中性格
 */
danmuJs.selectPersonality = function(personalityId) {
    danmuJs.selectedPersonality = personalityId;

    // 更新样式
    document.querySelectorAll('.robot-personality-option').forEach(option => {
        const optId = option.dataset.personalityId;
        if (optId === personalityId) {
            option.classList.add('selected');
        } else {
            option.classList.remove('selected');
        }
    });

    // 清空错误提示
    const errorMsg = document.getElementById('robotModalErrorMsg');
    if (errorMsg) errorMsg.classList.remove('show');
};

/**
 * 渲染机器人状态信息
 */
danmuJs.renderRobotStatus = function() {
    const container = document.getElementById('robotStatusInfo');
    if (!container) return;

    const statusText = danmuJs.robotEnabled ? '✅ 已启用' : '⛔ 已禁用';
    const currentName = danmuJs.getPersonalityName(danmuJs.currentPersonality);

    container.innerHTML = `
        <div>🤖 机器人状态: ${statusText}</div>
        <div>🎭 当前性格: <span>${currentName}</span></div>
        <div style="font-size: 11px; margin-top: 5px;">💡 提示：机器人会自动回复弹幕、感谢礼物、欢迎入场</div>
    `;
};

/**
 * 获取性格名称
 */
danmuJs.getPersonalityName = function(personalityId) {
    const personality = danmuJs.personalities.find(p => p.id === personalityId);
    return personality ? personality.name : '无下限马屁精';
};

/**
 * 提交机器人配置
 */
danmuJs.submitRobotConfig = async function() {
    let personalityId = danmuJs.selectedPersonality;

    if (!personalityId) {
        personalityId = danmuJs.currentPersonality;
    }

    if (!personalityId) {
        danmuJs.showRobotModalError('请选择一种性格');
        return;
    }

    // 如果性格没变，直接关闭
    if (personalityId === danmuJs.currentPersonality) {
        danmuJs.hideRobotModal();
        return;
    }

    // 显示加载状态
    const confirmBtn = document.getElementById('robotModalConfirmBtn');
    const originalText = confirmBtn ? confirmBtn.innerText : '确认';
    if (confirmBtn) {
        confirmBtn.innerText = '切换中...';
        confirmBtn.disabled = true;
    }

    try {
        const response = await fetch(`/robot/set_personality/${personalityId}`);
        const data = await response.json();

        if (data.code === 0) {
            danmuJs.currentPersonality = personalityId;
            danmuJs.showRobotModalError(data.message || '切换成功', 'success');

            // 延迟关闭弹框
            setTimeout(() => {
                danmuJs.hideRobotModal();
            }, 1000);
        } else {
            danmuJs.showRobotModalError(data.message || '切换失败，请重试');
        }
    } catch (error) {
        console.error('切换性格失败:', error);
        danmuJs.showRobotModalError('网络错误，请稍后重试');
    } finally {
        if (confirmBtn) {
            confirmBtn.innerText = originalText;
            confirmBtn.disabled = false;
        }
    }
};

/**
 * 显示机器人弹框错误提示
 */
danmuJs.showRobotModalError = function(message, type = 'error') {
    const errorMsg = document.getElementById('robotModalErrorMsg');
    if (errorMsg) {
        errorMsg.innerText = message;
        errorMsg.classList.add('show');
        if (type === 'success') {
            errorMsg.style.backgroundColor = 'rgba(76, 175, 80, 0.2)';
            errorMsg.style.color = '#4CAF50';
        } else {
            errorMsg.style.backgroundColor = 'rgba(244, 67, 54, 0.2)';
            errorMsg.style.color = '#f44336';
        }
        setTimeout(() => {
            errorMsg.classList.remove('show');
            errorMsg.style.backgroundColor = '';
            errorMsg.style.color = '';
        }, 2000);
    }
};

/**
 * 隐藏机器人弹框
 */
danmuJs.hideRobotModal = function() {
    const modal = document.getElementById('robotModal');
    if (modal) {
        modal.classList.remove('active');
    }
    danmuJs.selectedPersonality = null;
};

/**
 * 绑定机器人弹框事件
 */
danmuJs.bindRobotModalEvents = function() {
    const closeBtn = document.getElementById('robotModalCloseBtn');
    const cancelBtn = document.getElementById('robotModalCancelBtn');
    const confirmBtn = document.getElementById('robotModalConfirmBtn');
    const modal = document.getElementById('robotModal');

    if (closeBtn) {
        closeBtn.onclick = () => danmuJs.hideRobotModal();
    }

    if (cancelBtn) {
        cancelBtn.onclick = () => danmuJs.hideRobotModal();
    }

    if (confirmBtn) {
        confirmBtn.onclick = () => danmuJs.submitRobotConfig();
    }

    if (modal) {
        modal.onclick = (e) => {
            if (e.target === modal) {
                danmuJs.hideRobotModal();
            }
        };
    }
};

/**
 * 页面加载时获取并保存机器人状态到 Session
 */
danmuJs.initRobot = async function() {
    try {
        // 获取机器人状态
        const response = await fetch('/robot/status');
        const data = await response.json();

        if (data.code !== -1) {
            danmuJs.currentPersonality = data.personality_id;
            danmuJs.robotEnabled = data.enabled;

            // 如果当前性格不是默认的，但 Session 中没有，可以在这里处理
            // 后端已经在 set_personality 时保存到 session 了
        } else {
            // 机器人未初始化，设置默认性格
            danmuJs.currentPersonality = 'sycophant';
            // 调用后端设置默认性格
            await fetch('/robot/set_personality/sycophant');
        }
    } catch (error) {
        console.error('初始化机器人状态失败:', error);
        danmuJs.currentPersonality = 'sycophant';
    }
};
/**
 * 重写 changeRoom 方法 - 使用自定义弹框
 */
danmuJs.changeRoom = function() {
    danmuJs.showModal();
};




// 清空消息
danmuJs.clearMessages = function () {
    document.getElementById('messages').innerHTML = '';
    danmuJs.messageCounts = {total: 0, danmaku: 0, gift: 0, welcome: 0, guard: 0};
    console.log('消息已清空');
}

// 添加消息
danmuJs.addMessage = function (type, data) {


    danmuJs.messageCounts.total++;
    danmuJs.messageCounts[type] = (danmuJs.messageCounts[type] || 0) + 1;

    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.setAttribute("data-type",type);

    let contentHtml = '';
    let typeText = '';

    switch (type) {
        case 'danmaku':
            typeText = '💬 弹幕';
            contentHtml = `<span class="message-user">${data.uname}:</span> ${data.msg}`;
            break;
        case 'gift':
            typeText = '🎁 礼物';
            contentHtml = `<span class="message-user">${data.uname}</span> ${data.action}了 ${data.gift_num} 个 ${data.gift_name}`;
            break;
        case 'welcome':
            typeText = '👋 欢迎';
            contentHtml = `<span class="message-user">${data.guard_name}${data.uname}</span> 进入直播间`;
            break;
        case 'guard':
            typeText = '⚓ 大航海';
            contentHtml = `<span class="message-user">${data.uname}</span> 购买了 ${data.guard_level} 级舰长`;
            break;
        case 'view':
            typeText = '👥 人气';
            contentHtml = `当前人气值: ${data.view_count}`;
            break;
        default:
            typeText = '📢 系统';
            contentHtml = JSON.stringify(data);
    }

    msgDiv.innerHTML = `
                <div class="message-header">
                    <span>${typeText}</span>
                    <span>${data.time || new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-content">${contentHtml}</div>
            `;

    messagesDiv.appendChild(msgDiv);
    if (danmuJs.currentFilter !== 'all' && type !== danmuJs.currentFilter) {
         msgDiv.classList.add('hidden'); // 隐藏;
    }

    document.scrollTop = document.scrollHeight;

    // 限制消息数量
    while (messagesDiv.children.length > 500) {
        messagesDiv.removeChild(messagesDiv.firstChild);
    }
}