#!/usr/bin/env python3
"""check consistency of T5-ontology"""

from owlready2 import *
import json
import rdflib
import timeit


def load_query(query) -> str:
    f = open(query, "r")
    return f.read()


def query_onto(onto, query) -> list:
    with onto:
        graph = default_world.as_rdflib_graph()
        return list(graph.query(query))


def query_w_rdflib(onto, query) -> list:
    g = rdflib.Graph()
    g.parse(onto)
    return list(g.query(query))

def resultsToDict(queryresult) -> dict:
    dic={}
    k=0
    for item in queryresult:
        string=""
        for element in item:
            if "#" in element:
                i = element.split("#")[1]
            else:
                i = element
            if len(string):
                string=string+"<br>"+i
            else:
                string = string + i
        dic["result" + " " + str(k)] = string
        k+=1
    return dic

def query(path, filename=None,engine="owlready", showall: bool=True) -> None:
    """ run several queries to check for consistencies

    :param path: path to onto file
    :param filename: onto filename - for loading onto with rdflib
    :param showall: show info that query was run, even if no results are returned, i.e., no inconsistency was found
    """
    engines = ["owlready", "rdflib"]
    qlog = []
    assert engine in engines, f"invalid engine, must be in {engines}"

#    model_iri_list = list(model_data.keys())

    queries = [
        (1,"query/scenario_query.sparql", "+++++++++++++"),
        (2, "query/scenario_info_query.sparql", "+++++++++++++++++++")
    ]
    if engine == "owlready":
        onto = get_ontology(path).load()
        with onto:
            for query in queries:
                query_results = query_onto(onto, load_query(query[1]))          #load the 2 element in the query_list, and do the quary in onto
                print_if_available(query[2], query_results, showall)            #print the 3 element in the query_list, if theres result or showall

    elif engine == "rdflib":
        for query in queries:
            query_results = query_w_rdflib(filename, load_query(query[1]))
            print_if_available(query[2], query_results, showall)



def print_if_available(msg: str, input: list, showall: bool) -> None:
    if showall or input:
        print(msg)
        if input:
            print(*input, sep="\n")
        else:
            print("no inconsistencies found")



if __name__ == "__main__":
    iri = "http://example.org/min-onto-example.owl"
    onto_path = "outputs/onto.owl"
    onto_filename = "outputs/onto.owl"
    query(onto_path, onto_filename, "owlready")


