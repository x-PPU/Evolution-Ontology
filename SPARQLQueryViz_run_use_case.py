# import
from sparql_query_viz import SQV

port = 8050
while True:
    try:
        SQV(iri="http://example.org/onto-example.owl",
            path="sparql_query_viz/datasets/ontologies/xPPU_onto.owl").plot(port=port)
    except:
        port += 1