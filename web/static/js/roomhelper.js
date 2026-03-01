var roomJs = {}

roomJs.ondel = function (event){
            var target = event.target;
            room_id = target.dataset.roomid
            formData = new FormData();
            formData.append('room_id', room_id);
            fetch('/api/delroom',{
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

roomJs.onFilterKeyPress = function (event){
    if (event.key === 'Enter' || event.keyCode === 13) {
        roomJs.filterRoom();
    }
}

roomJs.filterRoom = function (){
    filtern = document.getElementById('room_id').value;

    params = new URLSearchParams({
      room_id: filtern
    });
    var divlist = document.getElementById('divrooms');
    divlist.innerHTML = ""
    fetch('/api/searchrooms?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                for (i=0;i<data.rooms.length;i++){
                    room = data.rooms[i];
                    var div_row = document.createElement("div");
                    div_row.classList.add("roominfo");
                    div_row.setAttribute("data-roomid",room.room_id);
                    divlist.appendChild(div_row);

                    var imgcover = document.createElement("img");
                    imgcover.classList.add("cover");
                    imgcover.src = room.room_cover;
                    div_row.appendChild(imgcover);

                    var divcontent = document.createElement("div");
                    divcontent.classList.add("roomcontents");
                    div_row.appendChild(divcontent);

                    var ptitle = document.createElement("p");
                    ptitle.classList.add("room_title");
                    ptitle.innerText = room.room_name;
                    divcontent.appendChild(ptitle);

                    var pupper = document.createElement("p");
                    pupper.classList.add("roomidp");
                    pupper.innerText = "房号：" + room.room_id;
                    divcontent.appendChild(pupper);

                    var pupper = document.createElement("p");
                    pupper.classList.add("upuserp");
                    pupper.innerText = "UP："+room.room_user_name;
                    divcontent.appendChild(pupper);

                    var divbuttons = document.createElement("div");
                    divbuttons.classList.add("buttons");
                    div_row.appendChild(divbuttons);

                    var imgfav = document.createElement("img");
                    if (room.is_favorites == "Y"){
                        imgfav.src = "/static/images/btn_fav.png";
                    }
                    else{
                        imgfav.src = "/static/images/btn_unfav.png";
                    }
                    imgfav.setAttribute("data-roomid",room.room_id);
                    imgfav.setAttribute("data-hasfav",room.is_favorites);
                    imgfav.classList.add("fav_button");
                    imgfav.setAttribute("onclick","javascript:roomJs.onFav(event);");
                    divbuttons.appendChild(imgfav);

                    var imgsend = document.createElement("img");
                    imgsend.src = "/static/images/btn_send.png";
                    imgsend.classList.add("send_button");
                    imgsend.setAttribute("data-roomid",room.room_id);
                    imgsend.setAttribute("onclick","javascript:roomJs.goSend(event)");
                    divbuttons.appendChild(imgsend);
                }
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

roomJs.doNewRoom = function (){
            room_id = document.getElementById('room_id').value;
            if (room_id == ""){
                document.getElementById('msg_txt').innerText = "请输入房间号"
                return
            }
            formData = new FormData();
            formData.append('room_id', room_id);
            fetch('/api/updateroom',{
                    method:"post",
                    body:formData,
                    headers:{}
                })
                .then(response => response.json())
                .then(data => {
                    if (data.code == 0){
                        roomJs.filterRoom();
                    }
                    else{
                        document.getElementById('msg_txt').innerText = data.message;
                        console.error('Error:', data.message) ;
                    }
                })
                .catch(error => console.error('Error:', error))
                .finally(() => {
                });
}

roomJs.onFav = function (event){
            var target = event.target;
            room_id = target.dataset.roomid;
            has_fav = target.dataset.hasfav;
            sub_fav = "N";
            if (has_fav == "N"){
                sub_fav = "Y";
            }
            formData = new FormData();
            formData.append('room_id', room_id);
            formData.append('is_favorites', sub_fav);
            fetch('/api/updatefav',{
                    method:"post",
                    body:formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.code == 0){
                        if (sub_fav == 'Y'){
                             target.src = "/static/images/btn_fav.png";
                             target.setAttribute("data-hasfav",sub_fav);
                        }
                        else{
                             target.src = "/static/images/btn_unfav.png";
                             target.setAttribute("data-hasfav",sub_fav);
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


roomJs.goSend = function (event){
    var target = event.target;
    room_id = target.dataset.roomid
    window.location.href = "/danmu/" + room_id
}