"""
Handle the term annotations.
"""
from pprint import pprint

from combine.metadata.webservices import json_providers_for_uri, json_term_for_uri

ICON_WARNING = "<span class=\"fa fa-exclamation-circle fa-lg\" title=\"true\" style=\"color:red\"> </span>"
ICON_TRUE = "<span class=\"fa fa-check-circle fa-lg\" title=\"true\" style=\"color:green\"> </span>"
ICON_FALSE = "<span class=\"fa fa-times-circle fa-lg\" title=\"false\" style=\"color:red\"> </span>"
ICON_NONE = "<span class=\"fa fa-circle-o fa-lg\" title=\"none\" style=\"color:grey\"> </span>"
ICON_INVISIBLE = "<span class=\"fa fa-circle-o fa-lg icon-invisible\" title=\"none\"> </span>"


class Annotation(object):

    def __init__(self, subject, qualifier, uri):
        self.subject = subject
        self.qualifier = qualifier
        self.uri = uri
        self.qualifier = qualifier
        self.parse_uri_info()

    def parse_uri_info(self):
        """ Retrieves JSON.

        :param uri:
        :return:
        """
        json = json_term_for_uri(self.uri)
        pprint(json)
        self.description = json.get("description", None)
        self.synonyms = json.get("synonyms", None)
        self.obo_synonyms = json.get("obo_synonym", None)
        self.iri = json.get("iri", None)
        self.label = json.get("label", None)
        self.obo_id = json.get("obo_id", None)
        self.ontology_name = json.get("ontology_name", None)
        self.providers = json_providers_for_uri(self.uri)

    def __str__(self):
        return self.uri

    @staticmethod
    def _url_from_provider(provider, obo_id):
        """ Creates tha actual url for given provider.
            'accessURL': 'http://www.ebi.ac.uk/ols/ontologies/chebi/terms?obo_id={$id}'

        :param provider:
        :param obo_id:
        :return:
        """
        url = provider["accessURL"]
        return url.replace("{$id}", obo_id)

    def html(self):

        html = '<p class="cvterm">\n'

        if "biology-qualifiers" in self.qualifier:
            qualifier_type = "BQB"
        elif "model-qualifiers" in self.qualifier:
            qualifier_type ="BQM"
        else:
            qualifier_type = ""

        qualifier_short = qualifier_type + "_" + self.qualifier.split("/")[-1]
        qualifier_html = '<a href="{}" target="_blank"><span class="qualifier" title="{}">{}</span></a>\n'.format("http://co.mbine.org/standards/qualifiers", self.qualifier, qualifier_short.upper())

        # find official provider
        official_provider = None
        ols_provider = None
        for provider in self.providers:
            if not official_provider:
                official_provider = provider
            if provider["official"] == True:
                official_provider = provider
            if provider["resourcePrefix"] == "ols":
                ols_provider = provider

        official_url = Annotation._url_from_provider(official_provider, self.obo_id)
        official_info = official_provider["info"]
        collection_url = 'http://identifiers.org/' + self.ontology_name

        collection_html = '<a href="{}" target="_blank"><span class="collection" title="MIRIAM data collection. Click to open on MIRIAM registry.">{}</span></a>\n'.format(collection_url, official_info)
        identifier_html = '<a href="{}" target="_blank"><span class="identifier" title="Resource identifier. Click to open primary resource.">{}</span></a><br />\n'.format(official_url, self.obo_id)
        html += qualifier_html + collection_html + identifier_html

        # ontology information
        if ols_provider:
            html += '<a href="{}" target="_blank"><span class="ontology" title="Ontology">OLS</span></a> <b>{}</b> <a href="{}" target="_blank" class="text-muted">{}</a><br />\n'.format(
                Annotation._url_from_provider(ols_provider, self.obo_id),
                self.label,
                self.iri,
                self.iri
            )
        else:
            html += "<b>{}</b><br />".format(self.label)

        # description
        if self.description:
            for item in self.description:
                html += '<span class="text-success">{}</span><br />\n'.format(item)

        # synonyms
        if self.synonyms and len(self.synonyms)>0:
            html += '<span class="comment">Synonyms</span> '
            for synonym in self.synonyms:
                html += synonym + "; "
            html += "<br />\n"
        if self.obo_synonyms and len(self.obo_synonyms)>0:
            html += '<span class="comment">OBO Synonyms</span> '
            for synonym in self.obo_synonyms:
                html += synonym.get("name") + "; "
            html += "<br />\n"

        # resources
        pprint(self.providers)
        for provider in self.providers:
            url = Annotation._url_from_provider(provider, self.obo_id)

            info = provider["info"]
            official = provider["official"]
            if official:
                icon = ICON_TRUE
            else:
                icon = ICON_INVISIBLE

            html += '\t{} <a href="{}" target="_blank"> {}</a><br />\n'.format(icon, url, info)

        html += '</p>'

        return html




if __name__ == "__main__":
    subject = "./BIOMD0000000176.xml#_525523"
    qualifier = "http://biomodels.net/biology-qualifiers/is"
    uri = "http://identifiers.org/chebi/CHEBI:4167"
    a = Annotation(subject=subject, qualifier=qualifier, uri=uri)
    print(a)

    with open("test.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" type="text/css" href="../static/combine/css/combine.css"/>
    <link rel="stylesheet" href="../static/combine/css/bootstrap.min.css">
    <link rel="stylesheet" type="text/css" href="../static/combine/js/datatables.min.css"/>
    <link rel="stylesheet" type="text/css" href="../static/combine/font-awesome-4.7.0/css/font-awesome.min.css"/>
</head>
<body>
{}
</body>
</html> 
        """.format(a.html()))
