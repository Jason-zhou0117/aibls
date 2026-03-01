function onhourchange(event){
    target = event.target;
    if (!target.dataset.hasOwnProperty("checked")){
        target = target.parentNode;
    }
    check = target.dataset.checked;
    if (check == "false"){
        target.setAttribute("data-checked",true);
        target.classList.add("hoursitem-checked");
    }
    else{
        target.setAttribute("data-checked",false);
        target.classList.remove("hoursitem-checked");
    }
}

function formatDate(date) {
    formatterCN = new Intl.DateTimeFormat("zh-CN", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    });
    return formatterCN.format(date);
}

function initdatevalue(){
    dtnow = new Date();
    var year_s = document.getElementById('i_year');
    year_s.value = dtnow.getFullYear();
    var month_s = document.getElementById('i_month');
    ms = dtnow.getMonth()+1;
    if (ms < 10){
        ms = "0" + ms;
    }
    month_s.value = ms;
    var day_s = document.getElementById('i_day');
    ds = dtnow.getDate();
    if (ds < 10){
        ds = "0" + ds;
    }
    day_s.value = ds;

    var min_s = document.getElementById('i_mins');
    min_s.value = "1";

}


function initUserlist(){
    dtnow = new Date();
    var senddate = formatDate(dtnow);
    var sendhour = dtnow.getHours();

    params = new URLSearchParams({
      senddate: senddate,
      sendhour: sendhour
    });

    url ='/api/task/loadsetalluser?'+params.toString();
    load_users(url)
}

function initHourusers(){
    cron_date = document.getElementById('cron_date').value;
    cron_hour = document.getElementById('cron_hour').value;
    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;

    params = new URLSearchParams({
      cron_date: cron_date,
      cron_hour: cron_hour,
      room_id:room_id
    });
    url ='/api/task/loadsethouruser?'+params.toString();
    load_users(url)
}

function load_users(url){
    var divusers = document.getElementById('sendusers');
    divusers.innerHTML = ""

    //复位全选
    imgall = document.getElementById('imgselall');
    imgall.setAttribute("data-selectall",false);
    imgall.src="/static/images/icon_unsel.png";

    fetch(url)
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                var ix=1;
                console.log(data.users.length)
                for (i=0;i<data.users.length;i++){

                    user = data.users[i]
                    var div_item = document.createElement("div");
                    div_item.setAttribute("data-uid",user.user_id);
                    div_item.setAttribute("data-index",ix);
                    div_item.classList.add("useritem");
                    divusers.appendChild(div_item);

                    var div_itemtext = document.createElement("div");
                    div_itemtext.classList.add("itemtextnobut");
                    div_item.appendChild(div_itemtext);
                    //序号
                    var div_itemindex = document.createElement("div");
                    div_itemindex.classList.add("userindex");
                    div_itemtext.appendChild(div_itemindex);
                    var span_itemindex = document.createElement("span");
                    span_itemindex.innerText=ix;
                    div_itemindex.appendChild(span_itemindex);
                    //选择
                    var img_check = document.createElement("img");
                    img_check.classList.add("imgcheck");
                    img_check.classList.add("unchecked");
                    img_check.setAttribute("data-index",ix);
                    img_check.setAttribute("data-checked",false);
                    img_check.setAttribute("data-userid",user.user_id);
                    img_check.src="/static/images/icon_unsel.png";
                    img_check.addEventListener('click', checkself)
                    div_itemtext.appendChild(img_check);
                    //头像
                    var img_face = document.createElement("img");
                    img_face.classList.add("imgface");
                    img_face.src= user.face;
                    div_itemtext.appendChild(img_face);
                    //主体内容
                    var div_content = document.createElement("div");
                    div_content.classList.add("usercontent");
                    div_itemtext.appendChild(div_content);
                    //用户名和状态
                    var div_username = document.createElement("div");
                    div_username.classList.add("user_name");
                    div_content.appendChild(div_username);
                    var span_username = document.createElement("span");
                    span_username.innerText = user.name;
                    div_username.appendChild(span_username);
                    if (user.lgstatus =='0'){
                        var span_status = document.createElement("span");
                        span_status.innerText = "正常";
                        span_status.classList.add("normal");
                        div_username.appendChild(span_status);
                    }else{
                        var span_status = document.createElement("span");
                        span_status.innerText = "掉线";
                        span_status.classList.add("unlink");
                        div_username.appendChild(span_status);
                    }
                    //附加信息
                    var div_other = document.createElement("div");
                    div_other.classList.add("otheritem");
                    div_content.appendChild(div_other);
                    //电池
                    var img_dian = document.createElement("img");
                    img_dian.classList.add("goldicon");
                    img_dian.src= "/static/images/btn_nodian.png";
                    div_other.appendChild(img_dian);
                    var span_gold = document.createElement("span");
                    span_gold.innerText = user.gold_num;
                    div_other.appendChild(span_gold);
                    var span_uid = document.createElement("span");
                    span_uid.innerText = "(UID:" + user.user_id + ")";
                    div_other.appendChild(span_uid);
                    //按钮区域
                    var div_button = document.createElement("div");
                    div_button.classList.add("nobuttons");
                    div_itemtext.appendChild(div_button);

                    ix=ix+1;
                }
             }
             else{
                console.error('Error:', data.text) ;
                alert(data.text);
             }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}

function checkself(event){
    target = event.target;
    ischecked = target.dataset.checked;
    if (ischecked == "true"){
        target.classList.replace("checked","unchecked");
        target.src="/static/images/icon_unsel.png";
        target.setAttribute("data-checked",false);
    }
    else{
        target.classList.replace("unchecked","checked");
        target.src="/static/images/icon_checked.png";
        target.setAttribute("data-checked",true);
    }
}

function selectAllUser(event){
    imgall = document.getElementById('imgselall');
    isselected = imgall.dataset.selectall;

    if (isselected == "true"){

        var imgs = document.querySelectorAll('.checked');
        for(i=0;i<imgs.length;i++){
            img = imgs[i];
            img.classList.replace("checked","unchecked");
            img.src="/static/images/icon_unsel.png";
            img.setAttribute("data-checked",false);
        }
        imgall.setAttribute("data-selectall",false);
        imgall.src="/static/images/icon_unsel.png";
    }
    else{
        var imgs = document.querySelectorAll('.unchecked');

        for (i=0;i<imgs.length;i++){
            img = imgs[i];
            img.classList.replace("unchecked","checked");
            img.src="/static/images/icon_checked.png";
            img.setAttribute("data-checked",true);
        }
        imgall.setAttribute("data-selectall",true);
        imgall.src="/static/images/icon_checked.png";
    }
}

function dochoice(){
    s_start = document.getElementById('ix-start').value.trim();
    s_end = document.getElementById('ix-end').value.trim();
    if (s_start == "" || s_end ==""){
        alert("序号必须填写且为数字");
        return
    }
    v_start = parseInt(s_start);
    v_end = parseInt(s_end);
    if (isNaN(v_start) == true || isNaN(v_end) == true){
        alert("序号必须为数字");
        return
    }
    if (v_start > v_end){
        alert("序号请按左小右大的填写");
        return
    }
    //复位全选
    imgall = document.getElementById('imgselall');
    imgall.setAttribute("data-selectall",false);
    imgall.src="/static/images/icon_unsel.png";
    //复位用户已选
    var imgs = document.querySelectorAll('.checked');
    for(i=0;i<imgs.length;i++){
        img = imgs[i];
        img.classList.replace("checked","unchecked");
        img.src="/static/images/icon_unsel.png";
    }
    //开始勾选
    var imgs = document.querySelectorAll('.imgcheck');
    for(i=0;i<imgs.length;i++){
        img = imgs[i];
        ix = parseInt(img.dataset.index);
        if (ix>=v_start && ix<=v_end){
            img.classList.replace("unchecked","checked");
            img.src="/static/images/icon_checked.png";
        }
    }
}

function showMask(text) {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_hidden","mask_show");
}

function hideMask() {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_show","mask_hidden");
}

function getHours(){
    var hourdivs = document.querySelectorAll('.hoursitem-checked');
    hoursi = new Array();
    for(i=0;i<hourdivs.length;i++){
        hoursi[i] = parseInt(hourdivs[i].dataset.hour);
    }
    return hoursi;
}

function sendData(){

    var year_s = document.getElementById('i_year');
    var month_s = document.getElementById('i_month');
    var day_s = document.getElementById('i_day');
    var dates = year_s.value + "/" + month_s.value + "/" + day_s.value;
    var mins = document.getElementById('i_mins').value;

    var hours = getHours();
    if (hours.length <= 0){
        alert("没有选择要自动执行的时段");
        return
    }

    var imgs = document.querySelectorAll('.checked');
    user_ids = new Array()
    for(i=0;i<imgs.length;i++){
        user_ids[i] = imgs[i].dataset.userid;
    }
    if (user_ids.length <= 0){
        alert("没有选择要投喂的账号！");
        return
    }
    showMask();
    do_pos_data(dates,hours,mins,user_ids);
}

function sendhourdata(){
    var dates = document.getElementById('cron_date').value;
    var mins = document.getElementById('i_mins').value;
    var hours = getHours();
    if (hours.length <= 0){
        alert("没有选择要自动执行的时段");
        return
    }

    var imgs = document.querySelectorAll('.checked');
    user_ids = new Array()
    for(i=0;i<imgs.length;i++){
        user_ids[i] = imgs[i].dataset.userid;
    }
    if (user_ids.length <= 0){
        alert("没有选择要投喂的账号！");
        return
    }
    showMask();
    do_pos_data(dates,hours,mins,user_ids);
}

function do_pos_data(dates,hours,mins,user_ids){
    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;
    room_uname = div_room.dataset.roomuname;

    formData = new FormData();
    var maskmsg = document.getElementById('maskmsg');
    maskmsg.innerText = "正在保存；请耐心等待..."

    formData.append('room_id', room_id);
    formData.append('room_uname', room_uname);
    formData.append('user_ids', user_ids);
    formData.append('cron_date', dates);
    formData.append('cron_hours', hours);
    formData.append('cron_minute', mins);
    formData.append('gift_id', "33988");
    formData.append('gift_num', 1);
    fetch('/api/task/savenewsetting',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                alert("已成功保存配置，如要执行，请在首页启动自动任务")
                gohome();
            }else{
                console.error('Error:', data.text);
                alert("网络断了，刷新页面或退出本页在进入重试吧！")
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            hideMask();
        });
}


function updatenum(data){
    var success = document.getElementById('success_nm');
    var failt = document.getElementById('failt_nm');
    success.value = parseInt(success.value) + data.result.suc_num;
    failt.value = parseInt(failt.value) + data.result.flt_num;
    console.log("成功：" + success.value + ";失败：" + failt.value);
}

function goback(event){
    target = event.target;
    cron_date = target.dataset.date;
    cron_hour = target.dataset.hour;
    params = new URLSearchParams({
              cron_date:cron_date,
              cron_hour:cron_hour
    });
    window.location.href = "/updatetaskroom?" + params.toString();
}