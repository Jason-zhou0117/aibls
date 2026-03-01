
function showMask(text) {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_hidden","mask_show");
}

function hideMask() {
  var mask = document.getElementById('fullmask');
  mask.classList.replace("mask_show","mask_hidden");
}

function doupdategold(){
    user_count = parseInt(document.getElementById('data-usnum').innerText);
    pagesize = 50;
    maxlen = Math.ceil(user_count/pagesize);
    showMask();
    do_refresh_user(maxlen,1,pagesize);
}

function do_refresh_user(maxlen,page_num,pagesize){
    if (page_num <= maxlen){
        var maskmsg = document.getElementById('maskmsg');
        maskmsg.innerText = "执行进度：" + page_num + "/" + maxlen + "；请耐心等待..."
        fetch('/api/updategold?pagesize='+ pagesize +'&pagenum=' + page_num)
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                do_refresh_user(maxlen,(page_num+1),pagesize)
             }
             else{
                console.error('Error:', data.text) ;
                alert("网络中断了,需要重新更新");
                hideMask();
                location.reload();
             }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
        });
    }
    else{
        hideMask();
        alert("更新成功");
        location.reload();
    }
}

function dorefreshroom(){
    user_count = parseInt(document.getElementById('data-rmnum').innerText);
    pagesize = 50;
    maxlen = Math.ceil(user_count/pagesize);
    showMask();
    do_refresh_room(maxlen,1,pagesize);
}

function do_refresh_room(maxlen,page_num,pagesize){
    if (page_num <= maxlen){
        var maskmsg = document.getElementById('maskmsg');
        maskmsg.innerText = "执行进度：" + page_num + "/" + maxlen + "；请耐心等待..."
        fetch('/api/refreshroom?pagesize='+pagesize+'&pagenum=' + page_num)
            .then(response => response.json())
            .then(data => {
                 if (data.code == 0){
                    do_refresh_room(maxlen,(page_num+1),pagesize)
                 }
                 else{
                    console.error('Error:', data.text) ;
                    alert("网络中断了,需要重新更新");
                    hideMask();
                    location.reload();
                 }
            })
            .catch(error => console.error('Error:', error))
            .finally(() => {
            });
    }
    else{
        hideMask();
        alert("更新成功");
        location.reload();
    }
}

function load_user_count(){
    // 使用 Fetch API 请求数据
    fetch('/api/getusertotals')
            .then(response => response.json())  // 解析 JSON 格式的响应体
            .then(data => {
                // 更新页面内容
                document.getElementById('data-usnum').innerText = data.us_num ;
                document.getElementById('data-ndnum').innerText = data.nd_num ;
            })
            .catch(error => console.error('Error:', error));
}

function load_room_count(){
    fetch('/api/getroomcounts')
            .then(response => response.json())  // 解析 JSON 格式的响应体
            .then(data => {
                // 更新页面内容
                document.getElementById('data-rmnum').innerText = data.rm_num ;
                document.getElementById('data-fvnum').innerText = data.fv_num ;
            })
            .catch(error => console.error('Error:', error));
}

function load_task_count(){
    fetch('/api/task/counttask')
            .then(response => response.json())  // 解析 JSON 格式的响应体
            .then(data => {
                // 更新页面内容
                document.getElementById('task-num').innerText = data.tasknum ;
            })
            .catch(error => console.error('Error:', error));
}

function load_schedule_running(){
    fetch('/api/sche/getstatus')
            .then(response => response.json())  // 解析 JSON 格式的响应体
            .then(data => {
                if (data.is_run){
                    document.getElementById('task-running').style.color = "green";
                    document.getElementById('task-running').innerText = "已启动" ;
                }
                else{
                    document.getElementById('task-running').style.color = "red";
                    document.getElementById('task-running').innerText = "未启动" ;
                }

            })
            .catch(error => console.error('Error:', error));
}

function change_schedule_status(){
    fetch('/api/sche/runandstop')
            .then(response => response.json())  // 解析 JSON 格式的响应体
            .then(data => {
                if (data.code == 0){
                    if (data.is_run){
                        document.getElementById('task-running').style.color = "green";
                        document.getElementById('task-running').innerText = "已启动" ;
                    }
                    else{
                        document.getElementById('task-running').style.color = "red";
                        document.getElementById('task-running').innerText = "未启动" ;
                    }
                }
                else{
                    alert(data.text);
                }
                load_task_count();
            })
            .catch(error => console.error('Error:', error));

}

