
/**
 * Javascript for working with websockets and channels.
 */

$(function() {
   // When we're using HTTPS, use WSS too.
   var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
   var ws_path = ws_scheme + '://' + window.location.host + '/';
   console.log("Connecting to " + ws_path)
   var socket = new ReconnectingWebSocket(ws_path);
   socket.onmessage = function(message) {
       console.log("Got message: " + message.data);

       var data = JSON.parse(message.data);
       var archive_id = data.archive_id;
       var button = $("#action_"+archive_id);
       var status = $("#status_"+archive_id);

       if (data.task_status == "PENDING") {
           // action
           button.attr("class", "btn-xs btn-info");
           button.attr("title", "Executing archive");
           button.html('<i class="fas fa-cog fa-spin fa-fw">');
           // status
           status.html('<span class="label label-warning">PENDING</span>');
       }
       else if (data.task_status == "SUCCESS"){
           // action
           button.attr("class", "btn-xs btn-success");
           button.attr("title", "Rerun archive");
           button.html('<i class="fas fa-sync-alt fa-fw">');
           // status
           status.html('<span class="label label-success">SUCCESS</span>');
           // results icon
           var result_url = "./archive/" + archive_id + "/results";
           var content = '<a href="' + result_url +'"><button id="results_' + archive_id +'" class="btn-xs btn-default" title="Show results">\n' +
               '<i class="fas fa-chart-line fa-fw fa-lg"></i></button></a>';
           $("#results_"+archive_id).html(content);
       }
       else if (data.task_status == "FAILURE") {
           // action
           button.attr("class", "btn-xs btn-danger");
           button.attr("title", "Retry archive");
           button.html('<i class="fas fa-sync-alt fa-fw">');
           // status
           status.html('<span class="label label-danger">FAILURE</span>');
       }
       else {
           // status
           status.html('<span class="label label-warning">data.task_status</span>');
       }

   };

   /* Action after clicking the archive action. */
   $(".archive-action").on("click", function(event) {
       var archive_id = $(this).attr("archive");
       console.log("Archive id: " + archive_id);

       var message = {
           action: "run_archive",
           archive_id: archive_id
       };
       socket.send(JSON.stringify(message));

       // update action icon
       var button = $("#action_"+archive_id);
       button.attr("class", "btn-xs btn-info");
       button.attr("title", "Executing archive");
       button.html('<i class="fas fa-cog fa-spin fa-fw">');

       // update results icon
       $("#results_"+archive_id).html('');

       // update status
       $("#status_"+archive_id).html('');


       return false;
   });


});
