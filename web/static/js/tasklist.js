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

function loadtasksettings(){
    for (i=0;i<24;i++){
        loadtasone(i)
    }
}

function loadtasone(hour){
    var year_s = document.getElementById('i_year');
    var month_s = document.getElementById('i_month');
    var day_s = document.getElementById('i_day');
    var ds = year_s.value + "/" + month_s.value + "/" + day_s.value;

    params = new URLSearchParams({
      cron_date: ds,
      cron_hour: hour
    });
    var div_hour = document.getElementById('taskc-'+hour);
    div_hour.innerHTML = ""
    fetch('/api/task/loadtasklist?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                var ttL_user=0
                for (i=0;i<data.tasks.length;i++){
                    task = data.tasks[i];
                    ttL_user = ttL_user + task.user_num;
                    var div_row = document.createElement("div");
                    div_row.classList.add("tasksetitem");
                    div_hour.appendChild(div_row);
                    //礼物类型图标
                    var div_rowimg = document.createElement("div");
                    div_rowimg.classList.add("rowimg");
                    div_row.appendChild(div_rowimg);

                    var img_gift = document.createElement("img");
                    img_gift.src = "/static/images/icon_rq.png";
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
                    //结果数据
                    var div_nums = document.createElement("div");
                    div_nums.classList.add("rownums");
                    div_content.appendChild(div_nums);

                    var span_user = document.createElement("span");
                    span_user.innerText = "数量：" + task.user_num;
                    div_nums.appendChild(span_user);

                    //起止时间
                    var div_buttons = document.createElement("div");
                    div_buttons.classList.add("buttons");
                    div_row.appendChild(div_buttons);

                    var img_del = document.createElement("img");
                    img_del.src="/static/images/btn_del.png";
                    img_del.setAttribute("data-taskid",task.task_id);
                    img_del.setAttribute("data-hour",hour);
                    img_del.setAttribute("onclick","javascript:ondeltask(event)")
                    div_buttons.appendChild(img_del);
                }
                var span_ttl = document.getElementById('ttl-'+hour);
                span_ttl.innerText = "本时段累计数量："+ttL_user+ "笔";
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

function ondeltask(event){
    target = event.target;
    task_id = target.dataset.taskid;
    hour = target.dataset.hour;
    params = new URLSearchParams({
      task_id: task_id
    });
    fetch('/api/task/deltaskset?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                loadtasone(hour);
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

function addtask(event){
    var year_s = document.getElementById('i_year');
    var month_s = document.getElementById('i_month');
    var day_s = document.getElementById('i_day');
    var ds = year_s.value + "/" + month_s.value + "/" + day_s.value;
    target = event.target;
    hour = target.dataset.hour;
    if (typeof hour === "undefined"){
        alert("点太快了,页面没有加载完毕!");
        return
    }
    params = new URLSearchParams({
        cron_date:ds,
        cron_hour:hour
     });
     window.location.href = "/updatetaskroom?" + params.toString();

}