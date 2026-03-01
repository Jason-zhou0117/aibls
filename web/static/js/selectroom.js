
function onfilterkeypress(event){
    if (event.key === 'Enter' || event.keyCode === 13) {
        filterroom()
    }
}

function filterroom(){
    filtern = document.getElementById('filterinput').value;

    params = new URLSearchParams({
      filter: filtern
    });
    var divlist = document.getElementById('divrooms');
    divlist.innerHTML = ""
    fetch('/api/filtrooms?'+params.toString())
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
                    imgcover.src = room.cover;
                    div_row.appendChild(imgcover);

                    var divcontent = document.createElement("div");
                    divcontent.classList.add("roomcontents");
                    div_row.appendChild(divcontent);

                    var ptitle = document.createElement("p");
                    ptitle.classList.add("room_title");
                    ptitle.innerText = room.title;
                    divcontent.appendChild(ptitle);

                    var pupper = document.createElement("p");
                    pupper.classList.add("roomidp");
                    pupper.innerText = "房号：" + room.room_id;
                    divcontent.appendChild(pupper);

                    var pupper = document.createElement("p");
                    pupper.classList.add("upuserp");
                    pupper.innerText = "UP："+room.uname;
                    divcontent.appendChild(pupper);

                    var divbuttons = document.createElement("div");
                    divbuttons.classList.add("buttons");
                    div_row.appendChild(divbuttons);

                    var imgsend = document.createElement("img");
                    imgsend.src = "/static/images/btn_goto.png";
                    imgsend.classList.add("fav_button");
                    imgsend.setAttribute("data-roomid",room.room_id);
                    imgsend.setAttribute("onclick","javascript:gotaskset(event)");
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

function donewroom(){
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
                        var roomtitle = document.querySelector('.room_title')
                        roomtitle.innerText = data.roominfo.title

                        var roomcover = document.querySelector('.cover')
                        roomcover.src = data.roominfo.cover

                        var upuser = document.querySelector('.upuserp')
                        upuser.innerText = "UP：" + data.roominfo.uname

                        var roomidp = document.querySelector('.roomidp')
                        roomidp.innerText = "房号：" + data.roominfo.room_id;

                        var btnfav = document.querySelector('.fav_button')
                        btnfav.setAttribute("data-roomid",room_id)
                        btnfav.setAttribute("data-hasfav",data.hasfav)

                        var btnsend = document.querySelector('.send_button')
                        btnsend.setAttribute("data-roomid",room_id)

                        if (data.has_fav){
                            btnfav.src = "/static/images/btn_fav.png"
                        }
                        else{
                            btnfav.src = "/static/images/btn_unfav.png"
                        }

                        var roomdiv = document.querySelector('.roominfo')
                        roomdiv.style.visibility = 'visible';
                    }
                    else{
                        document.getElementById('msg_txt').innerText = data.text;

                        console.error('Error:', data.text) ;
                    }
                })
                .catch(error => console.error('Error:', error))
                .finally();
}

function gosend(event){
    var target = event.target;
    room_id = target.dataset.roomid
    window.location.href = "/sendgift/" + room_id
}