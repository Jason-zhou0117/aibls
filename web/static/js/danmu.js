var danmuJs = {}

danmuJs.socket=null;

danmuJs.init = function(){
    danmuJs.connect_socket()
    danmuJs.danmuCount = 0;

}

danmuJs.connect_socket = function (){


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
    danmuJs.socket.on('connect', function() {
        console.log('Socket.IO连接成功');
    });
    // 监听连接事件
    danmuJs.socket.on('disconnect', function() {
        console.log('Socket.IO连接断开');
    });
    // 重连尝试事件
    danmuJs.socket.on('reconnect_attempt', function(attempt) {
        console.log('重连尝试 #' + attempt);
    });

    // 重连成功事件
    danmuJs.socket.on('reconnect', function() {
        console.log('重连成功');
    });

    // 重连失败事件
    danmuJs.socket.on('reconnect_failed', function() {
        console.log('重连失败');
    });

    // 欢迎消息
    danmuJs.socket.on('welcome', function(data) {
        console.log('收到欢迎信息弹幕:', data);
        danmuJs.setStatus(data.msg);
    });

    danmuJs.socket.on('danmaku', function(data) {
        console.log('收到新弹幕:', data.msg);
        //++danmuJs.danmuCount;
        //处理页面效果
    });

    // 监听所有事件（调试用）
    danmuJs.socket.onAny((eventName, ...args) => {
            console.log(`事件 ${eventName}:`, args);
        });

    // 礼物事件
    danmuJs.socket.on('gift', (data) => {
            console.log('收到礼物:', data);
        });

    // 欢迎事件
    danmuJs.socket.on('welcome', (data) => {
            console.log('收到欢迎:', data);
        });
    // 房间加入确认
    danmuJs.socket.on('room_joined', (data) => {
            console.log('房间加入确认:', data);
        });
}


/*开始监听*/
danmuJs.startStop = function (event){
    var target = event.target;
    room_id = target.dataset.roomid;
    is_running = target.dataset.running;
    if (room_id){
        url = '/danmu/start/'+room_id;
        if (is_running == "1"){
            url = '/danmu/stop/'+room_id;
        }
        console.log("启停，url=" + url);
        fetch(url)
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                 //danmuJs.socket.emit('join_room', { room_id: parseInt(room_id) });
                 danmuJs.setRoomStatus(data)
             }
             else{
                alert(data.text);
                console.error('Error:', data.text) ;
             }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
    }
}

danmuJs.setRoomStatus = function(data) {
    span_status = document.getElementById('txt_status');
    span_status.innerText = data.message;
    span_status.setAttribute("data-running", data.type);
}