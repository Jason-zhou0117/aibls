function onscopechange(event){
    target = event.target;
    if (!target.classList.contains("scopenormal")){
        target = target.parentNode;
    }
    if (target.classList.contains("scopecheck")){
        return
    }
    else{
        var divs = document.querySelectorAll('.scopenormal');
        for (i=0;i<divs.length;i++){
            div = divs[i];
            if (div.classList.contains("scopecheck")){
                div.classList.remove("scopecheck");
            }
        }
        target.classList.add("scopecheck");
        ip = document.getElementById('scopetype');
        ip.value = target.dataset.scope;
        loadtaskhis();
    }
}


function loadtaskhis(){
    var year_s = document.getElementById('i_year');
    var month_s = document.getElementById('i_month');
    var day_s = document.getElementById('i_day');
    var ds = year_s.value + "/" + month_s.value + "/" + day_s.value;
    var viewtype = document.getElementById('scopetype').value;
    params = new URLSearchParams({
      cron_date: ds,
      viewtype:viewtype
    });



    var divlist = document.getElementById('divlist');
    divlist.innerHTML = ""
    fetch('/api/loadtaskhis?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                ht = -1;
                var div_hour;
                var div_title;
                var roomids = new Array();
                var ttL_suc = 0;
                var ttl_failt = 0;
                for (i=0;i<data.tasks.length;i++){
                    task = data.tasks[i];
                    if (!roomids.includes(task.room_id)){
                        roomids.push(task.room_id);
                    }
                    ttL_suc = ttL_suc + task.success_num;
                    ttl_failt = ttl_failt + task.failt_num;
                    console.log(ht + "/" + task.cron_hour)
                    if (ht != task.cron_hour){
                        div_hour = document.createElement("div");
                        div_hour.classList.add("hourdiv");
                        divlist.appendChild(div_hour);

                        div_title = document.createElement("div");
                        div_title.classList.add("tasktitle");
                        div_hour.appendChild(div_title);

                        var span_title = document.createElement("span");
                        span_title.innerText = task.cron_hour + ":00";
                        div_title.appendChild(span_title);
                        ht = task.cron_hour;
                    }

                    var div_row = document.createElement("div");
                    div_row.classList.add("taskrow");
                    div_hour.appendChild(div_row);
                    //礼物类型图标
                    var div_rowimg = document.createElement("div");
                    div_rowimg.classList.add("rowimg");
                    div_row.appendChild(div_rowimg);

                    var img_gift = document.createElement("img");

                    img_gift.src = "/static/images/icon_"+task.gift_id+".png";
                    div_rowimg.appendChild(img_gift);
                    //核心文本
                    var div_content = document.createElement("div");
                    div_content.classList.add("rowcontent");
                    div_row.appendChild(div_content);
                    //目标播间
                    var div_room = document.createElement("div");
                    div_room.classList.add("rowroom");
                    div_content.appendChild(div_room);

                    var span_room = document.createElement("span");
                    span_room.innerText = "主播：" + task.room_uname + "(" + task.room_id + ")";
                    div_room.appendChild(span_room);

                    var div_send = document.createElement("div");
                    div_send.classList.add("rowsend");
                    div_content.appendChild(div_send);
                    var span_send = document.createElement("span");
                    span_send.innerText = "操作：" + task.send_uname +"("+loginid_mask(task.send_id) + ")";
                    div_send.appendChild(span_send);

                    //结果数据
                    var div_nums = document.createElement("div");
                    div_nums.classList.add("rownums");
                    div_content.appendChild(div_nums);


                    var span_type = document.createElement("span");
                    if (task.task_type == "1"){
                        span_type.classList.add("hsend");
                        span_type.innerText = "手动";
                    }
                    else{
                        span_type.classList.add("asend");
                        span_type.innerText = "自动";
                    }
                    div_nums.appendChild(span_type);

                    var span_succ = document.createElement("span");
                    span_succ.innerText = "成功" + task.success_num + "笔";
                    div_nums.appendChild(span_succ);

                    var span_failt = document.createElement("span");
                    span_failt.innerText = "失败" + task.failt_num + "笔";
                    div_nums.appendChild(span_failt);
                    //起止时间
                    var div_times = document.createElement("div");
                    div_times.classList.add("rowtimes");
                    div_row.appendChild(div_times);

                    var div_stime = document.createElement("div");
                    div_stime.classList.add("rowtimeitem");
                    div_times.appendChild(div_stime);

                    var span_stime = document.createElement("span");
                    span_stime.innerText = "起：" +task.s_time;
                    div_stime.appendChild(span_stime);

                    var div_etime = document.createElement("div");
                    div_etime.classList.add("rowtimeitem");
                    div_times.appendChild(div_etime);

                    var span_etime = document.createElement("span");
                    span_etime.innerText =  "止：" +task.e_time;
                    div_etime.appendChild(span_etime);

                }
                var span_ttl = document.getElementById('ttlmsg');
                span_ttl.innerText = "当日累计向"+roomids.length+ "个播间发送礼物，共计"
                 + data.tasks.length + "轮。成功" + ttL_suc +"笔，失败" + ttl_failt +"笔！";
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
}