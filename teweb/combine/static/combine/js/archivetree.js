/**
 * Javascript for working with the archive navigation tree.
 */


/**
 * Load zip tree
 */

var endpoint = './zip_tree';
$.ajax({
    method: "GET",
    url: endpoint,
    success: function (data) {
        $('#json_tree').jstree({
            'core': {
                'multiple': false,
                'data': data
            },
            'plugins':['types']
        });
    },
    error: function (error_data) {
        console.log("error");
        console.log(error_data);
    }
})


/**
 * Load detail of selected entry.
 */

     $('#json_tree')
  // listen for event in json tree
  .on('select_node.jstree', function (e, data) {
      // get selected node
      var selected, entry_pk;
      selected = $('#json_tree').jstree(true).get_selected(true);
      entry_pk = selected[0].original.pk;
      display_entry_detail(entry_pk, false);
    });


    /**
      * Trigger on_select for selected node when tree loads
      */
    $("#json_tree").on("ready.jstree", function(e, data) {
      var tree = data.instance;
      var obj = tree.get_selected(true)[0];

      // trigger the on_select handler for the tree node that is currently selected
        // and ensure that it is opened
      if (obj) {
        if (obj.state.opened) {
          tree.trigger('select_node',
              {
                  'node': obj,
                  'selected': tree._data.core.selected,
                  'event' : e
              });
        } else {
          tree.open_node(obj, function() {
            tree.trigger('select_node',
                {
                    'node': obj,
                    'selected': tree._data.core.selected,
                    'event': e
                });
          });
        }
      }
    });

    $(document).on('click','#editButton',function(){
        var selected = $('#json_tree').jstree(true).get_selected(true);
        var entry_pk = selected[0].original.pk;
        display_entry_detail(entry_pk, true);
    });

    $(document).on('click','#addCreator',function(){
        var contact_content = add_empty_contact();
        $("#creators_div").append(contact_content);
    });

    $(document).on('click','#delete',function(){
         var creatorId = this.parentNode.parentNode.parentNode.id;
         delete_contact(creatorId,this.parentNode.parentNode.parentNode.parentNode);
         this.parentNode.parentNode.parentNode = this.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode)
    });
    $(document).on('click','#saveButton',function(){
        var frm = $('#form_detail');
        frm.submit(submit_form());
    });

    $(document).on('click','#cancelButton',function(){
       var selected = $('#json_tree').jstree(true).get_selected(true);
        var entry_pk = selected[0].original.pk;
        display_entry_detail(entry_pk, false);
    });

    function display_entry_detail(entry_pk, edit){

        /** Main function for displaying archive entry detail after selection. */
        var endpoint_path = "/api/archive-entries/" + entry_pk + "/";
        var endpoint = window.location.origin + endpoint_path;

        var manifest_detail_div = document.getElementById("manifest_detail");
        var button_div = document.getElementById("button-div");
        var entry_detail_div = document.getElementById("item_detail");
        var button_div_meta = document.getElementById("button-meta-div");
        var div_tripples = document.getElementById("tripples_detail");

        // empty content
        manifest_detail_div.innerHTML = "";
        button_div.innerHTML = "";
        entry_detail_div.innerHTML = "";
        button_div_meta.innerHTML = "";
        div_tripples.innerHTML = "";

        $.ajax({
            url: endpoint,
            type:'Get',
            success: function (data) {

                if ('{{request.user.is_superuser}}'=='True' && data.file){
                    var archive_entry_button = document.createElement("input");
                    archive_entry_button.setAttribute("type","button");
                    archive_entry_button.setAttribute("value","Archive Entry");
                    archive_entry_button.setAttribute("class","btn btn-default entry_buttons");
                    archive_entry_button.addEventListener("click",function () {window.open('/entry/'+entry_pk);}, false);
                    button_div.appendChild(archive_entry_button);

                    var archive_entry_api_button = document.createElement("input");
                    archive_entry_api_button.setAttribute("type","button");
                    archive_entry_api_button.setAttribute("value","Archive Entry API");
                    archive_entry_api_button.setAttribute("class","btn btn-default entry_buttons");
                    archive_entry_api_button.addEventListener("click",function () {window.open('/api/archive-entries/'+entry_pk);}, false);
                    button_div.appendChild(archive_entry_api_button);
                }

                var metadata = data.metadata;

                button_div.appendChild(create_buttons_div(edit));
                manifest_detail_div.appendChild(create_entry_title(data));
                manifest_detail_div.appendChild(create_manfifest_detail(entry_pk, data, edit));

                if(metadata !== 'undefined'){
                    if (edit){
                        button_div_meta.innerHTML = '<button class="btn btn-default entry_buttons" type="button" id="addCreator"><i class="fa fa-fw fa-users"></i> Add Creator </button>';
                    }
                    entry_detail_div.append(create_meta(metadata, edit));
                    for (var triple in metadata.triples){
                     if(metadata.triples.hasOwnProperty(triple)){
                         var triple_div = addTriple(metadata.triples,triple,edit);
                         div_tripples.appendChild(triple_div);
                         }
                     }
                }
            },
            error: function (error_data) {
                // errors if anything goes wrong
                console.log("error");
                console.log(error_data);
            }
        })
    }

    function submit_form(){
        document.getElementById("form_detail").appendChild(create_master_input());
        var frm = $('#form_detail');
        $.ajax({
            type: frm.attr('method'),
            url: frm.attr('action'),
            data: {"data": frm.serializeJSON({useIntKeysAsArrayIndex:false})},
            success: function (data) {

                // if data is not valid
                if(data.is_error){
                    for (var error in data.errors){
                        $("#item_detail").prepend("<div class='alert alert-danger' data-alert>"+error+":"+data.errors[error]+"</div>")
                    }
                }
                // if data valid
                else{
                console.log("success"); // another sanity check
                var selected = $('#json_tree').jstree(true).get_selected(true);
                var entry_pk = selected[0].original.pk;
                display_entry_detail(entry_pk,false)}

            },
            error: function(data) {
                console.log(data.status + ": " + data.responseText);
            }
        });
        return false;
    }
