//定义封装的页头公共JS对象
var headJs = {};

/*
返回到首页
*/
headJs.goHome = function(){
    window.location.href='/';
}


/*
去配置
*/
headJs.openConfig = function(){
    window.open('/vip_config');
}
/*
打开视频侧视页面
*/
headJs.openPlayer = function(){
    window.open('/static/video_player.html');
}
/*
去配置
*/
headJs.openGiftConfig = function(){
    window.open('/gift_config');
}

/*
去配置
*/
headJs.openGiftStat= function(){
    window.open('/gift_stat');
}

/*
去配置
*/
headJs.openLogOff= function(){
    window.open('/logoff_api/page');
}

/*
去扫码登录监察账号（先退出当前登录，再跳转到登录页）
*/
headJs.openLogin = function(){
    // 调用退出登录接口
    fetch('/logout', {
        method: 'POST',
        credentials: 'same-origin'  // 携带 cookie/session
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        // 无论退出是否成功，都跳转到登录页
        window.location.href = '/login/page';
    })
    .catch(function(error) {
        console.error('Logout error:', error);
        // 出错也仍然跳转到登录页
        window.location.href = '/login/page';
    });
}