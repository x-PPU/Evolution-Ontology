"""
Author: Mohit Mayank

Editor: Maximilian Mayerhofer

Main class for SPARQL-Query-Viz ontology visualization and querying GUI
"""

# import
from .layout import get_app_layout, get_distinct_colors, create_color_legend, get_categorical_features, \
    get_numerical_features, DEFAULT_COLOR, DEFAULT_NODE_SIZE, DEFAULT_EDGE_SIZE, get_options
from .datasets.parse_ontology import *
from .datasets.parse_dataframe import parse_dataframe
from ontor import OntoEditor
import datetime
import logging
import os
import pyparsing
import dash
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

# basic configuration for logging
dir_file = os.path.dirname(__file__)
logfile = dir_file.replace('/SPARQL-Query-Viz/sparql_query_viz',
                           '/SPARQL-Query-Viz/docs/logging/') + datetime.datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S") + "_SparqlQueryViz.log"
logging.basicConfig(filename=logfile, level=logging.INFO)

# imports after logging (ontor would otherwise overwrite the logfile)

# CONSTANTS
PREFIXES = 'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ' \
           'PREFIX owl: <http://www.w3.org/2002/07/owl#> ' \
           'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ' \
           'PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> ' \
           'PREFIX owlready: <http://www.lesfleursdunormal.fr/static/_downloads/owlready_ontology.owl#> ' \
           'PREFIX obo: <http://purl.obolibrary.org/obo/>' \
           'PREFIX : <http://example.org/onto-example.owl#>'


def _callback_search_graph(graph_data: dict, search_text: str):
    """ only show the nodes which match the search text

    :param graph_data: network data in format of visdcc
     :type graph_data: dict
     :param search_text: the text the graph will be searched for
     :type search_text: str
     :return: network data with only the matching results in format of visdcc
     :rtype: dict
    """
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    for node in nodes:
        if (search_text.lower() not in node['label'].lower()) and (search_text not in node['label']):
            node['hidden'] = True
        else:
            node['hidden'] = False
    for edge in edges:
        if search_text in edge['label'].lower():
            for node in nodes:
                if edge['from'].lower() == node['label'].lower():
                    node['hidden'] = False
                elif edge['to'].lower() == node['label'].lower():
                    node['hidden'] = False
    graph_data['nodes'] = nodes
    graph_data['edges'] = edges
    return graph_data


def get_color_popover_legend_children(node_value_color_mapping: dict = None, edge_value_color_mapping: dict = None):
    """ get the popover legends for node and edge based on the color setting

    :param node_value_color_mapping: maps a node value to a specific color
     :type node_value_color_mapping: dict
     :param edge_value_color_mapping: maps an edge value to a specific color
     :type edge_value_color_mapping: dict
     :return: returns a list of dbc.PopoverHeader, html.Div and dbc.PopoverBody - elements
     :rtype: list
    """
    # var
    if edge_value_color_mapping is None:
        edge_value_color_mapping = {}
    if node_value_color_mapping is None:
        node_value_color_mapping = {}
    popover_legend_children = []

    # common function
    def create_legends_for(title="Node", legends=None):
        # add title
        if legends is None:
            legends = {}
        _popover_legend_children = [dbc.PopoverHeader(f"{title} legends")]
        # add values if present
        if len(legends) > 0:
            for key, value in legends.items():
                partition = key.partition(',\n ')
                if partition[2] == '':
                    _popover_legend_children.append(
                        create_color_legend(key, value)
                    )
                else:
                    _popover_legend_children.append(
                        create_color_legend(partition[0], value)
                    )
                    _popover_legend_children.append(
                        create_color_legend(partition[2], value)
                    )
        else:  # otherwise add filler
            _popover_legend_children.append(
                dbc.PopoverBody(f"no {title.lower()} colored!"))

        return _popover_legend_children

    # add node color legends
    popover_legend_children.extend(
        create_legends_for("Node", node_value_color_mapping))
    # add edge color legends
    popover_legend_children.extend(
        create_legends_for("Edge", edge_value_color_mapping))

    return popover_legend_children


def get_nodes_to_be_shown(graph_data: dict, res_list: list = None, number_of_edges_to_be_shown_around_result: int = 1):
    """ gets the nodes in graph_data that are listed in res_list and therefore will be shown in the graph NOTE: with
    number_of_edges_to_be_shown_around_result how many layers of the surrounding neighbourhood will be displayed

    :param graph_data: network data in format of visdcc
     :type graph_data: dict
     :param res_list: list of nodes that will be shown in the graph
     :type res_list: list
     :param number_of_edges_to_be_shown_around_result: how many layers of the surrounding neighbourhood will be displayed
     :type number_of_edges_to_be_shown_around_result: int
     :return: filtered node graph_data and the result nodes that will be selected
     :rtype: tuple[list, list]
     """
    if res_list is None:
        res_list = []
    filtered_node_data = []
    n = 1
    for node in graph_data['nodes']:
        for result in res_list:
            try:
                res_name = result.name
            except AttributeError:
                res_name = ''
            if node['id'] == res_name:
                filtered_node_data.append(node)
    node_selection = filtered_node_data.copy()
    current_level_res_list = node_selection.copy()
    next_level_res_list = []
    while n <= number_of_edges_to_be_shown_around_result:
        for result in current_level_res_list:
            for edge in graph_data['edges']:
                if edge['from'] == result['id']:
                    for node in graph_data['nodes']:
                        if node['id'] == edge['to']:
                            filtered_node_data.append(node)
                            next_level_res_list.append(node)
        current_level_res_list = next_level_res_list.copy()
        next_level_res_list = []
        n = n + 1
    return filtered_node_data, node_selection


class SQV:
    """ The main visualization class of SPARQL-Query-Viz
    """

    def __init__(self, iri: str = "http://example.org/onto-ex.owl",
                 path: str = "./sparql_query_viz/datasets/ontologies/pizza-onto.owl", abox: bool = True):
        """ initialize SQV class

        :param iri: IRI of the ontology
         :type iri: str
         :param path: local path to ontology file
         :type path: str
         :param abox: indicates whether A-Boxes are visualized
         :type abox: bool
         :return: returns an instance of the SQV class
         :rtype: SQV
        """
        self.logger = logging.getLogger('sparql_query_viz-app')
        self.abox = abox
        self.onto = ontor.OntoEditor(iri, path)
        self.edge_df, self.node_df = get_df_from_ontology(self.onto, self.abox)
        self.logger.info(
            "begin parsing data from dataframes to visdcc data format...")
        self.data, self.scaling_vars = parse_dataframe(
            self.edge_df, self.node_df)
        self.logger.info(
            "...successfully parsed data from dataframes to visdcc data format")
        self.filtered_data = self.data.copy()
        self.node_value_color_mapping = {}
        self.edge_value_color_mapping = {}
        self.sparql_query = ''
        self.sparql_query_last_input = ['']
        self.sparql_query_last_input_type = ['']
        self.sparql_query_history = ''
        self.counter_query_history = 0
        self.sparql_query_result = ''
        self.sparql_query_result_list = []
        self.selected_template = ''
        self.nodes_selected_for_template = 0
        self.selected_node_for_template = ''
        self.edges_selected_for_template = 0
        self.selected_edge_for_template = ''

    def edit_edge_appearance(self, directed: bool = True):
        """ edits the arrow heads of is_a relations

        :param directed: indicates whether arrow heads are displayed
         :type directed: bool
         """
        for edge in self.data['edges']:
            if edge['label'] == 'is_a':
                arrow_type = {'arrows': {
                    'to': {'enabled': directed, 'type': 'circle'}}}
            else:
                arrow_type = {'arrows': {
                    'to': {'enabled': directed, 'type': 'arrow'}}}
            edge.update(arrow_type)

    def clear_selection_for_template_query(self):
        """ deletes/ clears the selection made by the user for query templates
        """
        self.selected_template = ''
        self.nodes_selected_for_template = 0
        self.selected_node_for_template = ''
        self.edges_selected_for_template = 0
        self.selected_edge_for_template = ''

    def complete_sparql_query_with_selection(self, selection: dict, template: str):
        """ inserts the selection made by the user into the chosen template

        :param selection: selected node/ edge
         :type selection: dict
         :param template: file name of the template that was chosen
         :type template: str
         """
        if len(selection['nodes']) > 0:
            max_number_of_selected_nodes = -1
            placeholder = ''
            for node in self.data['nodes']:
                if [node['id']] == selection['nodes']:
                    self.sparql_query_last_input.append(' :' + node['id'])
                    if template == "template_2.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_3.sparql":
                        max_number_of_selected_nodes = 3
                    elif template == "template_4.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_5.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_6.sparql":
                        max_number_of_selected_nodes = 2
                    elif template == "template_7.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_8.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_9.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_10.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_11.sparql":
                        max_number_of_selected_nodes = 2
                    elif template == "template_12.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_13.sparql":
                        max_number_of_selected_nodes = 1
                    elif template == "template_14.sparql":
                        max_number_of_selected_nodes = 2
                    elif template == "template_15.sparql":
                        max_number_of_selected_nodes = 2
                    elif template == "template_16.sparql":
                        max_number_of_selected_nodes = 3
                    elif template == "template_17.sparql":
                        max_number_of_selected_nodes = 3
                    elif template == "template_18.sparql":
                        max_number_of_selected_nodes = 3
                    elif template == "template_19.sparql":
                        max_number_of_selected_nodes = 4
                    elif template == "template_20.sparql":
                        max_number_of_selected_nodes = 3
                    if '[:node]' in self.sparql_query:
                        placeholder = "[:node]"
                    elif '[:node1]' in self.sparql_query:
                        placeholder = "[:node1]"
                    elif '[:node2]' in self.sparql_query:
                        placeholder = "[:node2]"
                    elif '[:node3]' in self.sparql_query:
                        placeholder = "[:node3]"
                    if self.nodes_selected_for_template < max_number_of_selected_nodes and template and (
                            placeholder != ''):
                        self.sparql_query = self.sparql_query.replace(
                            placeholder, self.sparql_query_last_input[-1])
                        self.nodes_selected_for_template = self.nodes_selected_for_template + 1
                        self.selected_node_for_template = self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('select_node')
                    elif self.nodes_selected_for_template == max_number_of_selected_nodes:
                        pass
                    else:
                        self.sparql_query = self.sparql_query + \
                            self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                    self.logger.info("%s added to sparql query",
                                     self.sparql_query_last_input[-1])
        elif len(selection['edges']) > 0:
            max_number_of_selected_edges = -1
            placeholder = ''
            for edge in self.data['edges']:
                if [edge['id']] == selection['edges']:
                    self.sparql_query_last_input.append(' :' + edge['label'])
                    if template == "template_2.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_3.sparql":
                        max_number_of_selected_edges = 2
                    elif template == "template_5.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_6.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_7.sparql":
                        max_number_of_selected_edges = 2
                    elif template == "template_8.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_9.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_11.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_12.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_14.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_15.sparql":
                        max_number_of_selected_edges = 1
                    elif template == "template_16.sparql":
                        max_number_of_selected_edges = 3
                    elif template == "template_17.sparql":
                        max_number_of_selected_edges = 2
                    elif template == "template_18.sparql":
                        max_number_of_selected_edges = 2
                    elif template == "template_19.sparql":
                        max_number_of_selected_edges = 3
                    elif template == "template_20.sparql":
                        max_number_of_selected_edges = 1
                    if '[:edge]' in self.sparql_query:
                        placeholder = "[:edge]"
                    elif '[:edge1]' in self.sparql_query:
                        placeholder = "[:edge1]"
                    elif '[:edge2]' in self.sparql_query:
                        placeholder = "[:edge2]"
                    elif '[:edge3]' in self.sparql_query:
                        placeholder = "[:edge3]"
                    if self.edges_selected_for_template < max_number_of_selected_edges and (placeholder != ''):
                        self.sparql_query = self.sparql_query.replace(
                            placeholder, self.sparql_query_last_input[-1])
                        self.edges_selected_for_template = self.edges_selected_for_template + 1
                        self.selected_edge_for_template = self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('select_edge')
                    elif self.edges_selected_for_template == max_number_of_selected_edges:
                        pass
                    else:
                        self.sparql_query = self.sparql_query + \
                            self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                    self.logger.info("%s added to sparql query",
                                     self.sparql_query_last_input[-1])

    def delete_last_user_input(self):
        if not self.sparql_query_last_input_type:
            pass
        elif self.sparql_query_last_input_type[-1] == 'user_input':
            self.sparql_query = self.sparql_query.replace(
                self.sparql_query_last_input[-1], '')
        elif self.sparql_query_last_input_type[-1] == 'select_node':
            self.sparql_query = self.sparql_query.replace(
                self.sparql_query_last_input[-1], ':[node]', 1)
            self.selected_node_for_template = ''
            self.nodes_selected_for_template = self.nodes_selected_for_template - 1
        elif self.sparql_query_last_input_type[-1] == 'select_edge':
            self.sparql_query = self.sparql_query.replace(
                self.sparql_query_last_input[-1], ':[edge]', 1)
            self.selected_edge_for_template = ''
            self.edges_selected_for_template = self.edges_selected_for_template - 1
        self.sparql_query_last_input.pop(-1)
        self.sparql_query_last_input_type.pop(-1)
        self.logger.info(
            'last input from user deleted from sparql query, triggered by user')

    def add_to_query_history(self):
        """ adds the evaluated query to the query history
        """
        self.counter_query_history = self.counter_query_history + 1
        self.sparql_query_history = self.sparql_query_history + str(
            self.counter_query_history) + ": " + self.sparql_query + '\n'

    def _callback_filter_nodes(self, graph_data: dict, shown_result_level: int = 1):
        """ filters the nodes based on the SPARQL query syntax

        :param graph_data: network data in format of visdcc
         :type graph_data: dict
         :param shown_result_level: how many layers of the surrounding neighbourhood will be displayed
         :type shown_result_level: int
         :return: the filtered graph_data, the result nodes as string, and the nodes  that will be selected
         :rtype: tuple[dict, str, dict]
        """
        self.filtered_data = self.data.copy()
        selection = {'nodes': [], 'edges': []}
        if self.sparql_query:
            try:
                rdflib_onto = self.onto.onto_world.as_rdflib_graph()
                res_list = list(rdflib_onto.query_owlready(
                    PREFIXES + self.sparql_query))

                if not res_list:
                    graph_data = self.data
                    result = "No results for this SPARQL query."
                    self.sparql_query_result = result
                    self.add_to_query_history()
                    self.logger.info(
                        "valid sparql query successfully evaluated")
                    self.logger.info("result for passed sparql query is empty")
                    return graph_data, result, selection
                else:
                    if type(res_list[0]) == list:
                        flat_res_list = [x for l in res_list for x in l]
                    else:
                        flat_res_list = res_list
                    self.sparql_query_result_list = flat_res_list
                    result = ""
                    res_is_no_data_object = True
                for flat_res in flat_res_list:
                    try:
                        result = result + str(flat_res.name) + "\n"
                        self.logger.info(
                            "result is a valid node/edge of graph")
                        res_is_no_data_object = False
                    except AttributeError:
                        graph_data = self.data
                        result = result + str(flat_res) + "\n"
                        self.logger.info(
                            "result is not an object (A-/ T-Box) in graph (different data-type)")
                self.sparql_query_result = result
                if not res_is_no_data_object:
                    self.filtered_data['nodes'], selection['nodes'] = get_nodes_to_be_shown(self.filtered_data,
                                                                                            flat_res_list,
                                                                                            shown_result_level)
                    graph_data = self.filtered_data
                self.add_to_query_history()
                self.logger.info("valid sparql query successfully evaluated")
            except pyparsing.ParseException:
                graph_data = self.data
                result = "Syntax Error in SPARQL Query."
                self.sparql_query_result = result
                self.logger.warning(
                    "sparql query passed from user includes a syntax error")
            except Exception:
                graph_data = self.data
                result = "An unknown Error occurred! Possible reasons are: " \
                         "\n - Used Prefix is not defined " \
                         "\n - Structural mistake in query"
                self.sparql_query_result = result
                self.logger.warning(
                    "sparql query passed from user includes an error")

        else:
            graph_data = self.data
            result = "There is nothing to evaluate."
            self.sparql_query_result = result
            self.logger.warning("sparql query passed from user is empty")
        return graph_data, result, selection

    def _callback_sparql_query_history(self, number_of_shown_queries: int):
        """ gets the sparql queries to be shown in the sparql query history

        :param number_of_shown_queries: how many queries will be included in the history
        :type number_of_shown_queries: int
        :return: the history of sparql queries to be shown
        :rtype: str
        """
        sparql_query_history = self.sparql_query_history
        if self.counter_query_history > number_of_shown_queries:
            separator = str(self.counter_query_history -
                            (number_of_shown_queries - 1)) + ": "
            partition = sparql_query_history.partition(separator)
            shown_sparql_query_history = partition[1] + partition[2]
        else:
            shown_sparql_query_history = sparql_query_history
        return shown_sparql_query_history

    def _callback_color_nodes(self, color_nodes_value: str):
        """ colors the nodes according to the color_nodes_value

        :param color_nodes_value: the feature that is used to color the nodes
         :type color_nodes_value: str
         :return: the graph_data with the adjusted node-color values and the color-value mapping
         :rtype: tuple[dict, dict]
        """
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_nodes_value == 'None':
            # revert to default color
            for node in self.data['nodes']:
                node['color'] = DEFAULT_COLOR
        else:
            unique_values = pd.DataFrame(self.data['nodes'])[
                color_nodes_value].unique()
            colors = get_distinct_colors(len(unique_values), for_nodes=True)
            value_color_mapping = {x: y for x, y in zip(unique_values, colors)}
            for node in self.data['nodes']:
                node['color'] = value_color_mapping[node[color_nodes_value]]
        # filter the data currently shown
        filtered_nodes = [x['id'] for x in self.filtered_data['nodes']]
        self.filtered_data['nodes'] = [
            x for x in self.data['nodes'] if x['id'] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping

    def _callback_size_nodes(self, size_nodes_value: str):
        """ sizes the nodes according to the size_nodes_value

                :param size_nodes_value: the feature that is used to size the nodes
                 :type size_nodes_value: str
                 :return: the graph_data with the adjusted edge-size values
                 :rtype: dict
                """
        minn = 0
        maxx = 100
        # fetch the scaling value
        if size_nodes_value != 'None':
            # fetch the scaling value
            minn = self.scaling_vars['node'][size_nodes_value]['min']
            maxx = self.scaling_vars['node'][size_nodes_value]['max']
        # color option is None, revert back all changes
        if size_nodes_value == 'None' or minn == maxx:
            # revert to default size
            for node in self.data['nodes']:
                node['size'] = DEFAULT_NODE_SIZE
        else:
            # define the scaling function
            def scale_val(x): return 20 * (x - minn) / (maxx - minn)
            # set size after scaling
            for node in self.data['nodes']:
                node['size'] = node['size'] + scale_val(node[size_nodes_value])
        # filter the data currently shown
        filtered_nodes = [x['id'] for x in self.filtered_data['nodes']]
        self.filtered_data['nodes'] = [
            x for x in self.data['nodes'] if x['id'] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data

    def _callback_color_edges(self, color_edges_value: str):
        """ colors the edges according to the color_edges_value

                :param color_edges_value: the feature that is used to color the edges
                 :type color_edges_value: str
                 :return: the graph_data with the adjusted edge-color values and the color-value mapping
                 :rtype: tuple[dict, dict]
                """
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_edges_value == 'None':
            # revert to default color
            for edge in self.data['edges']:
                edge['color']['color'] = DEFAULT_COLOR
        else:
            unique_values = pd.DataFrame(self.data['edges'])[
                color_edges_value].unique()
            colors = get_distinct_colors(len(unique_values), for_nodes=False)
            value_color_mapping = {x: y for x, y in zip(unique_values, colors)}
            for edge in self.data['edges']:
                edge['color']['color'] = value_color_mapping[edge[color_edges_value]]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [
            x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping

    def _callback_size_edges(self, size_edges_value: str):
        """ sizes the edges according to the size_edges_value

        :param size_edges_value: the feature that is used to size the edges
         :type size_edges_value: str
         :return: the graph_data with the adjusted edge-size values
         :rtype: dict
        """
        minn = 0
        maxx = 100
        # fetch the scaling value
        if size_edges_value != 'None':
            minn = self.scaling_vars['edge'][size_edges_value]['min']
            maxx = self.scaling_vars['edge'][size_edges_value]['max']
        # if color option is None or minn and maxx is the same, revert back all changes
        if size_edges_value == 'None' or minn == maxx:
            # revert to default size
            for edge in self.data['edges']:
                edge['width'] = DEFAULT_EDGE_SIZE
        else:
            # define the scaling function
            def scale_val(x): return 5 * (x - minn) / (maxx - minn)
            # set the size after scaling
            for edge in self.data['edges']:
                if edge[size_edges_value] == minn:
                    edge['width'] = DEFAULT_EDGE_SIZE
                else:
                    edge['width'] = scale_val(edge[size_edges_value])
                # edge['width'] = edge[size_edges_value]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [
            x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data

    def forced_callback_execution_at_beginning(self, directed=True):
        """ executes the callback functions for node and edge Coloring and Sizing at start of the app

        :param directed: indicates whether graph is directed
         :type directed: bool
         """

        # Give all is_a edges a circle as arrowhead
        self.edit_edge_appearance(directed=directed)
        # Get list of categorical features from nodes
        cat_node_features = get_categorical_features(pd.DataFrame(self.data['nodes']),
                                                     20, ['shape', 'label', 'id', 'title', 'color'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_node_features]
        # If options has more then one categorical feature, the callback function for nodes-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data, self.node_value_color_mapping = self._callback_color_nodes(
                options[1].get('value'))
            self.logger.info("Nodes were initially colored")
        # Get list of categorical features from edges
        cat_edge_features = get_categorical_features(pd.DataFrame(self.data['edges']).drop(
            columns=['color', 'from', 'to', 'id', 'arrows']), 20, ['color', 'from', 'to', 'id'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_edge_features]
        # If options has mor then one categorical feature, the callback function for edge-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data, self.edge_value_color_mapping = self._callback_color_edges(
                options[1].get('value'))
            self.logger.info("Edges were initially colored")
        # Get list of numerical features from nodes
        num_node_features = get_numerical_features(
            pd.DataFrame(self.data['nodes']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_node_features]
        # If options has mor then one numerical feature, the callback function for nodes-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data = self._callback_size_nodes(options[1].get('value'))
            self.logger.info("Nodes were initially sized")
        # Get list of numerical features from edges
        num_edge_features = get_numerical_features(
            pd.DataFrame(self.data['edges']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_edge_features]
        # If options has mor then one numerical feature, the callback function for edge-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data = self._callback_size_edges(options[1].get('value'))
            self.logger.info("Edges were initially sized")

    def create(self, directed: bool = False, vis_opts: dict = None):
        """ creates the SPARQl-Query-Viz app and returns it

        :param directed: indicates whether the graph is directed
         :type directed: bool
         :param vis_opts: additional visualization options for the visdcc-graph
         :type vis_opts: dict
         :return: the SPARQl-Query-Viz app
         :rtype dash.Dash
        """
        # create the app
        app = dash.Dash(__name__, external_stylesheets=[
                        dbc.themes.BOOTSTRAP], title='SPARQL-Query-Viz')

        # get color_mapping and size_mapping once at the start
        self.forced_callback_execution_at_beginning(directed=directed)

        # define layout
        app.layout = get_app_layout(self.data, self.onto, color_legends=get_color_popover_legend_children(),
                                    directed=directed, vis_opts=vis_opts, abox=self.abox)

        # create callback to freeze/ unfreeze simulation
        @app.callback(
            Output("graph", "options"),
            Input("freeze-physics", "n_clicks"),
            [State("graph", "options")],
        )
        def toggle_filter_collapse(n_show, options):
            if n_show and options['physics'] == {'enabled': False}:
                options = get_options(directed=directed, opts_args=vis_opts)
            elif n_show:
                options = get_options(
                    directed=directed, opts_args=vis_opts, physics=False)
            return options

        # create callback to toggle legend popover
        @app.callback(
            Output("color-legend-popup", "is_open"),
            [Input("color-legend-toggle", "n_clicks")],
            [State("color-legend-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "legend popup was hidden, triggered by user")
                else:
                    self.logger.info(
                        "legend popup was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle sparql-info popover
        @app.callback(
            Output("info-sparql-popup", "is_open"),
            [Input("info-sparql-query-button", "n_clicks")],
            [State("info-sparql-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "sparql info popup was hidden, triggered by user")
                else:
                    self.logger.info(
                        "sparql info popup was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle hide/show sections - SPARQL QUERY section
        @app.callback(
            Output("filter-show-toggle", "is_open"),
            [Input("filter-show-toggle-button", "n_clicks"),
             Input('sparql_template_dropdown', 'value'),
             Input('inconsistency_template_dropdown', 'value'),
             Input('sparql_library_dropdown', 'value'), ],
            [State("filter-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, template_value, incons_template_value, library_value, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "filter-show-toggle-button" and n_show:
                    if is_open:
                        self.logger.info(
                            "sparql query section was hidden, triggered by user")
                    else:
                        self.logger.info(
                            "sparql query section was shown, triggered by user")
                    return not is_open
                if (input_id == "sparql_template_dropdown" and template_value) \
                        or (input_id == "sparql_library_dropdown" and library_value)\
                        or (input_id == "inconsistency_template_dropdown" and incons_template_value):
                    self.logger.info(
                        "sparql query section was shown, because template/library input was triggered")
                    return True
            return is_open

        # create callback to toggle hide/show sections - SPARQL RESULT section
        @app.callback(
            Output("result-show-toggle", "is_open"),
            [Input("result-show-toggle-button", "n_clicks"),
             Input('evaluate_query_button', 'n_clicks'),
             Input('select_button', 'n_clicks')],
            [State("result-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, n_evaluate, n_select, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "result-show-toggle-button" and n_show:
                    if is_open:
                        self.logger.info(
                            "sparql result section was hidden, triggered by user")
                    else:
                        self.logger.info(
                            "sparql result section was shown, triggered by user")
                    return not is_open
                if input_id == "evaluate_query_button" and n_evaluate:
                    self.logger.info(
                        "sparql result section was shown, because evaluation button was triggered")
                    return True
                elif input_id == "select_button" and n_select:
                    self.logger.info(
                        "sparql result section was shown, because select button was triggered")
                    return True
            return is_open

        # create callback to toggle hide/show sections - SPARQL HISTORY section
        @app.callback(
            Output("history-show-toggle", "is_open"),
            [Input("history-show-toggle-button", "n_clicks")],
            [State("history-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, is_open):
            if n_show:
                if is_open:
                    self.logger.info(
                        "sparql history section was hidden, triggered by user")
                else:
                    self.logger.info(
                        "sparql history section was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to interactively compose SPARQL queries
        @app.callback(
            Output("select-sparql", "children"),
            [Input("sparql-keywords-dropdown", "value"),
             Input("sparql-variables-dropdown", "value"),
             Input("sparql-syntax-dropdown", "value"),
             Input("add_to_query_button", "n_clicks"),
             Input("clear_query_button", "n_clicks"),
             Input("delete_query_button", "n_clicks"),
             Input("add_node_edge_to_query_button", "on"),
             Input('graph', 'selection'),
             Input('sparql_template_dropdown', 'value'),
             Input('inconsistency_template_dropdown', 'value'),
             Input('sparql_library_dropdown', 'value')],
            [State("filter_nodes", "value")],
        )
        def edit_sparql_query(kw_value, var_value, syn_value, n_add,
                              n_clear, n_delete, on_select, selection, template_value,
                              inconsistency_template_value, library_value, value):
            ctx = dash.callback_context
            if self.sparql_query is None:
                self.sparql_query = ""

            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return self.sparql_query
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation depending on which sparql button was triggered
                if input_id == "sparql-keywords-dropdown":
                    if kw_value is not None:
                        if kw_value == "PREFIX":
                            self.sparql_query_last_input.append(
                                " PREFIX : <" + self.onto.iri + "#>")
                        elif kw_value == "SELECT":
                            self.sparql_query_last_input.append(" SELECT")
                        else:
                            self.sparql_query_last_input.append(" " + kw_value)
                        self.sparql_query = self.sparql_query + \
                            self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                        self.logger.info(
                            "%s - keyword added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "sparql-variables-dropdown":
                    if var_value is not None:
                        self.sparql_query_last_input.append(" " + var_value)
                        if 'COUNT ( ?[...] ) AS' in self.sparql_query:
                            self.sparql_query = self.sparql_query.replace(
                                ' ?[...]', self.sparql_query_last_input[-1])
                        else:
                            self.sparql_query = self.sparql_query + \
                                self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                        self.logger.info(
                            "%s - variable added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "sparql-syntax-dropdown":
                    if syn_value is not None:
                        self.sparql_query_last_input.append(" " + syn_value)
                        self.sparql_query = self.sparql_query + \
                            self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                        self.logger.info(
                            "%s - syntax added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "add_to_query_button":
                    if n_add and value is not None:
                        self.sparql_query_last_input.append(' ' + value)
                        self.sparql_query = self.sparql_query + \
                            self.sparql_query_last_input[-1]
                        self.sparql_query_last_input_type.append('user_input')
                        self.logger.info(
                            "user-text-input %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "clear_query_button":
                    if n_clear:
                        self.sparql_query_last_input = ['']
                        self.sparql_query = ''
                        self.sparql_query_last_input_type = ['']
                        self.logger.info("sparql query cleared by user")
                        self.clear_selection_for_template_query()
                elif input_id == "delete_query_button":
                    if n_delete:
                        self.delete_last_user_input()
                elif input_id == "sparql_template_dropdown" and template_value:
                    query = open(
                        "sparql_query_viz/datasets/templates/" + template_value, "r")
                    self.sparql_query_last_input.append(
                        "PREFIX : <" + self.onto.iri + "#>" + "\n" + "\n" + query.read())
                    self.sparql_query = self.sparql_query_last_input[-1]
                    self.clear_selection_for_template_query()
                    self.selected_template = template_value
                    self.sparql_query_last_input_type.append('user_input')
                    self.logger.info(
                        "standard-template: %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "inconsistency_template_dropdown" and inconsistency_template_value:
                    query = open("sparql_query_viz/datasets/templates/" +
                                 inconsistency_template_value, "r")
                    self.sparql_query_last_input.append(
                        "PREFIX : <" + self.onto.iri + "#>" + "\n" + "\n" + query.read())
                    self.sparql_query = self.sparql_query_last_input[-1]
                    self.clear_selection_for_template_query()
                    self.selected_template = inconsistency_template_value
                    self.sparql_query_last_input_type.append('user_input')
                    self.logger.info("inconsistency-template: %s added to sparql query",
                                     self.sparql_query_last_input[-1])
                elif input_id == "sparql_library_dropdown" and library_value:
                    query = open(
                        "sparql_query_viz/datasets/queries/" + library_value, "r")
                    self.sparql_query_last_input.append(
                        "PREFIX : <" + self.onto.iri + "#>" + "\n" + "\n" + query.read())
                    self.sparql_query = self.sparql_query_last_input[-1]
                    self.clear_selection_for_template_query()
                    self.sparql_query_last_input_type.append('user_input')
                    self.logger.info(
                        "Inconsistency Check: %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "graph" and selection != {'nodes': [], 'edges': []} and on_select:
                    self.complete_sparql_query_with_selection(
                        selection, self.selected_template)
            return self.sparql_query

        # create callback to toggle hide/show sections - COLOR section
        @app.callback(
            Output("color-show-toggle", "is_open"),
            [Input("color-show-toggle-button", "n_clicks")],
            [State("color-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "color section was hidden, triggered by user")
                else:
                    self.logger.info(
                        "color section was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle hide/show sections - SIZE section
        @app.callback(
            Output("size-show-toggle", "is_open"),
            [Input("size-show-toggle-button", "n_clicks")],
            [State("size-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "size section was hidden, triggered by user")
                else:
                    self.logger.info(
                        "size section was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle hide/show sections - SPARQL TEMPLATE section
        @app.callback(
            Output("template-show-toggle", "is_open"),
            [Input("template-show-toggle-button", "n_clicks")],
            [State("template-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "template section was hidden, triggered by user")
                else:
                    self.logger.info(
                        "template section was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle hide/show sections - SPARQL LIBRARY section
        @app.callback(
            Output("library-show-toggle", "is_open"),
            [Input("library-show-toggle-button", "n_clicks")],
            [State("library-show-toggle", "is_open")],
        )
        def toggle_library_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info(
                        "library section was hidden, triggered by user")
                else:
                    self.logger.info(
                        "library section was shown, triggered by user")
                return not is_open
            return is_open

        # create callback to toggle hide/show sections - A-BOX DATA-PROPERTY section
        @app.callback(
            Output("abox-dp-show-toggle", "is_open"),
            [Input("abox-dp-show-toggle-button", "n_clicks"),
             Input('graph', 'selection'),
             Input("add_node_edge_to_query_button", "on")],
            [State("abox-dp-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, selection, on_select, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "abox-dp-show-toggle-button":
                    if n:
                        if is_open:
                            self.logger.info(
                                "A-Box Data Property section was hidden, triggered by user")
                            return not is_open
                        else:
                            self.logger.info(
                                "A-Box Data Property section was shown, triggered by user")
                            return not is_open
                if input_id == "graph":
                    if on_select:
                        return is_open
                    elif len(selection['nodes']) > 0:
                        for node in self.data['nodes']:
                            if [node['id']] == selection['nodes']:
                                if node['T/A'] == 'A':
                                    self.logger.info(
                                        "A-Box Data Property section was shown, triggered by user")
                                    return True
                                else:
                                    self.logger.info(
                                        "A-Box Data Property section was hidden, triggered by user")
                                    return False
                    elif (selection == {'nodes': [], 'edges': []}) or \
                            (len(selection['nodes']) == 0 and len(selection['edges']) > 0):
                        self.logger.info(
                            "A-Box Data Property section was hidden, triggered by user")
                        return False
            return is_open

        # create callback to toggle hide/show sections - SELECTED EDGE section
        @app.callback(
            Output("edge-selection-show-toggle", "is_open"),
            [Input("edge-selection-show-toggle-button", "n_clicks"),
             Input('graph', 'selection'),
             Input("add_node_edge_to_query_button", "on")],
            [State("edge-selection-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, selection, on_select, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "edge-selection-show-toggle-button":
                    if n:
                        if is_open:
                            self.logger.info(
                                "edge selection section was hidden, triggered by user")
                            return not is_open
                        else:
                            self.logger.info(
                                "edge selection section was shown, triggered by user")
                            return not is_open
                if input_id == "graph":
                    if on_select:
                        return is_open
                    elif len(selection['edges']) > 0 and len(selection['nodes']) == 0:
                        self.logger.info(
                            "edge selection section was shown, triggered by user")
                        return True
                    elif (selection == {'nodes': [], 'edges': []}) or len(selection['nodes']) > 0:
                        self.logger.info(
                            "edge selection section was hidden, triggered by user")
                        return False
            return is_open

        # create callback to display dp of selected A-Box
        @app.callback(
            Output('node-selection', 'children'),
            [Input('graph', 'selection')])
        def show_dp_from_selected_node(x):
            s_node = ''
            if len(x['nodes']) > 0:
                for node in self.data['nodes']:
                    if [node['id']] == x['nodes']:
                        if node['T/A'] == 'T':
                            return s_node
                        s_node = [html.Div(x['nodes'] + [': '])]
                        if node['title'] == '':
                            return s_node + [html.Div(['No Data-Properties for this A-Box'])]
                        separator = ',\n '
                        partition = node['title'].partition(separator)
                        if separator in node['title']:
                            s_node = s_node + [html.Div([partition[0]])]
                            while separator in partition[2]:
                                partition = partition[2].partition(separator)
                                s_node = s_node + [html.Div([partition[0]])]
                            s_node = s_node + [html.Div([partition[2]])]
                        else:
                            s_node = s_node + [html.Div([node['title']])]
            return s_node

        # create callback to display label of selected edge
        @app.callback(
            Output('edge-selection', 'children'),
            [Input('graph', 'selection')])
        def show_label_from_selected_edge(x):
            s_edge = ''
            if len(x['edges']) > 0:
                for edge in self.data['edges']:
                    if [edge['id']] == x['edges']:
                        separator = ',\n '
                        partition_id = edge['id'].partition(separator)
                        partition_label = edge['label'].partition(separator)
                        if (separator in edge['id']) and (separator in edge['label']):
                            s_edge = [html.Div([partition_label[0]] + [': '])]
                            s_edge = s_edge + [html.Div([partition_id[0]])]
                            while (separator in partition_id[2]) and (separator in partition_label[2]):
                                partition_id = partition_id[2].partition(
                                    separator)
                                partition_label = partition_label[2].partition(
                                    separator)
                                s_edge = s_edge + \
                                    [html.Div([partition_label[0]] + [': '])]
                                s_edge = s_edge + [html.Div([partition_id[0]])]
                            s_edge = s_edge + \
                                [html.Div([partition_label[2]] + [': '])]
                            s_edge = s_edge + [html.Div([partition_id[2]])]
                        else:
                            s_edge = [html.Div([edge['label']] + [': '])]
                            s_edge = s_edge + [html.Div([edge['id']])]
            return s_edge

#! ---------------------------------------------- Create and Run Query ------------------
        # * Create callback with two selectors + button as input
        # * Assemble query based upon selector
        # * Run and show query
      #  @app.callback(
       #     Output("test-text", "children"),
        #    [
         #       Input('select_button', 'n_clicks'),
          #      Input('scenario_select_dropdown', 'value'),
           #     Input('terminology_select_dropdown', 'value')
            #],
      #      State('graph', 'data')
       # )
#    '''     """ 
#        def compose_scenario_query(n, scenario_in, terminology_in, graph_data):
#             ctx = dash.callback_context
#             if not ctx.triggered:
#                 self.logger.info("no trigger by user")
#                 return False
#             else:
#                 self.logger.info(n)
#                 if n:
#                     scenario = str(scenario_in)
#                     terminology = str(terminology_in)
#                     query = ("SELECT DISTINCT ?element \n"
#                              "WHERE { \n"
#                              f"?element a/rdfs:subClassOf* :{terminology}. \n"
#                              f":{scenario} :has_info_source ?source. \n"
#                              "{ ?source ?connectedTo ?element } \n"
#                              "} GROUP BY ?element")
#                     self.sparql_query = PREFIXES + query
#                     graph_data, result, selection = self._callback_filter_nodes(
#                         graph_data, 1)
#                     return 'result'
#                 return 'no'
#         """ '''

        # create the main callbacks
        @app.callback(
            [Output('graph', 'data'),
             Output('color-legend-popup', 'children'),
             Output('textarea-result-output', 'children'),
             Output('sparql_query_history', 'children'),
             Output('graph', 'selection')],
            [Input('search_graph', 'value'),
             Input('color_nodes', 'value'),
             Input('color_edges', 'value'),
             Input('size_nodes', 'value'),
             Input('size_edges', 'value'),
             Input('evaluate_query_button', 'n_clicks'),
             Input('clear-query-history-button', 'n_clicks'),
             Input('query-history-length-slider', 'value'),
             Input("color-legend-toggle", "n_clicks"),
             Input('result-level-slider', 'value'),
             Input('select_button', 'n_clicks') , 
             Input('scenario_select_dropdown', 'value'),
             Input('terminology_select_dropdown', 'value')],
            [State('graph', 'data')]
        )
        def setting_pane_callback(search_text, color_nodes_value, color_edges_value,
                                  size_nodes_value, size_edges_value, n_evaluate, n_clear, query_history_length,
                                  n_legend, shown_result_level, n_select, scenario, terminology, graph_data):
            # fetch the id of option which triggered
            ctx = dash.callback_context
            flat_res_list_children = self.sparql_query_result
            sparql_query_history_children = []
            selection = {'nodes': [], 'edges': []}
            # if its the first call
            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return [self.data, get_color_popover_legend_children(),
                        flat_res_list_children, sparql_query_history_children, selection]
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation in case of search graph option
                if input_id == "search_graph":
                    graph_data = _callback_search_graph(
                        graph_data, search_text)
                    self.logger.info(
                        "shown graph data filtered, triggered by user")
                # In case filter nodes was triggered
                elif (input_id == 'evaluate_query_button' and n_evaluate) or (input_id == 'select_button' and n_select):
                    if input_id == 'select_button':
                        query = ("SELECT DISTINCT ?element \n"
                             "WHERE { \n"
                             f"?element a/rdfs:subClassOf* :{terminology}. \n"
                             f":{scenario} :has_info_source ?source. \n"
                             "{ ?source ?connectedTo ?element } \n"
                             "} GROUP BY ?element")
                        self.sparql_query = PREFIXES + query
                    graph_data, flat_res_list_children, selection = self._callback_filter_nodes(graph_data,
                                                                                                shown_result_level)
                elif input_id == 'result-level-slider':
                    graph_data['nodes'], selection['nodes'] = get_nodes_to_be_shown(self.data,
                                                                                    self.sparql_query_result_list,
                                                                                    shown_result_level)
                if input_id == "clear-query-history-button" and n_clear:
                    self.counter_query_history = 0
                    self.sparql_query_history = ""
                    self.logger.info(
                        "query history was cleared, triggered by user")
                # If color node text is provided
                if input_id == 'color_nodes':
                    graph_data, self.node_value_color_mapping = self._callback_color_nodes(
                        color_nodes_value)
                    self.logger.info("Nodes were recolored, triggered by user")
                # If color edge text is provided
                if input_id == 'color_edges':
                    graph_data, self.edge_value_color_mapping = self._callback_color_edges(
                        color_edges_value)
                    self.logger.info("Edges were recolored, triggered by user")
                # If size node text is provided
                if input_id == 'size_nodes':
                    graph_data = self._callback_size_nodes(size_nodes_value)
                    self.logger.info("Nodes were resized, triggered by user")
                # If size edge text is provided
                if input_id == 'size_edges':
                    graph_data = self._callback_size_edges(size_edges_value)
                    self.logger.info("Edges were resized, triggered by user")
            # create the color legend children
            color_popover_legend_children = get_color_popover_legend_children(
                self.node_value_color_mapping, self.edge_value_color_mapping)
            self.logger.info("color legend was updated, triggered by user")
            # update the sparql query history
            sparql_query_history_children = self._callback_sparql_query_history(
                query_history_length)
            self.logger.info(
                "query history is shown with a length of %i", query_history_length)
            # finally return the modified data
            return [graph_data, color_popover_legend_children, flat_res_list_children,
                    sparql_query_history_children, selection]

        return app

    def plot(self, debug: bool = False, host: str = "127.0.0.1", port: int = 8050,
             directed: bool = True, vis_opts: dict = None):
        """Plot the Jaal by first creating the app and then hosting it on default server


        :param debug: run the debug instance of Dash?
        :type debug: bool
        :param host: ip address on which to run the dash server
        :type host: str
        :param port: port on which to expose the dash server
        :type port: int
        :param directed: whether the graph is directed or not
        :type directed: bool
        :param vis_opts: the visual options to be passed to the dash server
        :type directed: dict
        """
        # call the create_graph function
        app = self.create(directed=directed, vis_opts=vis_opts)
        # run the server
        app.run_server(debug=debug, host=host, port=port)
