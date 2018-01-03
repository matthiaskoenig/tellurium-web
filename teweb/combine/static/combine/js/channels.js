
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
       if (data.task_status == "PENDING") {
           // update icon
           var content = '<i class="fas fa-fw fa-cog fa-spin"></i> PENDING';
           $("#task-status-"+archive_id).html(content);
       }
       // if action is completed, just update the status
       else if (data.task_status == "SUCCESS"){

           // update icon
           var content = '<i class="fas fa-fw fa-check"></i> SUCCESS';
           $("#task-status-"+archive_id).html(content);
       }
       else if (data.task_status == "FAILURE") {
           // update icon
           var content = '<i class="fas fa-fw fa-minus"></i> FAILURE';
           $("#task-status-" + archive_id).html(content);
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
       $("#task_name").val('').focus();

       // update icon
       var content = '<i class="fas fa-fw fa-cog fa-spin"></i> Executing Task';
       $("#task-status-"+archive_id).html(content);

       // update action icon
       var button = $(this).find("button");
       button.attr("class", "btn-xs btn-info");
       var icon = button.find("i");
       icon.attr("class", "fas fa-cog fa-spin fa-fw");

       return false;
   });


});
