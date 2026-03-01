function formatDate(date) {
    formatterCN = new Intl.DateTimeFormat("zh-CN", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    });
    return formatterCN.format(date);
}

function onpartnerchange(event){
    target = event.target;
    if (!target.dataset.hasOwnProperty("checked")){
        target = target.parentNode;
    }
    check = target.dataset.checked;
    if (check == "false"){
        target.setAttribute("data-checked",true);
        target.classList.add("partneritem-checked");
    }
    else{
        target.setAttribute("data-checked",false);
        target.classList.remove("partneritem-checked");
    }
    load_userlist();
}

function initauths(){
    var divpartner = document.getElementById('partners');
    divpartner.innerHTML = ""
    var login_id = document.getElementById('login_id').value;
    fetch('/api/loadauths_send')
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                for (i=0;i<data.authes.length;i++){
                    partner = data.authes[i]
                    var div_item = document.createElement("div");
                    div_item.setAttribute("data-sourceid",partner.source_uid);
                    div_item.setAttribute("onclick","javascript:onpartnerchange(event);");
                    div_item.classList.add("partneritem");
                    if (partner.source_uid == login_id){
                        div_item.classList.add("partneritem-checked");
                        div_item.setAttribute("data-checked",true);
                    }else{
                        div_item.setAttribute("data-checked",false);
                    }
                    divpartner.appendChild(div_item);
                    var span_item = document.createElement("span");
                    span_item.innerText = partner.s_uname + "(" + loginid_mask(partner.source_uid) + ")";
                    div_item.appendChild(span_item);
                }
                load_userlist();
             }
             else{
                console.error('Error:', data.text) ;
                alert(data.text);
             }
        })
        .catch(error => console.error('Error:', error))
        .finally();
}


function load_userlist(){
    var ch_parts = document.querySelectorAll('.partneritem-checked');
    var partner_ids = new Array();
    for (i=0;i<ch_parts.length;i++){
        div_part = ch_parts[i];
        partner_ids[i] = div_part.dataset.sourceid;
    }
    var divusers = document.getElementById('sendusers');
    divusers.innerHTML = ""
    dtnow = new Date();
    var senddate = formatDate(dtnow);
    var sendhour = dtnow.getHours();
    document.getElementById('sendhour').innerText = "时段：" + sendhour + "点";
    document.getElementById('senddate').innerText = "日期：" + senddate ;

    var ip_isfirst = document.getElementById('ip_isfirst');
    var ip_giftnum = document.getElementById('ip_giftnum');

    var selectElement = document.getElementById("gift_type");
    var gift_id = selectElement.options[selectElement.selectedIndex].value;

    //复位全选
    imgall = document.getElementById('imgselall');
    imgall.setAttribute("data-selectall",false);
    imgall.src="/static/images/icon_unsel.png";

    var divroom = document.getElementById('roominfo');
    var room_id = divroom.dataset.roomid;
    var room_uid = divroom.dataset.roomuid;


    formData = new FormData();
    formData.append('senddate', senddate);
    formData.append('sendhour', sendhour);
    formData.append('partners', partner_ids);
    formData.append('is_first', ip_isfirst.value);
    formData.append('gift_id', gift_id);
    formData.append('room_id', room_id);
    formData.append('room_uid', room_uid);
    fetch('/api/loadavaluser_send',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                var divusers = document.getElementById('sendusers');
                divusers.innerHTML = ""
                document.getElementById('usernum').innerText = "可用账号：" + data.ucount + "人";
                part_id = "";
                ava_gnum = 0;
                var span_gnum = null;
                for (i=0;i<data.users.length;i++){
                    var ix = i+1;
                    user = data.users[i]
                    ava_gnum = ava_gnum +1;
                    if (part_id != user.login_id){
                        var div_group = document.createElement("div");
                        div_group.setAttribute("data-pid",user.login_id);
                        div_group.setAttribute("data-index",ix);
                        div_group.classList.add("grouptitle");
                        divusers.appendChild(div_group);

                        var span_gtitle = document.createElement("span");
                        span_gtitle.innerText= "如下账号归属：" + loginid_mask(user.login_id);
                        span_gtitle.classList.add("partnerid");
                        div_group.appendChild(span_gtitle);

                        if (span_gnum !== null){
                            span_gnum.innerText = "可用用户数：" + (ava_gnum-1);
                            ava_gnum = 1;
                        }
                        span_gnum = document.createElement("span");
                        span_gnum.classList.add("pusernum");
                        div_group.appendChild(span_gnum);

                        part_id=user.login_id;
                    }
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
                    img_check.setAttribute("data-loginid",user.login_id);
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
                    var div_uc = document.createElement("div");
                    div_username.appendChild(div_uc);
                    var span_username = document.createElement("span");
                    span_username.innerText = user.name;;
                    div_uc.appendChild(span_username);
                    var span_app = document.createElement("span");
                    span_app.innerText = '['+ user.app_memo +']';
                    div_uc.appendChild(span_app);
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

                }
                if (span_gnum !== null){
                   span_gnum.innerText = "可用用户数：" + ava_gnum;
                   ava_gnum = 1;
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

pro_cur = 0;
pro_ttl = 0;
show_result = false;

function sendData(){

    user_idgroups = new Array();
    var imgs = document.querySelectorAll('.checked');
    if (imgs.length <=0){
        alert("没有选择投喂的账户！");
        return
    }
    console.log(imgs)
    groupindex = 0;
    user_ids = new Array()
    pagesize = 20;
    threads = 2;
    thread_a = new Array();
    tmp_thr = new Array();
    tmp_thr[0] = new Array();
    tmp_thr[1] = new Array();
    tmp_ix = -1;

    logins = new Array();

    for(i=0;i<imgs.length;i++){
        th_ix = i % threads;
        img = imgs[i];
        if (th_ix == 0) {
            tmp_ix = tmp_ix + 1;
        }
        tmp_thr[th_ix][tmp_ix] = img.dataset.userid;
        lgid = img.dataset.loginid;
        if (!logins.includes(lgid)){
            logins.push(lgid);
        }
    }

    for(i=0;i<tmp_thr.length;i++){
        tmp = tmp_thr[i];
        thread_a[i] = new Array();
        groupindex = 0;
        for (j=0;j<tmp.length;j++){
            us_ix = j % pagesize;
            if (us_ix == 0){
                user_ids = new Array()
                thread_a[i][groupindex] = user_ids;
                groupindex = groupindex + 1;
            }
            user_ids[us_ix] = tmp[j]
        }
    }
    console.log(logins);
    console.log(thread_a);
    createtaskhis_double(logins,thread_a);
}

function createtaskhis_double(logins,thread_a){
    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;
    room_uname = div_room.dataset.roomuname;
    dtnow = new Date();
    var senddate = formatDate(dtnow);
    var sendhour = dtnow.getHours();
    var task_id = document.getElementById('task_id_h').value;

    var ip_isfirst = document.getElementById('ip_isfirst');
    var ip_giftnum = document.getElementById('ip_giftnum');

    var selectElement = document.getElementById("gift_type");
    var gift_id = selectElement.options[selectElement.selectedIndex].value;


    formData = new FormData();
    formData.append('room_id', room_id);
    formData.append('room_uname', room_uname);
    formData.append('login_ids', logins);
    formData.append('cron_date', senddate);
    formData.append('cron_hour', sendhour);
    formData.append('task_id', task_id);
    formData.append('gift_id', gift_id);
    fetch('/api/createtaskhis',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                showMask();
                pro_cur=0;
                pro_ttl = (thread_a[0].length + thread_a[1].length);
                show_result = false;
                do_pos_data(thread_a[0],0);
                if (thread_a[1].length > 0 && thread_a[1][0] !== undefined){
                    do_pos_data(thread_a[1],0);
                }

            }else{
                console.error('Error:', data.text);
                alert("网络断了，刷新页面或退出本页在进入重试吧！")
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
}

function sendData_single(){

    user_idgroups = new Array();
    var imgs = document.querySelectorAll('.checked');
    if (imgs.length <=0){
        alert("没有选择投喂的账户！");
        return
    }
    groupindex = 0;
    user_ids = new Array()
    pagesize = 40;

    logins = new Array();

    for(i=0;i<imgs.length;i++){
        img = imgs[i];
        us_ix = i % pagesize;
        if (us_ix == 0){
            user_ids = new Array()
            user_idgroups[groupindex] = user_ids;
            groupindex = groupindex + 1;
        }
        user_ids[us_ix] = img.dataset.userid;
        lgid = img.dataset.loginid;
        if (!logins.includes(lgid)){
            logins.push(lgid);
        }
    }

    createtaskhis_single(logins,user_idgroups);
}

function createtaskhis_single(logins,user_idgroups){
    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;
    room_uname = div_room.dataset.roomuname;
    dtnow = new Date();
    var senddate = formatDate(dtnow);
    var sendhour = dtnow.getHours();
    var task_id = document.getElementById('task_id_h').value;

    var ip_isfirst = document.getElementById('ip_isfirst');
    var ip_giftnum = document.getElementById('ip_giftnum');

    var selectElement = document.getElementById("gift_type");
    var gift_id = selectElement.options[selectElement.selectedIndex].value;


    formData = new FormData();
    formData.append('room_id', room_id);
    formData.append('room_uname', room_uname);
    formData.append('login_ids', logins);
    formData.append('cron_date', senddate);
    formData.append('cron_hour', sendhour);
    formData.append('task_id', task_id);
    formData.append('gift_id', gift_id);
    fetch('/api/createtaskhis',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                showMask();
                pro_cur=0;
                pro_ttl = (user_idgroups.length);
                show_result = false;
                do_pos_data(user_idgroups,0);
            }else{
                console.error('Error:', data.text);
                alert("网络断了，刷新页面或退出本页在进入重试吧！")
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
}


function do_pos_data(user_idgroups,gindex){
    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;
    room_uname = div_room.dataset.roomuname;
    dtnow = new Date();
    var senddate = formatDate(dtnow);
    var sendhour = dtnow.getHours();
    var task_id = document.getElementById('task_id_h').value;
    var maskmsg = document.getElementById('maskmsg');
    var ip_isfirst = document.getElementById('ip_isfirst');
    var ip_giftnum = document.getElementById('ip_giftnum');

    var selectElement = document.getElementById("gift_type");
    var gift_id = selectElement.options[selectElement.selectedIndex].value;

    maskmsg.innerText = "执行进度：" + (pro_cur+1) + "/" + pro_ttl + "；请耐心等待..."
    user_ids = user_idgroups[gindex];


    formData = new FormData();
    formData.append('room_id', room_id);
    formData.append('room_uname', room_uname);
    console.log(user_ids)
    formData.append('user_ids', user_ids);
    formData.append('cron_date', senddate);
    formData.append('cron_hour', sendhour);
    formData.append('task_id', task_id);
    formData.append('gift_id', gift_id);
    formData.append('gift_num', ip_giftnum.value);
    formData.append('is_first', ip_isfirst.value);
    fetch('/api/sendgiftonce',{
        method:"post",
        body:formData,
        headers:{}
        })
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                updatenum(data);
                pro_cur = pro_cur + 1;
                maskmsg.innerText = "执行进度：" + (pro_cur+1) + "/" + pro_ttl + "；请耐心等待..."
                if ((gindex+1) < user_idgroups.length ){
                    do_pos_data(user_idgroups,(gindex+1))
                }else{
                    if (pro_cur == pro_ttl && !show_result){
                        hideMask();
                        show_result = true;
                        var success = document.getElementById('success_nm');
                        var failt = document.getElementById('failt_nm');
                        alert("完成投喂，成功" + success.value + "笔，失败" + failt.value + "笔");
                        if (gift_id == "33988"){
                            get_rank()
                        }
                        else{
                            location.reload();
                        }
                    }
                }
            }else{
                console.error('Error:', data.text);
                alert("网络断了，刷新页面或退出本页在进入重试吧！")
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
}

function get_rank(){

    div_room = document.getElementById('roominfo');
    room_id = div_room.dataset.roomid;
    var task_id = document.getElementById('task_id_h').value;

    params = new URLSearchParams({
      room_id: room_id,
      task_id: task_id
    });

     fetch('/api/load_renqib?'+params.toString())
        .then(response => response.json())
        .then(data => {
            if (data.code == 0){
                alert("其中有" + data.norank + "笔未能在人气榜朱助力上生效");
                location.reload();
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
}


function updatenum(data){
    var success = document.getElementById('success_nm');
    var failt = document.getElementById('failt_nm');
    success.value = parseInt(success.value) + data.result.suc_num;
    failt.value = parseInt(failt.value) + data.result.flt_num;
    console.log("成功：" + success.value + ";失败：" + failt.value);
}

function onfirstclick(event){
    target = event.target;
    if (!target.classList.contains("firstitem")){
        target = target.parentNode;
    }
    if (target.id == "b_isfirst"){
        if (!target.classList.contains("firstitem-checked")){
            target.classList.add("firstitem-checked");
            btn_set = document.getElementById('b_setting');
            btn_set.classList.remove("firstitem-checked");
            ip_giftnum = document.getElementById('ip_giftnum');
            ip_giftnum.disabled = true;
            ip_giftnum.value = "1";
            document.getElementById('ip_isfirst').value = "1";
        }
    }
    else{
        if (!target.classList.contains("firstitem-checked")){
            target.classList.add("firstitem-checked");
            btn_first = document.getElementById('b_isfirst');
            btn_first.classList.remove("firstitem-checked");
            ip_giftnum = document.getElementById('ip_giftnum');
            document.getElementById('ip_isfirst').value = "0";
            ip_giftnum.disabled = false;
            ip_giftnum.value = "1";
        }
    }
    load_userlist();
}

function onselectclick(value){
    op = document.getElementById('gift-' + value);
    visfirst = op.dataset.isfirst;
    vdfnum = op.dataset.dfnum;
    if (visfirst != '0'){
        btn_first = document.getElementById('b_isfirst');
        btn_first.classList.remove("firstitem-checked");
        btn_first.classList.add("firstitem-disabled");
        btn_first.removeAttribute("onclick");
        btn_set = document.getElementById('b_setting');
        btn_set.classList.add("firstitem-checked");
        btn_set.removeAttribute("onclick");
        document.getElementById('ip_isfirst').value = visfirst;
        ip_giftnum = document.getElementById('ip_giftnum');
        ip_giftnum.disabled = false;
        ip_giftnum.value = vdfnum;
    }
    else{
        btn_first = document.getElementById('b_isfirst');
        btn_first.classList.remove("firstitem-disabled");
        btn_first.classList.add("firstitem-checked");
        btn_first.setAttribute("onclick","javascript:onfirstclick(event);");

        btn_set = document.getElementById('b_setting');
        btn_set.classList.remove("firstitem-checked");
        btn_set.setAttribute("onclick","javascript:onfirstclick(event);");

        document.getElementById('ip_isfirst').value = visfirst;

        ip_giftnum = document.getElementById('ip_giftnum');
        ip_giftnum.disabled = true;
        ip_giftnum.value = vdfnum;
    }
    load_userlist();
}

