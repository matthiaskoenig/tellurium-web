
/**
 * Javascript for working with websockets and channels.
 */

$(function() {
   // When we're using HTTPS, use WSS too.
   var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
   var ws_path = ws_scheme + '://' + window.location.host + '/dashboard/';
   console.log("Connecting to " + ws_path)
   var socket = new ReconnectingWebSocket(ws_path);
   socket.onmessage = function(message) {
       console.log("Got message: " + message.data);
       var data = JSON.parse(message.data);
       // if action is started, add new item to table

       var archive_id = data.archive_id;
       var button = $("#action_"+archive_id);

       if (data.task_status == "PENDING") {
           // update icon
           var content = '<i class="fas fa-fw fa-cog fa-spin"></i> PENDING';
           $("#task-status-"+archive_id).html(content);
           button.attr("class", "btn-xs btn-info");
           button.attr("title", "Executing archive");
           button.html('<i class="fas fa-cog fa-spin fa-fw">');
       }
       // if action is completed, just update the status
       else if (data.task_status == "SUCCESS"){

           // update icon
           var content = '<i class="fas fa-fw fa-check"></i> SUCCESS';
           $("#task-status-"+archive_id).html(content);
           button.attr("class", "btn-xs btn-success");
           button.attr("title", "Rerun archive");
           button.html('<i class="fas fa-sync-alt fa-fw">');
       }
       else if (data.task_status == "FAILURE") {
           // update icon
           var content = '<i class="fas fa-fw fa-minus"></i> FAILURE';
           $("#task-status-" + archive_id).html(content);
           button.attr("class", "btn-xs btn-danger");
           button.attr("title", "Retry archive");
           button.html('<i class="fas fa-sync-alt fa-fw">');
       };

   };

   /*
    * Action after clicking the archive action.
    */
   $(".archive-action").on("click", function(event) {
       var archive_id = $(this).attr("archive");
       console.log("Archive id: " + archive_id)

       var message = {
           action: "run_archive",
           archive_id: archive_id
       };
       socket.send(JSON.stringify(message));

       // update message
       // var content = '<i class="fas fa-fw fa-cog fa-spin"></i> Executing Task';
       // $("#task-status-"+archive_id).html(content);

       // update action icon
       var button = $("#action_"+archive_id);
       button.attr("class", "btn-xs btn-info");
       button.attr("title", "Executing archive");

       button.html('<i class="fas fa-cog fa-spin fa-fw">');

       return false;
   });


});
