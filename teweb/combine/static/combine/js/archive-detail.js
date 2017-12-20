/**
 * Created by janekg89 on 19/12/17.
 */

function create_entry_title(data){
    "use strict";
    var title_entry = document.createElement("h3");
    var format_list = ['cellml', 'sed-ml', 'sbml', 'numl', 'csv', 'sbgn', 'omex', 'omex-manifest', 'omex-metadata'];
    var title_text = document.createTextNode(get_title(data.location));
    title_entry.appendChild(title_text);


    if (typeof base_format(data.format) !== 'undefined' && format_list.indexOf(base_format(data.format))>=0){
            title_entry.insertBefore(get_format_icon(data),title_entry.childNodes[0]);

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

function get_format_icon(data){
    "use strict";
    var src=url_mediatype+base_format(data.format)+".png";
    var format_icon = document.createElement("img");
    format_icon.setAttribute("src", src);
    format_icon.setAttribute("height","20");
    format_icon.setAttribute("title",data.format);
    return format_icon;
}

function get_format_code(data){
    "use strict";
    var format_div = document.createElement("div");
    var format_code = document.createElement("code");
    var format_label = document.createElement("label");
    format_code.setAttribute("title",data.format);
    format_label.innerHTML = "Format";
    format_code.innerHTML = base_format(data.format);
    format_div.appendChild(format_label);
    format_div.appendChild(format_code);

    return format_div;
}
function base_format(format){
    "use strict";
    var tokens = format.split('/').pop();
    var short = tokens.split('.')[0];
 return short.replace("+xml",'');
}

function add_master_checkbox(master,edit){
    "use strict";
    var checkbox_div = document.createElement("div");
    var checkbox_label = document.createElement("label");
    var checkbox = document.createElement("INPUT");
    checkbox_label.innerHTML = "Master";
    checkbox.type = "checkbox";
    checkbox.id = "checkbox1";
    checkbox.setAttribute("data-toggle", "toggle");
    checkbox.checked= master;
    checkbox.disabled = !edit;
    checkbox_div.appendChild(checkbox_label);
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
    var contact_div , familyName,givenName,email,organisation, id, delete_button;
    contact_div = document.createElement("div");
    contact_div.setAttribute("id", creator);

    if (edit===true){
        var idInput;
        idInput = document.createElement("input");
        idInput.setAttribute("value",creators[creator].id);
        idInput.setAttribute("type", "hidden");
        idInput.setAttribute("name", "creators["+creator+"][id]");
        idInput.setAttribute("class", "creatorId");

        id = idInput.outerHTML;

        var givenNameInput = document.createElement("input");
        givenNameInput.setAttribute("value",creators[creator].first_name);
        givenNameInput.setAttribute("placeholder", "First Name");
        givenNameInput.setAttribute("name", "creators["+creator+"][first_name]");


        givenName = givenNameInput.outerHTML;

        var familyNameInput = document.createElement("input");
        familyNameInput.setAttribute("value",creators[creator].last_name);
        familyNameInput.setAttribute("placeholder","Family Name");
        familyNameInput.setAttribute("name", "creators["+creator+"][last_name]");
        familyName = familyNameInput.outerHTML;

        var organisationInput = document.createElement("input");
        organisationInput.setAttribute("value",creators[creator].organisation);
        organisationInput.setAttribute("placeholder","Organisation");
        organisationInput.setAttribute("name", "creators["+creator+"][organisation]");
        organisation = organisationInput.outerHTML;

        var emailInput = document.createElement("input");
        emailInput.setAttribute("value",creators[creator].email);
        emailInput.setAttribute("placeholder","Email");
        emailInput.setAttribute("name", "creators["+creator+"][email]");
        email = emailInput.outerHTML;

        var deleteButton = document.createElement("input");
        deleteButton.setAttribute("class" , "btn btn-default btn-space");
        deleteButton.setAttribute("value","delete");
        deleteButton.setAttribute("id","deleteCreator");
        deleteButton.setAttribute("type","button");


        delete_button = deleteButton.outerHTML;


    }
    else {
        givenName = creators[creator].first_name;
        familyName = creators[creator].last_name;
        organisation = creators[creator].organisation;
        email = creators[creator].email;
        id = "";
        delete_button= "";
    }

    contact_div.innerHTML =delete_button+'<dl><dt>'+givenName+' '+familyName+'</dt><dd>'+organisation+"</dd><dd>"+email+"</dd></dl>"+id;

    return contact_div;
}

function create_delete_contact(creator, creator_id){
    "use strict";
    var deleteInput = document.createElement("input");
    deleteInput.setAttribute("value",creator_id);
    deleteInput.setAttribute("type", "hidden");
    deleteInput.setAttribute("name", "creators["+creator+"][delete]");
    return deleteInput;
}

function delete_contact(creator, creator_id, contact_div){
    "use strict";
    contact_div.parentNode.appendChild(create_delete_contact(creator,creator_id));

}

function create_edit_button(){
    "use strict";
    var myButton = document.createElement("span");
    var icon = document.createElement("i");
    myButton.className="btn btn-default btn-space";
    myButton.setAttribute("id","editButton");
    icon.className="fa fa-pencil fa-fw";
    icon.title="create new rdf entry";
    myButton.appendChild(icon);
    myButton.append("edit");
    return myButton;
}

function create_creator_button(){
    "use strict";
    var creatorButton = document.createElement("input");
    creatorButton.setAttribute("class","btn btn-default");
    creatorButton.setAttribute("id","addCreator");
    creatorButton.setAttribute("type","button");
    creatorButton.setAttribute("value","add Creator");
    return creatorButton;
}

function create_save_button(){
    "use strict";
    var saveButton = document.createElement("input");
    saveButton.setAttribute("class","btn btn-default");
    saveButton.setAttribute("id","saveButton");
    saveButton.setAttribute("type","submit");
    saveButton.setAttribute("value","save");
    return saveButton;
}


function create_buttons_div(edit){
    "use strict";
    var buttons_div = document.createElement("div");
    buttons_div.appendChild(create_edit_button());
    if ( edit ){
        buttons_div.appendChild(create_creator_button());
        buttons_div.appendChild(create_save_button());
    }
    return buttons_div;
}


function create_manfifest_detail(entry_pk,data,edit){
    "use strict";
    var detailManifest = document.createElement("div");
    detailManifest.appendChild(get_format_code(data));
    detailManifest.appendChild(add_master_checkbox(data.master,edit));
    detailManifest.appendChild(add_location(data.location));
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
    meta_div.appendChild(dl_created);
    meta_div.appendChild(dl_modified);

    for (var creator in metadata.creators){
         if(metadata.creators.hasOwnProperty(creator)){
        var contact_div = addContact(metadata.creators,creator,edit);
        meta_div.appendChild(contact_div);
    }}

    return meta_div;

}

