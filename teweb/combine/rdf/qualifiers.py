"""
Definition of the available BioModels qualifiers.
These are used in the triples.

http://co.mbine.org/standards/qualifiers
"""

MODEL_QUALIFIER_PREFIX = "http://biomodels.net/model-qualifiers/"
BIOLOGICAL_QUALIFIER_PREFIX = "http://biomodels.net/biological-qualifiers/"

# TODO: fill up the information from http://co.mbine.org/standards/qualifiers
ModelQualifierType = {
    "is": [0, "identity", "The modelling object represented by the model element is identical with the subject of the referenced resource (modelling object B). For instance, this qualifier might be used to link an encoded model to a database of models."],
    "isDescribedBy": 1,
    "isDerivedFrom": 2,
    "isInstanceOf": 3,
    "hasInstance": 4,
}

BiologicalQualifierType = {
    "is": 0,
    "hasPart": 1,
    "isPartOf": 2,
    "isVersionOf": 3,
    "hasVersion": 4,
    "isHomologTo": 5,
    "isDescribedBy": 6,
    "isEncodedBy": 7,
    "encodes": 8,
    "occursIn": 9,
    "hasProperty": 10,
    "isPropertyOf": 11,
    "hasTaxon": 12,
}