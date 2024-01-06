
function checkrun() {
    /** tracker for running processes **/
    let id = setInterval(() => {
        resPromise = ajax('checkrun', data_send='', raise_alert=false);
        
        resPromise.then(function (data_json) {
            $('#elem4').empty();
            for (let line of data_json.status) {
                $('#elem4').append(line+'<br>');
            }  
            if (! data_json.is_running){
                clearInterval(id);
            }
        });
        
    }, 1000);
}
function run_tough3() {
    
    let inifp = $('[name="ini_outfp_full"]').val();
    resPromise = ajax('run_tough3', data_send=inifp, raise_alert=false);
    
    resPromise.then(function (data_json) {
        $('#elem1').empty();
        $('#elem1').append(data_json.status_msg);
        $('#elem2').empty();
        $('#elem2').append(data_json.error_msg);
        $('#elem3').empty();
        $('#elem3').append(data_json.running_processes);

        if (data_json.flg_started) {
            // activate tracker for running processes
            checkrun();
        }
    });
}
function ajax(to, data_send='', raise_alert=true) {
    //deferredを使う
    var d = new $.Deferred;
    $.ajax({
        type: 'GET',
        url: 'http://localhost:8000/'+to,
        data: {key1: data_send},
        datatype: 'json',
        crossDomain:true,
        success: function (returned_data) {
            //json文字列をJSONオブジェクトに変換して配列に格納する
            var data_stringify = JSON.stringify(returned_data);
            if (raise_alert){
                alert("received from http://localhost:8000/"+to+": "+data_stringify);
            }
            var data_json = JSON.parse(data_stringify);
            //完了
            d.resolve(data_json);
        }
    });
    return d.promise();
}