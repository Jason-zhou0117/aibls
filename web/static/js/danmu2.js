var danmuJs = {}

danmuJs.socket = null;

danmuJs.init = function () {
    danmuJs.connect_socket()
    danmuJs.danmuCount = 0;
    danmuJs.currentFilter = 'all';
    danmuJs.messageCounts = {total: 0, danmaku: 0, gift: 0, welcome: 0, guard: 0, super_chat: 0};

}

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
    danmuJs.socket.on('welcome', (data) => {
        console.log('收到欢迎:', data);
        danmuJs.addMessage('welcome', data);
    });

    //弹幕
    danmuJs.socket.on('danmaku', function (data) {
        console.log('收到新弹幕:', data.msg);
        //++danmuJs.danmuCount;
        //处理页面效果
        danmuJs.addMessage('danmaku', data);
    });

    // 礼物事件
    danmuJs.socket.on('gift', (data) => {
        console.log('收到礼物:', data);
        danmuJs.addMessage('gift', data);
    });

    // 上舰事件
    danmuJs.socket.on('guard', (data) => {
        console.log('收到礼物:', data);
        danmuJs.addMessage('guard', data);
    });

    // 上舰事件
    danmuJs.socket.on('super_chat', (data) => {
        console.log('收到醒目留言:', data);
        danmuJs.addMessage('super_chat', data);
    });
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
    span_status = document.getElementById('txt_status');
    span_status.innerText = data.message;
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