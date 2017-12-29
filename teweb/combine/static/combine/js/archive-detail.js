
function create_entry_title(data){
    "use strict";
    var title_entry = document.createElement("h3");
    var format_list = ['cellml', 'sed-ml', 'sbml', 'numl', 'csv', 'sbgn', 'omex', 'omex-manifest', 'omex-metadata'];
    var title_text = document.createTextNode(get_title(data.location));
    title_entry.appendChild(title_text);

    if (typeof base_format(data.format) !== 'undefined'){
        title_entry.insertBefore(get_format_icon(data.format),title_entry.childNodes[0]);
    }

    if (data.master){
        title_entry.appendChild(get_master_icon(data.master));
    }

    return title_entry;
}


function get_master_icon(master){
    "use strict";
    var master_icon = document.createElement("i");
    master_icon.setAttribute("class", "fa fa-star fa-fw");
    master_icon.setAttribute("title", "master");
    return master_icon;
}


function get_title(location){
    "use strict";
    var splited_fn = location.split("/");
    return " " + splited_fn[splited_fn.length-1];
}

function get_format_icon(format){
    "use strict";
    var src=url_mediatype + base_format(format)+".png";
    var format_icon = document.createElement("img");
    format_icon.setAttribute("src", src);
    format_icon.setAttribute("height","20");
    format_icon.setAttribute("title",format);
    return format_icon;


}
function base_format(format){
    "use strict";
    var tokens = format.split('/').pop();
    var short = tokens.split('.')[0];
 return short.replace("+xml",'');
}





function modified_content( modified){
    "use strict";
    var content="";
    var i;
    for (i in  modified) {
        if(modified.hasOwnProperty(i)){
            content+='<dd>' + modified[i].date + '</dd>';
        }
    }
    return content;
}

function add_empty_contact(){
    "use strict";
    var contact_div = document.createElement("div");
    contact_div.setAttribute("id", "new");
    contact_div.innerHTML = "<div>"+empty_creator+"</div>";
    return contact_div


}

function add_empty_creator(){
    "use strict";
     var empty_creators= [{
                    "email": "",
                    "first_name": "",
                    "id": "new",
                    "last_name": "",
                    "organisation": ""
                }];
     return addContact(empty_creators,0,true);
}



function addContact(creators,creator,edit){
    "use strict";
    var contact_div , familyName,givenName,email,organisation, id, delete_creator, delete_button, id_creator;
    contact_div = document.createElement("div");
    id_creator =  creators[creator].id;
    contact_div.setAttribute("id", id_creator);

    if (edit===true){
        var idInput;
        idInput = document.createElement("input");
        idInput.setAttribute("value",id_creator);
        idInput.setAttribute("type", "hidden");
        idInput.setAttribute("name", "creators[][id]");
        idInput.setAttribute("class", "Id");

        id = idInput.outerHTML;

        var deleteInput;
        deleteInput = document.createElement("input");
        deleteInput.setAttribute("value","false");
        deleteInput.setAttribute("type", "hidden");
        deleteInput.setAttribute("name", "creators[][delete]");

        delete_creator =  deleteInput.outerHTML;



        var deleteButton = document.createElement("input");
        deleteButton.setAttribute("class" , "btn btn-default btn-space");
        deleteButton.setAttribute("value","delete");
        deleteButton.setAttribute("id","delete");
        deleteButton.setAttribute("type","button");


        delete_button = deleteButton.outerHTML;

        contact_div.innerHTML =delete_button+id+creators[creator].html_edit+delete_creator;

    }
    else {
            contact_div.innerHTML = creators[creator].html;
    }
    return contact_div;
}


function create_delete_contact(creator_id){
    "use strict";
    var deleteInput = document.createElement("input");
    deleteInput.setAttribute("value",creator_id);
    deleteInput.setAttribute("type", "hidden");
    deleteInput.setAttribute("name", "creators[][delete]");
    return deleteInput;
}

function delete_contact(creator_id, contact_div){
    "use strict";
    //contact_div.parentNode.innerHTML += "<input value='" + creator_id + "' type='hidden' name='creators[][delete]'/>";
    contact_div.parentNode.appendChild(create_delete_contact(creator_id));

}

function create_buttons_div(edit){
    /** Button HTML */
    "use strict";
    var buttons_div = document.createElement("div");
    if ( edit ){
         buttons_div.innerHTML += '<span class="btn btn-default btn-space" id="saveButton"><i class="far fa-save"></i> Save </span>';
         buttons_div.innerHTML += '<span class="btn btn-default btn-space" id="cancelButton"><i class="fas fa-ban"></i> Cancel </span>';
    }
    else {
        buttons_div.innerHTML += '<span class="btn btn-default btn-space" id="editButton"> <i class="fas fa-edit fa-fw"></i> edit </span>';
    }

    return buttons_div;
}


function add_master_checkbox(master,edit){
    "use strict";
    var checkbox_div = document.createElement("div");
    var checkbox_label = document.createElement("label");
    var checkbox = document.createElement("input");
    checkbox_label.innerHTML = "Master ";
    checkbox.type = "checkbox";
    checkbox.id = "checkbox1";
    //checkbox.setAttribute("data-toggle", "toggle");
    checkbox.defaultChecked = master;
    checkbox.checked = master;
    checkbox.disabled = !edit;
    console.log(checkbox);
    checkbox_div.appendChild(checkbox_label);
    checkbox_div.innerHTML += " ";
    checkbox_div.appendChild(checkbox);
    return checkbox_div;
}

function add_location(location){
    "use strict";
    var dl = document.createElement("dl");
    var dt = document.createElement("dt");
    var dd = document.createElement("dd");
    dt.innerHTML = "Location";
    dd.innerHTML = location;
    dl.appendChild(dt);
    dl.appendChild(dd);
    return dl;
}

function create_manfifest_detail(entry_pk,data,edit){
    "use strict";
    var detailManifest = document.createElement("div");
    detailManifest.innerHTML += "<div><label> Format </label> <code title='"+data.format +"'>" + base_format(data.format) +" </code></div>"
    detailManifest.appendChild(add_master_checkbox(data.master,edit));
    if (data.file !== null && typeof data.file !== 'undefined'){
        detailManifest.innerHTML += "<div><label> Location </label>"+ " "+"<a  target='_blank' href='"+data.file+"'>"+ data.location + "</a></div>";
    }
    else{
         detailManifest.innerHTML += "<div><label> Location </label>"+ " "+ data.location + "</div>";
    }

    //detailManifest.appendChild(add_location(data.location));

    detailManifest.appendChild(hidden_input_entry_pk(entry_pk));
    return detailManifest;
}

function hidden_input_entry_pk(entry_pk){
    "use strict";
    var entryIdInput=document.createElement("input");
    entryIdInput.setAttribute("value",entry_pk);
    entryIdInput.setAttribute("type", "hidden");
    entryIdInput.setAttribute("name", "id");
    return entryIdInput;
}

function create_master_input(){
    "use strict";
    var master_output = document.createElement("input");
    master_output.setAttribute("value",document.getElementById('checkbox1').checked);
    master_output.setAttribute("name","master");
    master_output.setAttribute("type","hidden");
    master_output.setAttribute("id", "master_output");
    return master_output;
}


function create_meta(metadata, edit){
    "use strict";
    var meta_div = document.createElement("div");
    var creators_div = document.createElement("div");
    creators_div.setAttribute("id","creators_div");
    var creator_button;
    if (edit ){creator_button = '<span class="btn btn-default btn-space" id="addCreator"><i class="fa fa-fw fa-users"></i> Add Creator </span>';}
    else {creator_button = '';}
    creators_div.innerHTML += '<h3> Creators '+creator_button+'</h3>';

    var dl_desc = document.createElement("dl");
    var dt_desc = document.createElement("dt");
    var dd_desc = document.createElement("dd");

    var dl_created = document.createElement("dl");
    var dt_created = document.createElement("dt");
    var dd_created = document.createElement("dd");

    var dl_modified = document.createElement("dl");
    var dt_modified = document.createElement("dt");
    var dd_modified = document.createElement("dd");

    dt_desc.appendChild(document.createTextNode("Description"));
    dt_created.appendChild(document.createTextNode("Created"));
    dt_modified.appendChild(document.createTextNode("Modified"));

    dd_created.appendChild(document.createTextNode(metadata.created));
    dd_modified.innerHTML = modified_content(metadata.modified);

    if (edit===true) {

        var textArea = document.createElement("textarea");
        textArea.cols = "50";
        textArea.rows = "5";
        textArea.setAttribute("name", "description");
        textArea.append(metadata.description);
        dd_desc.appendChild(textArea);
    }
    else{
        dd_desc.appendChild(document.createTextNode(metadata.description));
    }

    dl_desc.appendChild(dt_desc);
    dl_desc.appendChild(dd_desc);




    dl_created.appendChild(dt_created);
    dl_created.appendChild(dd_created);

    dl_modified.appendChild(dt_modified);
    dl_modified.appendChild(dd_modified);

    meta_div.appendChild(dl_desc);

     for (var creator in metadata.creators){
         if(metadata.creators.hasOwnProperty(creator)){
        var contact_div = addContact(metadata.creators,creator,edit);
        creators_div.appendChild(contact_div);
    }}

    meta_div.appendChild(creators_div);
    meta_div.innerHTML += "<br>";

    meta_div.appendChild(dl_created);
    meta_div.appendChild(dl_modified);


    for (var triple in metadata.triples){
         if(metadata.triples.hasOwnProperty(triple)){
             var triple_div = addTriple(metadata.triples,triple,edit);
        meta_div.appendChild(triple_div);
    }}

    return meta_div;

}

function addTriple(triples,triple,edit){
 "use strict";
    var triple_div;
    triple_div = document.createElement("div");
    triple_div.innerHTML = triples[triple].html;
    return triple_div;
}

