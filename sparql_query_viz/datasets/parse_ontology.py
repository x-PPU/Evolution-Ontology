"""
Author: Mohit Mayank

Load and return the Game of Thrones dataset

Data details:
1. 
"""

# imports
import logging
import os
import ontor as ontor
import pandas as pd
from ontor import OntoEditor


def get_tboxes(onto: OntoEditor, nodelist: list = None):
    """ extract T-Boxes from ontology and return them in a list

    :param onto: ontology from which classes are extracted
     :type onto: OntoEditor
     :param nodelist: list of all classes/ instances that were already extracted from the ontology
     :type nodelist: list
     :return: returns list of T-Boxes
     :rtype: list
    """

    # Generator of all classes in the ontology is created
    if nodelist is None:
        nodelist = []
    node_gen = onto.onto.classes()
    # All classes from the generator are written into a list with their name, importance, shape and T-Box label
    for cl in node_gen:
        nodelist.append([cl.name, 1, 'dot', 'T', ""])
    # return list of all extracted classes
    logging.info("successfully parsed T-Boxes from ontology specified")
    return nodelist


def get_isa_relations(onto: OntoEditor, edgelist: list = None):
    """ extracts all 'is_a'-relations from ontology and returns them in a list

    :param onto: ontology from which relations are extracted
     :type onto:OntoEditor
     :param edgelist: list of all relations that were already extracted from the ontology
     :type edgelist: list
     :return: return list of relations extracted until this point
     :rtype: list
    """

    # Generator of all classes in the ontology is created
    if edgelist is None:
        edgelist = []
    node_gen = onto.onto.classes()
    # For all classes from the generator the associated subclasses are written into a list
    for cl in node_gen:
        rellist = list(cl.subclasses())
        # All subclasses are written into a list with their name, associated superclasses' name,
        # id, weight, label and dashed-boolean
        for i, value in enumerate(rellist):
            identifier = rellist[i].name + ' is_a ' + cl.name
            edgelist.append([rellist[i].name, cl.name, identifier, 1, 'is_a', False])
    # return list of all extracted edges/ relations
    logging.info("successfully parsed IS_A-relations from ontology specified")
    return edgelist


def get_OPs(onto: OntoEditor, edgelist: list = None):
    """ extracts all object-properties from ontology and returns them in a list that is passed to the function

    :param onto: ontology from which relations are extracted
     :type onto: OntoEditor
     :param edgelist: list of all relations that were already extracted from the ontology
     :type edgelist: list
     :return: return list of relations extracted until this point
     :rtype: list
    """

    skipped_ops = 0
    extracted_ops = 0
    # Generator of all object-properties in the ontology is created
    if edgelist is None:
        edgelist = []
    op_gen = onto.onto.object_properties()
    # Iteration over all object-properties from the generator
    for op in op_gen:
        # All range-elements (targets) are written into a list, with their
        # domain's name, name, identifier, weight, associated object-property's name and dashes-boolean
        for i, value in enumerate(op.range):
            # if i != 0:
            domain = op.domain
            if not domain:
                # TODO: Find a suitable way to display ops if the domain is empty
                logging.warning("the op %s was skipped because there was no domain defined", op.name)
                skipped_ops = skipped_ops + 1
                # node_gen = onto.onto.classes()
                # for cl in node_gen:
                #    edge_already_exists = False
                #    identifier = cl.name + ' ' + op.name + ' ' + op.range[i].name
                #    for edge in edgelist:
                #        if cl != value and (cl.name == edge[0] and op.range[i].name == edge[1]):
                #            edge_already_exists = True
                #            edge[2] = edge[2] + ',\n ' + identifier
                #            edge[4] = edge[4] + ',\n ' + op.name
                #            edge[3] = edge[3] + 1
                #    if not edge_already_exists and cl != value:
                #        edgelist.append([cl.name, op.range[i].name, identifier, 1, op.name, True])
            else:
                identifier = op.domain[0].name + ' ' + op.name + ' ' + op.range[i].name
                edgelist.append([op.domain[0].name, op.range[i].name, identifier, 1, op.name, True])
                extracted_ops = extracted_ops + 1
    if skipped_ops > 0:
        logging.warning("%i ops were skipped", skipped_ops)
    logging.info("successfully parsed %i Object-Properties from ontology specified", extracted_ops)
    # return list of all extracted edges/ relations
    return edgelist


def get_DPs(onto: OntoEditor, nodelist: list = None, edgelist: list = None):
    """ extracts all data-properties from ontology and returns them in a list that is passed to the function

    :param onto: ontology from which relations are extracted
     :type onto: OntoEditor
     :param nodelist: list of all classes/ instances that were already extracted from the ontology
     :type nodelist:list
     :param edgelist: list of all relations that were already extracted from the ontology
     :type edgelist: list
     :return: returns the nodelist and edgelist including the extracted data-properties
     :rtype: tuple[ list, list]
    """

    # TODO: Filter DPs that have no valid structure (if min/max exclusive is given and exact value is given, a error must
    #  be thrown e.g. faulty dp)
    extracted_dps = 0
    skipped_dps = 0
    if edgelist is None:
        edgelist = []
    if nodelist is None:
        nodelist = []
    # Generator of all data-properties in the ontology is created
    dp_gen = onto.onto.data_properties()
    # Iteration over all data-properties from the generator
    for dp in dp_gen:
        # A list of unique domains of the associated data-property is created
        dp_dom_unique = []
        for dom in dp.domain:
            if not dom in dp_dom_unique:
                dp_dom_unique.append(dom)
        # Booleans to indicate, whether node/ edge is already in nodelist/ edgelist are instantiated
        edge_in_edgelist = False
        # The datatype of the associated data-property is written into a string-variable
        try:
            dp_type = str(dp.range).split("'")[1]
        except IndexError:
            dp_type = 'NoneType'
            logging.warning("the op %s was skipped because there was no defined range", dp.name)
            skipped_dps = skipped_dps + 1
        # Iteration over all relations in edgelist
        for edge in edgelist:
            # Iteration over all unique domains of the associated data-property
            for i, value in enumerate(dp_dom_unique):
                # If there is already a relation between two corresponding domains and data-types,
                # and it is not the first domain of the associated data-property (unless there is only one),
                # the new data-property is added to the existing edge with their id and the data-property's name.
                # Also the weight of the edge is increased by one and the boolean to indicate the edge already
                # exists is set to True
                if edge[0] == dp_dom_unique[i].name and edge[1] == dp_type and (
                        len(dp_dom_unique) == 1 or not i == 0):
                    edge_in_edgelist = True
                    identifier = dp_dom_unique[i].name + ' ' + dp.name + ' ' + dp_type
                    edge[2] = edge[2] + ',\n ' + identifier
                    edge[4] = edge[4] + ',\n ' + dp.name
                    edge[3] = edge[3] + 1
        # If there is not already a relation between two corresponding domains and data-types,
        # and it is not the first domain of the associated data-property (unless there is only one), the new
        # data-property is written to a list with their domain's name, data-type, id, weight, data-property's name
        # and dashes-boolean
        if not edge_in_edgelist:
            for i, value in enumerate(dp_dom_unique):
                if len(dp_dom_unique) == 1 or not i == 0:
                    identifier = dp_dom_unique[i].name + ' ' + dp.name + ' ' + dp_type
                    edgelist.append([dp_dom_unique[i].name, dp_type, identifier, 1, dp.name, True])
        # If the data-type of the associated data-property is already in the nodelist, the boolean to indicate
        # the node already exists is set to True
        node_in_nodelist = is_already_in_list(dp_type, nodelist)
        # If node_in_list is False, the data-type of the associated data-property will be added to the nodelist
        # with their identifier, weight, shape and T-Box label
        if not node_in_nodelist:
            nodelist.append([dp_type, 1, 'triangle', 'T', ""])
        extracted_dps = extracted_dps + 1
    if skipped_dps > 0:
        logging.warning("%i dps were skipped", skipped_dps)
    logging.info("successfully parsed %i Data-Properties from ontology specified", extracted_dps)
    # return list of all extracted nodes/ data-types and list of all extracted edges/ relations
    return nodelist, edgelist


def get_node_importance(nodelist: list, edgelist: list):
    """ weights the nodes in nodelist according to the number of incoming edges

        :param nodelist: list of all classes/ instances that were already extracted from the ontology
         :type nodelist: list
         :param edgelist: list of all relations that were already extracted from the ontology
         :type edgelist: list
         :returns: nodelist including the calculated weights
         :rtype: list
        """
    for node in nodelist:
        counter = 10
        for edge in edgelist:
            if node[0] == edge[1] and edge[4] == 'is_a':
                counter = counter + 1
            # If the counter of a node is higher than zero, the new importance value is assigned
        if counter != 0:
            node[1] = counter
    logging.info("successfully calculated weights for A-/T-Boxes")
    return nodelist


def calculate_node_importance(node_df: pd.DataFrame, edge_df: pd.DataFrame):
    """ weights the nodes in nodelist according to the number of incoming edges

    :param node_df: DataFrame parsed from nodelist
     :type node_df: pd.DataFrame
     :param edge_df: DataFrame parsed from edgelist
     :type edge_df: pd.DataFrame
     :returns: node_df with including the calculated weights
     :rtype: pd.DataFrame
    """
    # Boolean to indicate there is an weight/ importance column in node_df is created
    importance_col = False
    # If there is a column in node_df called importance, importance_col will be set to True
    for col in node_df.columns:
        if col == 'importance':
            importance_col = True
    # If importance_col is True ...
    if importance_col:
        # Iteration over nodes in node_df
        for node_index, node in node_df.iterrows():
            # For every new node-ID the counter is set to zero
            counter = 10
            # Iteration over all edges in edge_df
            for edge_index, edge in edge_df.iterrows():
                # If the ID/ name of a node is equal to the edge to-column and it is an is_a relation,
                # the counter is increased by one
                if node['id'] == edge['to'] and edge['label'] == 'is_a':
                    counter = counter + 1
            # If the counter of a node is higher than zero, the new importance value is assigned
            if counter != 0:
                node_df.loc[node_index, 'importance'] = counter
    # return node_df with new importance values
    logging.info("successfully calculated weights for A-/T-Boxes")
    return node_df


def get_aboxes(onto: OntoEditor, nodelist: list, edgelist: list):
    """ extracts all instances/ A-Boxes from ontology and returns them in a list that is passed to the function

    :param onto: ontology from which relations are extracted
     :type onto: OntoEditor
     :param nodelist: list of all classes/ instances that were already extracted from the ontology
     :type nodelist: list
     :param edgelist: list of all relations that were already extracted from the ontology
     :type edgelist: list
     :returns: nodelist and edgelist including the extracted A-boxes
     :rtype: tuple[ list, list]
    """
    # Generator of all classes in the ontology is created
    node_gen = onto.onto.classes()
    # Iteration over all classes/ nodes in the generator
    for node in node_gen:
        # Iteration over all instances of the associated class
        for ins in onto.onto.search(type=node):
            # Boolean to indicate, whether edge is already in edgelist is instantiated
            edge_in_edgelist = False
            # Get superclass of instance
            superclass = ins.is_a
            # write property in node or edge list depending on OP or DP
            prop_value = ''
            for prop in ins.get_properties():
                for value in prop[ins]:
                    if type(value) == float or type(value) == int or type(value) == str:
                        if prop_value == '' and not (prop.name + ' = ' + str(value)) in prop_value:
                            prop_value = prop.name + ' = ' + str(value)
                        elif not (prop.name + ' = ' + str(value)) in prop_value:
                            prop_value = prop_value + ',\n ' + prop.name + ' = ' + str(value)
                    else:
                        identifier = ins.name + ' ' + prop.name + ' ' + value.name
                        new_edge = [ins.name, value.name, identifier, 1, prop.name, False]
                        if not new_edge in edgelist:
                            edgelist.append(new_edge)
                        # for rel in edgelist:
                        #    if rel[2] == identifier:
                        #        edge_in_edgelist = True
                        # if not edge_in_edgelist:
                        #    edgelist.append([ins.name, value.name, identifier, 1, prop.name, False])
                        edge_in_edgelist = False
            # If there is a class in nodelist that has the same name as the instance node_in_list is set to True
            node_in_nodelist = is_already_in_list(ins.name, nodelist)
            # If node_in_nodelist is False the instance is written in a list with its ID, weight, shape and A-Box label
            if not node_in_nodelist:
                nodelist.append([ins.name, 1, 'box', 'A', prop_value])
            # Iteration over all relations/ edges in edgelist
            for rel in edgelist:
                # If there is already an edge between the instance and its superclass, edge_in_edgelist is set to True.
                # The new relation is added to the existing edge with its ID and label and the weight
                # is increased by one.
                if ins.name == rel[0] and superclass[0].name == rel[1]:
                    edge_in_edgelist = True
                    identifier = ins.name + ' is_a ' + superclass[0].name
                    # The new relation is added to the existing edge with its ID and label and the weight
                    # is increased by one, if there is not already an relationship with the same ID
                    if not identifier == rel[2]:
                        rel[2] = rel[2] + ',\n ' + identifier
                        rel[4] = rel[4] + ',\n ' + 'is_a'
                        rel[3] = rel[3] + 1
            # If edge_in_edgelist is False, the new instance is written into a list
            # with its name, its superclasses' name, identifier, weight, label and dashes-boolean
            if not edge_in_edgelist:
                identifier = ins.name + ' is_a ' + superclass[0].name
                edgelist.append([ins.name, superclass[0].name, identifier, 1, 'is_a', False])
    logging.info('successfully parsed A-Boxes from ontology specified')
    # return list of all extracted instances and list of all extracted edges/ relations
    return nodelist, edgelist


def is_already_in_list(nodename: str, nodelist: list):
    """ checks if a node with a given name, is already in the given list

    :param nodename: the name of the node
     :type nodename: str
     :param nodelist: list of names to check
     :type nodelist: list
     :return: return whether the nodename is already in nodelist
     :rtype: bool
     """
    # Iterate over all classes in nodelist
    for cl in nodelist:
        # If there is a class in nodelist that has the name nodename, True is returned
        if cl[0] == nodename:
            return True
    return False


def get_df_from_ontology(onto: OntoEditor, abox: bool = False):
    """ parses the information given by the ontology into a panda.DataFrame. Parsed data includes:
    T-Boxes, is-a relations, object-properties, data-properties and A-Boxes (if abox is True)

    :param onto: ontology from which the information is extracted
     :type onto: OntoEditor
     :param abox: indicates whether A-Boxes should be extracted or not
     :type abox: bool
     :return: edge_df and node_df including all parsed information
     :rtype: tuple[ pd.DataFrame, pd.DataFrame]
    """
    logging.info("begin parsing data from specified ontology to dataframes...")
    # Get T-Boxes from ontology and write them into nodelist
    nodelist = get_tboxes(onto)
    # Get is-a relations from ontology and write them into edgelist
    edgelist = get_isa_relations(onto)
    # Get object-properties from ontology and write them into edgelist
    edgelist = get_OPs(onto, edgelist)
    # Get data-properties from ontology and write them into edgelist
    nodelist, edgelist = get_DPs(onto, nodelist, edgelist)
    # If abox is True, get A-Boxes from ontology and write them into nodelist
    if abox:
        nodelist, edgelist = get_aboxes(onto, nodelist, edgelist)
    # Calculate the importance of nodes in nodelist
    nodelist = get_node_importance(nodelist, edgelist)
    # Parse nodelist into panda.DataFrame, with column-names id, importance, shape and T/A
    node_df = pd.DataFrame(nodelist)
    node_df.columns = ['id', 'importance', 'shape', 'T/A', 'title']
    # Parse edgelist into panda.DataFrame, with column-names from, to, id, weight, label and dashes
    edge_df = pd.DataFrame(edgelist)
    edge_df.columns = ['from', 'to', 'id', 'weight', 'label', 'dashes']
    # Calculate the importance of nodes in nodelist and write the new importance value into node_df
    # node_df = calculate_node_importance(node_df, edge_df)
    logging.info("...successfully parsed data from ontology specified to dataframes")
    return edge_df, node_df
