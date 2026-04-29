//定义扫码登录相关的Js
var loginJs = {};

//定义轮询的序号
loginJs.timeout_id = "";
//停止扫码
loginJs.stop_flag = false;

/*
刷新二维码，点击页面上刷新按钮时方法
*/
loginJs.refreshQrcode = function(){
    //获取二维码的DIV元素
//    var divimg = document.getElementById("divqrcode");
//    //清除DIV内的元素
//    divimg.innerHTML = "";
    //异步调用后台刷新二维码的API接口
    fetch('/login/qrcode')
        .then(response => response.json())
        .then(data => {
            //如果成功获取二维码，展示二维码
            if (data.code == 0){
                //创建二维码的图像控件
                var imgqr = document.getElementById("qrcodeImage");

                imgqr.src =data.img_url;
//                imgqr.classList.add("imgqrcode");
//                divimg.appendChild(imgqr);
//                //创建二维码下的提示信息
//                var spqr = document.createElement("span");
//                spqr.setAttribute("id","qrcode_msg");
//                spqr.innerText = "请扫码二维码";
//                divimg.appendChild(spqr);
                //复位轮询的标识
                timeout_id = "";
                stop_flag = false;
                //开始轮询扫码状态
                loginJs.pollStatus();
            }
            else{
                //否则提示错误信息
                console.error('Error:', data.text) ;
                alert(data.text);
            }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}

/*
轮询监控扫码状态
*/
loginJs.pollStatus = function() {
    params = new URLSearchParams({
      app_memo: ""
    });
    //异步调用后台获取轮询的状态
    fetch('/login/poll?'+params.toString())
        .then(response => response.json())
        .then(data => {
            //根据轮询状态的结果，将提示文字显示在二维码的下方
            document.getElementById('expiredTip').innerText = data.text;
            //如果成功则跳转到首页
            if (data.code == 0){
                //如果扫码登录成功
                document.getElementById('expiredTip').style.color = "green";
                if (timeout_id != ""){
                   console.log("清除" + timeout_id)
                   clearTimeout(timeout_id);
                   stop_flag = true;
                }
                //就跳转到Home页
                headJs.goHome();
            }
            //如果保存信息报错或超时，则提示错误信息并终止轮询。等待刷新二维码
            else if (data.code == 1102 || data.code == 86038){
                document.getElementById('expiredTip').style.color = "red";
                if (timeout_id != ""){
                   console.log("清除" + timeout_id)
                   clearTimeout(timeout_id);
                   stop_flag = true;
                }
            }
            else{//如果是等待扫码，则持续
                stop_flag = false;
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            //如果
            if (!stop_flag){
                timeout_id = setTimeout(loginJs.pollStatus, 1000);
                console.log("开始定时任务：" + timeout_id);
            }
        }); // 每2秒轮询一次
}
