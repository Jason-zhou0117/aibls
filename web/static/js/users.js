function ondeluser(event){
    var target = event.target;
    user_id = target.dataset.uid
    formData = new FormData();
    formData.append('user_id', user_id);
    fetch('/api/delacuser',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                location.reload()
            }
            else{
                console.error('Error:', data.text) ;
                alert(data.text);
            }
        })
        .catch(error => console.error('Error:', error))
        .finally();

}

timeout_id = "";
success_flag = false;

function show_paywindow(){
   var mask = document.getElementById('paymask');
  mask.classList.replace("pay_mask_hidden","pay_mask_show");
}

function hidde_paywindow(){
   var mask = document.getElementById('paymask');
    mask.classList.replace("pay_mask_show","pay_mask_hidden");
    if (timeout_id != ""){
        console.log("清除" + timeout_id)
        clearTimeout(timeout_id);
        success_flag = true;
    }
}

function onmoneykey(event){
    if (event.keyCode === 13) {
        target = event.target;
        user_id = target.dataset.uid;
        pay_money = target.value;
        if (isNum(pay_money)){
            pn = parseInt(pay_money);
            show_paywindow();
            params = new URLSearchParams({
              user_id: user_id,
              pay_num: pn
            });
            dorefresqrcode(params);
        }
        else{
            alert("输入正整数")
        }
    }
    else{
        target = event.target;
        pay_money = target.value;
        if (isNum(pay_money)){
            var gold_num = document.getElementById('gold_num');
            gold_num.innerText = parseInt(pay_money) * 10;
        }
    }
}

function isNum(str) {
    const num = Number(str);
    return !Number.isNaN(num) && Number.isInteger(num);
}

function payment(event){
    target = event.target;
    user_id = target.dataset.uid;

    var imgqr = document.getElementById('payqrcode');
    imgqr.setAttribute("data-uid",user_id);
    var inppay = document.getElementById('paymoney');
    inppay.setAttribute("data-uid",user_id);

    show_paywindow()
    pay_money = inppay.value;
    if (isNum(pay_money)){
        pn = parseInt(pay_money);
        show_paywindow();
        params = new URLSearchParams({
            user_id: user_id,
            pay_num: pn
        });
        dorefresqrcode(params);
    }
}

function dorefresqrcode(params){
    if (timeout_id != ""){
        console.log("清除" + timeout_id)
        clearTimeout(timeout_id);
        success_flag = true;
    }

    fetch('/api/getpayqrcode?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                var imgqr = document.getElementById('payqrcode');
                imgqr.setAttribute("data-orderid",data.result.order_id);
                imgqr.setAttribute("data-uid",user_id);
                imgqr.setAttribute("onclick","javascript:payment(event);");
                imgqr.src=data.img_url;

                var inppay = document.getElementById('paymoney');
                inppay.setAttribute("data-orderid",data.result.order_id);
                inppay.setAttribute("data-uid",user_id);

                success_flag = false;
                queryStatus();
             }
             else{
                console.error('Error:', data.text) ;
                alert(data.text);
             }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}

function showMask(text) {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_hidden","mask_show");
}

function hideMask() {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_show","mask_hidden");
}

function reloadstatus(){
    showMask();
    fetch('/api/refreshexpuser')
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                location.reload();
             }
             else{
                console.error('Error:', data.text) ;
                alert(data.text);
             }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}

function queryStatus() {
    var imgqr = document.getElementById('payqrcode');
    order_id =imgqr.dataset.orderid;
    user_id = imgqr.dataset.uid;
    params = new URLSearchParams({
      user_id: user_id,
      order_id: order_id
    });
    fetch('/api/querypayqrcode?'+params.toString())
        .then(response => response.json())
        .then(data => {

            if (data.code == 0){
                if (data.result.status == 5){
                    if (timeout_id != ""){
                       console.log("清除" + timeout_id)
                       clearTimeout(timeout_id);
                       success_flag = true;
                    }
                    location.reload();
                }

            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            if (!success_flag){
                timeout_id = setTimeout(queryStatus, 1000);
                console.log("开始定时任务：" + timeout_id);
            }
        }); // 每2秒轮询一次
}

function refreshone(event){
    target = event.target;
    user_id=target.dataset.uid;
    fetch('/api/refreshoneuser?user_id='+user_id)
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                location.reload();
             }
             else{
                console.error('Error:', data.text) ;
                alert(data.text);
             }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}