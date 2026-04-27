//定义封装的页头公共JS对象
var headJs = {};

/*
返回到首页
*/
headJs.goHome = function(){
    window.location.href='/';
}

/*
去扫码登录监察账号
*/
headJs.openLogin = function(){
    window.location.href='/login/page';
}

/*
去配置
*/
headJs.openConfig = function(){
    window.location.href='/login.html';
}
