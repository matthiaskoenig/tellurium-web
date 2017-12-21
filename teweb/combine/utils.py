def input_template(**kwargs):
    input_string = ""
    for key in kwargs:
        input_string+=" "+key+"='"+kwargs[key]+"' "

    return "<input"+input_string +"/>"

def html_creator(first_name, last_name, organisation, email):
    return '<dl><dt>{} {}</dt><dd>{}</dd><dd>{}</dd></dl>'.format(first_name, last_name, organisation,
                                                                  email)

