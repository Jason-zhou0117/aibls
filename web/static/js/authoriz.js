function ontargetkeypress(event){
    if (event.key === 'Enter' || event.keyCode === 13) {
        doaddauth()
    }
}

function doaddauth(){
    target_id = document.getElementById('target_id').value;
    if (target_id.trim() == ""){
        alert("请输入被授权的账号（手机号）");
        return
    }
    params = new URLSearchParams({
      target_id: target_id
    });
    fetch('/api/addauth?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                location.reload();
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

function delauth(event){
    target = event.target;
    auth_id = target.dataset.authid
    if (typeof auth_id === "undefined" ){
        alert("还未完全加载完毕，请稍等！");
        return
    }
    params = new URLSearchParams({
      auth_id: auth_id
    });
    fetch('/api/delauth?'+params.toString())
        .then(response => response.json())
        .then(data => {
             if (data.code == 0){
                location.reload();
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