import rdflib
from rdflib import URIRef
from rdflib.util import guess_format


def test_to_turtle(path_in, path_out):
    """ Convert XML to turtle. """
    g = rdflib.Graph()
    format = guess_format(path_in)
    g.parse(path_in, format=format)
    g.bind(prefix="dcterms", namespace=URIRef("http://purl.org/dc/terms/"))

    # convert to turtle
    ttl = g.serialize(format='turtle').decode("utf-8")
    print(ttl)
    with open(path_out, "w") as f_ttl:
        f_ttl.write(ttl)


if __name__ == "__main__":
    path_in = "./internationalization_example.rdf"
    path_out = "./internationalization_example.ttl"
    test_to_turtle(path_in, path_out)