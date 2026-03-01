var danmuJs = {}

danmuJs.init = function(){
    danmuJs.socket = io.connect('http://' + document.domain + ':' + location.port);
    danmuJs.danmuCount = 0;
    // 监听连接事件
    danmuJs.socket.on('connect', function() {
        console.log('Socket.IO连接成功');
    });
    // 监听连接事件
    danmuJs.socket.on('disconnect', function() {
        console.log('Socket.IO连接断开');
    });
    danmuJs.socket.on('new_danmu', function(data) {
        console.log('收到新弹幕:', data);
        ++danmuJs.danmuCount;
        //处理页面效果
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
        fetch(url)
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                danmuJs.setStatus(data.message)
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

danmuJs.setStatus = function(msg){
    span_status = document.getElementById('txt_status');
    span_status.innerText = msg
}