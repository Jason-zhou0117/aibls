const danmuJs = {
        socket: null,
        roomId: null,
        isRunning: false,
        roomTitle: '',
        counts: { gift: 0, danmaku: 0, welcome: 0 },
        collapsedColumns: { gift: false, welcome: false }
}

danmuJs.init = function () {

    danmuJs.connect_socket()
    danmuJs.danmuCount = 0;
    danmuJs.currentFilter = 'all';
    danmuJs.messageCounts = {total: 0, danmaku: 0, gift: 0, welcome: 0, guard: 0, super_chat: 0};

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
    const div_username = '<div><span class="message-user">' + danmuJs.escapeHtml(data.uname) +':</span></div>';
    const div_msg = '<div class="message-content">' + danmuJs.escapeHtml(data.msg)+'</div>';
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
    const div_username = '<div><span class="message-user">' + danmuJs.escapeHtml(data.uname) +':</span></div>';
    const div_msg = '<div class="message-content">🏆 购买了 ' + danmuJs.escapeHtml(data.guard_level) + '舰长</div>';
    const msgDiv = danmuJs.createMessageDiv('guard', div_time + div_username + div_msg);
    container.appendChild(msgDiv);
    danmuJs.scrollToBottom(container);
    danmuJs.counts.gift++;
    document.getElementById('gift_count').innerText = danmuJs.counts.gift;
    danmuJs.limitMessages(container);
}

/**添加醒目消息消息**/
danmuJs.addSuperChat = function(data) {

    const container = document.getElementById('gift_messages');

    const div_time = '<div class="message-time">' + (data.time || new Date().toLocaleTimeString()) + '</div>';
    const div_username = '<div><span class="message-user">✨ ' + danmuJs.escapeHtml(data.uname) +':</span></div>';
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


danmuJs.changeRoom = function (){
    let room_id = prompt('请输入房间号：');
    // 取消处理
    if (room_id === null) {
//        showMessage('已取消输入', false);
        return;
    }
    if (room_id == ""){
        alert("请输入房间号");
        return
    }
    formData = new FormData();
    formData.append('room_id', room_id);
    fetch('/api/updateroom',{
        method:"post",
        body:formData,
        headers:{}
    })
    .then(response => response.json())
    .then(data => {
        if (data.code == 0){
           location.reload();
        }
        else{
            alert(data.message);
        }
    })
    .catch(error => console.error('Error:', error))
    .finally(() => {
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