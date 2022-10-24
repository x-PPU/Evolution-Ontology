"""
Author: Mohit Mayank

Editor: Maximilian Mayerhofer

Layout code for the application
"""
# import
import logging
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
import visdcc
from dash import dcc, html
from ontor import OntoEditor
from sparql_query_viz.components import scenario_select_form
# CONSTANTS
# default node and edge size
DEFAULT_NODE_SIZE = 300
DEFAULT_EDGE_SIZE = 1

# default node and edge color
DEFAULT_COLOR = '#97C2FC'

# Taken from https://stackoverflow.com/questions/470690/how-to-automatically-generate-n-distinct-colors
KELLY_COLORS_HEX = [
    "#FFB300",  # Vivid Yellow
    "#A6BDD7",  # Very Light Blue
    "#803E75",  # Strong Purple
    "#FF6800",  # Vivid Orange
    "#C10020",  # Vivid Red
    "#CEA262",  # Grayish Yellow
    "#817066",  # Medium Gray

    # The following don't work well for people with defective color vision
    "#007D34",  # Vivid Green
    "#F6768E",  # Strong Purplish Pink
    "#00538A",  # Strong Blue
    "#FF7A5C",  # Strong Yellowish Pink
    "#53377A",  # Strong Violet
    "#FF8E00",  # Vivid Orange Yellow
    "#B32851",  # Strong Purplish Red
    "#F4C800",  # Vivid Greenish Yellow
    "#7F180D",  # Strong Reddish Brown
    "#93AA00",  # Vivid Yellowish Green
    "#593315",  # Deep Yellowish Brown
    "#F13A13",  # Vivid Reddish Orange
    "#232C16",  # Dark Olive Green
]

DEFAULT_OPTIONS = {
    'height': '800px',
    'width': '100%',
    'interaction': {'hover': True},
}


def get_options(directed: bool, opts_args: dict = None, physics: bool = True):
    """ defines the default options for the visdcc-graph and adds the optional arguments if not None

    :param directed: indicates whether the graph has directed edges
     :type directed: bool
     :param opts_args: optional arguments for the graph visualization
     :type opts_args: dict
     :param physics: indicates whether simulation physics are on or off
     :type physics: bool
     :return: options for the visdcc-graph visualization
     :rtype: dict
     """
    opts = DEFAULT_OPTIONS.copy()
    if not physics:
        opts['physics'] = {'enabled': False}
    else:
        if opts_args == "small":
            opts['physics'] = {'enabled': True}
        elif opts_args is not None:
            opts.update(opts_args)
        else:
            opts['physics'] = {'stabilization': {'enabled': True, 'iterations': 50},
                               'timestep': 0.6,
                               'minVelocity': 5,
                               'maxVelocity': 250,
                               'barnesHut': {
                                   'theta': 1,
                                   'gravitationalConstant': -100000,
                                   'centralGravity': 0.3,
                                   'springLength': 200,
                                   'springConstant': 0.01,
                                   'damping': 0.09,
                                   'avoidOverlap': 0}}

    opts['edges'] = {'arrows': {'to': directed}, 'font': {'size': 15}}

    return opts


def get_distinct_colors(n: int, for_nodes=True):
    """ return distinct colors, with two options to get different color schemes (for edges and nodes)

    :param n: number of distinct colors required
     :type n: int
     :param for_nodes: indicates whether nodes or edges will be colored
     :type for_nodes: bool
     :return: list of colors
     :rtype: list[str]
    """
    if for_nodes:
        return KELLY_COLORS_HEX[:n]
    else:
        return KELLY_COLORS_HEX[2:(n + 2)]


def create_color_legend(text: str, color: str):
    """ creates individual row for the color legend

    :param text: text to appear in a row of the legend
     :type text: str
     :param color: color-code which will be the background color of the row
     :type color: str
     :return: html-element of the rwo of the legend
     :rtype: html.Div
    """
    return html.Div(text, style={'padding-left': '10px', 'width': '200px', 'background-color': color})


def create_info_text(text: str):
    """ creates the info text as html-element

    :param text: text to be shown in info popover
     :type text: str
     :return: html-element of info text in popover
     :rtype: html.Div
    """
    return create_row([
        html.Div(text, style={'padding-left': '10px'}),
    ])


def fetch_flex_row_style():
    return {'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'align-items': 'center'}


def create_row(children, style=None):
    if style is None:
        style = fetch_flex_row_style()
    return dbc.Row(children,
                   style=style,
                   className="column flex-display")


# forms for layout
search_form = dbc.FormGroup([
    dbc.Input(type="search", id="search_graph",
              placeholder="Search node or edge in graph..."),
    dbc.FormText(
        "Show the node or edge you are looking for",
        color="secondary",
    )
])

selected_edge_form = dbc.FormGroup([
    dbc.FormText(
        id='edge-selection',
        color="secondary",
    ),
])

a_box_dp_form = dbc.FormGroup([
    dbc.FormText(
        id='node-selection',
        color="secondary",
    ),
])

filter_node_form = dbc.FormGroup([
    # dbc.Label("Filter nodes", html_for="filter_nodes"),
    create_row([
        dbc.Button("Add", id="add_to_query_button",
                   outline=True, color="secondary", size="sm"),
        daq.BooleanSwitch(id='add_node_edge_to_query_button', on=False, color="#FFB300",
                          label="Select Edge/Node", labelPosition="top"),
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    dbc.Textarea(id="filter_nodes", placeholder="Enter SPARQL-query here..."),
    create_row([
        dcc.Dropdown(
            id='sparql-keywords-dropdown',
            options=[
                {'label': 'Prefix', 'value': 'PREFIX'},
                {'label': 'Count as', 'value': 'COUNT ( ?[...] ) AS'},
                {'label': 'Ask', 'value': 'ASK'},
                {'label': 'Describe', 'value': 'DESCRIBE'},
                {'label': 'Select', 'value': 'SELECT'},
                {'label': 'Where', 'value': 'WHERE'},
                {'label': 'Order', 'value': 'ORDER BY'},
                {'label': 'Group', 'value': 'GROUP BY'},
                {'label': 'Limit', 'value': 'LIMIT'},
                {'label': 'Union', 'value': 'UNION'},
                {'label': 'Filter', 'value': 'FILTER'},
                {'label': 'Bind', 'value': 'BIND'},
                {'label': 'Distinct', 'value': 'DISTINCT'},
                {'label': 'Having', 'value': 'HAVING'},
                {'label': 'Filter Exists', 'value': 'FILTER EXISTS'},
                {'label': 'Filter not Exists', 'value': 'FILTER NOT EXISTS'},
                {'label': 'Values', 'value': 'VALUES'}
            ],
            placeholder="Keywords",
            style={'width': '102px'},
        ),
        dcc.Dropdown(
            id='sparql-variables-dropdown',
            options=[
                {'label': 'X', 'value': '?x'},
                {'label': 'Y', 'value': '?y'},
                {'label': 'Z', 'value': '?z'}
            ],
            placeholder="Variables",
            style={'width': '97px'},
        ),
        dcc.Dropdown(
            id='sparql-syntax-dropdown',
            options=[
                {'label': '{', 'value': '{'},
                {'label': '}', 'value': '}'},
                {'label': '(', 'value': '('},
                {'label': ')', 'value': ')'},
                {'label': '.', 'value': '.'},
                {'label': 'rdf', 'value': 'rdf:'},
                {'label': 'rdfs', 'value': 'rdfs:'},
                {'label': 'owl', 'value': 'owl:'},
                {'label': 'owlready', 'value': 'owlready:'},
                {'label': 'xsd', 'value': 'xsd:'},
                {'label': 'obo', 'value': 'obo:'},
                {'label': 'type', 'value': 'rdf:type'},
                {'label': 'subClassOf', 'value': 'rdfs:subClassOf'},
                {'label': 'label', 'value': 'rdfs:label'},
                {'label': 'min', 'value': 'min'},
                {'label': 'max', 'value': 'max'},
                {'label': 'descended', 'value': 'desc'},
            ],
            placeholder="Symbols",
            style={'width': '81px'},
        )
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    html.Hr(className="my-2"),
    html.H6("SPARQL Query to evaluate:"),
    html.Div(id='select-sparql', style={'whiteSpace': 'pre-line'}),
    html.Hr(className="my-2"),
    create_row([
        dbc.Button("Delete", id="delete_query_button",
                   outline=True, color="secondary", size="sm"),
        dbc.Button("Clear", id="clear_query_button",
                   outline=True, color="secondary", size="sm"),
        dbc.Button("Evaluate Query", id="evaluate_query_button",
                   outline=True, color="secondary", size="sm"),
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    dbc.FormText(
        html.P([
            "Filter graph data by using ",
            html.A("SPARQL Query syntax",
                   href="https://www.w3.org/TR/sparql11-query/#grammar"),
        ]),
        color="secondary",
    ),
])

sparql_template_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='sparql_template_dropdown',
                options=[
                    {'label': 'Count Number of owl-Classes',
                        'value': 'template_1.sparql'},
                    {'label': 'Count Number of Instances of a Class',
                        'value': 'template_4.sparql'},
                    {'label': 'Ask for Instance with Property',
                        'value': 'template_12.sparql'},
                    {'label': 'Describe an Instance',
                        'value': 'template_13.sparql'},
                    {'label': 'Select Min and Max of Data Property',
                        'value': 'template_8.sparql'},
                    {'label': 'Select Subclasses of a Class',
                        'value': 'template_10.sparql'},
                    {'label': 'Select Instances with specific Property',
                        'value': 'template_2.sparql'},
                    {'label': 'Select Instances and Property Range',
                        'value': 'template_5.sparql'},
                    {'label': 'Select Instances and specific Property Range',
                        'value': 'template_6.sparql'},
                    {'label': 'Select Instances with various Properties',
                        'value': 'template_7.sparql'},
                    {'label': 'Select Instances that unite two Classes',
                        'value': 'template_11.sparql'},
                    {'label': 'Select Grouped and Ordered Properties',
                        'value': 'template_9.sparql'},
                    {'label': 'Construct Instances with Properties',
                        'value': 'template_15.sparql'},
                    {'label': 'Construct Instances with specific Properties',
                        'value': 'template_14.sparql'},
                ],
                placeholder="Standard Templates",
                style={'width': '100%'}),
            dcc.Dropdown(
                id='inconsistency_template_dropdown',
                options=[
                    {'label': 'Inconsistency Query Template 1',
                        'value': 'template_3.sparql'},
                    {'label': 'Inconsistency Query Template 2',
                        'value': 'template_16.sparql'},
                    {'label': 'Inconsistency Query Template 3',
                        'value': 'template_17.sparql'},
                    {'label': 'Inconsistency Query Template 4',
                        'value': 'template_18.sparql'},
                    {'label': 'Inconsistency Query Template 5',
                        'value': 'template_19.sparql'},
                    {'label': 'Inconsistency Query Template 6',
                        'value': 'template_20.sparql'},
                ],
                placeholder="Inconsistency Templates",
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
            'justify-content': 'space-between'}),
        color="secondary",
    ),
])

sparql_library_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='sparql_library_dropdown',
                options=[
                    {'label': 'Query scenario', 'value': 'scenario_query.sparql'},
                    {'label': 'Query Scenario Info',
                        'value': 'scenario_info_query.sparql'},
                    {'label': 'Test', 'value': 'test.sparql'}
                ],
                placeholder="Consistency Checks",
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
            'justify-content': 'space-between'}),
        color="secondary",
    ),
])

scenario_select_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='scenario_select_dropdown',
                options=[
                    {'label': 'xPPU_Sc0'+str(i), 'value': 'xPPU_Sc0'+str(i)} for i in range(0, 9)],
                placeholder='Select Scenario',
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
            'justify-content': 'space-between'}
        ), color='primary'
    )])

terminology = ['Owl:Thing', 'information_source', 'document', 'document_info', 'version',
               'plant_info', 'Clamp', 'Component', 'Description', 'Resource', 'Type', 'Position',
               'model', 'plc', 'action', 'function_block', 'sysml', 'research_plant', 'plant_process',
               'assembly_process', 'logistics_process', 'manufacturing_process', 'plant_product',
               'plant_resource', 'actuator', 'Motor', 'Valve', 'sensor', 'MicroSwitch', 'ReedSwitch', 'Vacuum_Switch', 'Scenario']
terminology_select_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='terminology_select_dropdown',
                options=[{'label': value, 'value': value}
                         for value in terminology],
                placeholder='Select Termonology',
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
            'justify-content': 'space-between'}
        ), color='primary'
    )])


def get_select_form_layout(form_id: str, options: list, label: str, description: str):
    """ creates a select (dropdown) form with provides details

    :param form_id: id of the form
     :type form_id: str
     :param options: options to show in dropdown
     :type options: list
     :param label: label of the select dropdown bar
     :type label: list
     :param description: long text detail of the setting
     :type description: str
     :return: dbc-element of the form
     :rtype: dbc.FormGroup
    """
    if len(options) > 1:
        return dbc.FormGroup([
            dbc.InputGroup([
                dbc.InputGroupAddon(label, addon_type="append"),
                dbc.RadioItems(id=form_id,
                               options=options, value=options[1].get('value')
                               ), ]),
            dbc.FormText(description, color="secondary", ), ])
    return dbc.FormGroup([
        dbc.InputGroup([
            dbc.InputGroupAddon(label, addon_type="append"),
            dbc.RadioItems(id=form_id,
                           options=options
                           ), ]),
        dbc.FormText(description, color="secondary", ), ])


def get_categorical_features(df_: pd.DataFrame, unique_limit: int = 20, blacklist_features: list[str] = None):
    """ identify categorical features for edge or node data and return their names
    NOTE: Additional logics: (1) cardinality should be within `unique_limit`, (2) remove blacklist_features

    :param df_: DataFrame from which the features are extracted
     :type df_: pd.DataFrame
     :param unique_limit: maximum of unique features
     :type unique_limit: int
     :param blacklist_features: list of features that will be excluded
     :type blacklist_features: list[str]
     :return: list of categorical features
     :rtype: list[str]
    """
    # identify the rel cols + None
    if blacklist_features is None:
        blacklist_features = ['shape', 'label', 'id']
    cat_features = ['None'] + df_.columns[
        (df_.dtypes == 'object') & (df_.apply(pd.Series.nunique) <= unique_limit)].tolist()
    # remove irrelevant cols
    try:
        for col in blacklist_features:
            cat_features.remove(col)
    except ValueError:
        pass
    return cat_features


def get_numerical_features(df_: pd.DataFrame):
    """ identify numerical features for edge or node data and return their names

    :param df_: DataFrame from which the features are extracted
     :type df_: pd.DataFrame
     :return: list of numerical features
     :rtype: list[str]
    """
    # supported numerical cols
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    # identify numerical features
    numeric_features = ['None'] + \
        df_.select_dtypes(include=numerics).columns.tolist()
    # remove blacklist cols (for nodes)
    try:
        numeric_features.remove('size')
    except ValueError:
        pass
    try:
        numeric_features.remove('width')
    except ValueError:
        pass
    # return
    return numeric_features


def get_app_layout(graph_data: dict, onto: OntoEditor, color_legends: list = None,
                   directed: bool = False, vis_opts: dict = None, abox: bool = False):
    """ create and return the layout of the app

    :param graph_data: network data in format of visdcc
     :type graph_data: dict
     :param onto: ontology
     :type onto: OntoEditor
     :param color_legends: list of legend elements
     :type color_legends: list
     :param directed: indicates whether the graph is directed
     :type directed: bool
     :param vis_opts: additional visualization options to pass to the visdcc-Network options
     :type vis_opts: dict
     :param abox: indicates whether A-Boxes are visualized
     :type abox: bool
     :return: html-element of the layout
     :rtype: html.Div
    """
    # Step 1-2: find categorical features of nodes and edges
    if color_legends is None:
        color_legends = []
    cat_node_features = get_categorical_features(pd.DataFrame(graph_data['nodes']),
                                                 20, ['shape', 'label', 'id', 'title', 'color']) 
    cat_edge_features = get_categorical_features(
        pd.DataFrame(graph_data['edges']).drop(
            columns=['color', 'from', 'to', 'id', 'arrows']), 20,
        ['color', 'from', 'to', 'id'])
    # Step 3-4: Get numerical features of nodes and edges
    num_node_features = get_numerical_features(
        pd.DataFrame(graph_data['nodes']))
    num_edge_features = get_numerical_features(
        pd.DataFrame(graph_data['edges']))
    # Step 5: create and return the layout
    layout_with_abox = html.Div([
        create_row(html.H2(children="SPARQL Query Viz")),  # Title
        create_row(html.H3(children=onto.onto.name)),  # Subtitle
        create_row([
            dbc.Col([
                # setting panel
                dbc.Form([
                    # ---- search section ----
                    create_row([
                        html.H6("Search"),
                        dbc.Button("Un-/Freeze", id="freeze-physics", outline=True,
                                   color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    html.Hr(className="my-2"),
                    search_form,

                    # ---- edge selection section ----
                    create_row([
                        html.H6("Selected Edge"),
                        dbc.Button("Hide/Show", id="edge-selection-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        selected_edge_form,
                        html.Hr(className="my-2"),
                    ], id="edge-selection-show-toggle", is_open=False),

                    # ---- abox data-properties section ----
                    create_row([
                        html.H6("A-Box Data-Properties"),
                        dbc.Button("Hide/Show", id="abox-dp-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        a_box_dp_form,
                        html.Hr(className="my-2"),
                    ], id="abox-dp-show-toggle", is_open=False),

                    #! START ---------- Select Scenanrio
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        html.H6('Select Scenario'),
                        scenario_select_form,
                        terminology_select_form,
                        dbc.Button("Select", id="select_button", outline=True, color="primary",
                                   size="sm"),
                        html.Hr(className="my-2"),
                        html.Div(id='test-text', children='')
                    ], id="scenario-show-toggle", is_open=True),

                    # '''  create_row([
                    #      html.H6("Select Terminology"),
                   #     dbc.Button("Hide/Show", id="terminology-show-toggle-button", outline=True, color="secondary",size="sm"),
                    # ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                   #        'justify-content': 'space-between'}),
                   #   dbc.Collapse([
                   #      terminology_select_form,
                   #     html.Hr(className="my-2"),
                    # ], id="terminology-show-toggle", is_open=True), '''

                    #! END ------------ Select Scenario
                    # ---- SPARQL Template section ----
                    create_row([
                        html.H6("SPARQL Templates"),
                        dbc.Button("Hide/Show", id="template-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        sparql_template_form,
                        html.Hr(className="my-2"),
                    ], id="template-show-toggle", is_open=False),

                    # ---- SPARQL Library section ----
                    create_row([
                        html.H6("SPARQL Library"),
                        dbc.Button("Hide/Show", id="library-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        sparql_library_form,
                        html.Hr(className="my-2"),
                    ], id="library-show-toggle", is_open=False),

                    # ---- SPARQL Query section ----
                    create_row([
                        html.H6("SPARQL Query"),
                        dbc.Button("Hide/Show", id="filter-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                        dbc.Button("Info", id="info-sparql-query-button",
                                   outline=True, color="info", size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Popover(
                        html.Div("To compose a SPARQL query, use the syntax provided in the dropdown-menus or "
                                 "write your own queries into the input text field and click the Add-button. "
                                 "To insert graph elements into the query, toggle the Select Edge/Node-button"
                                 " and click on the element you like to add. To evaluate the query click the "
                                 "evaluate-button."),
                        id="info-sparql-popup", is_open=False,
                        target="info-sparql-query-button", style={'padding-left': '10px', 'width': '230px'}
                    ),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        filter_node_form,
                    ], id="filter-show-toggle", is_open=False),

                    # ---- SPARQL Result section ----
                    create_row([
                        html.H6("SPARQL Result"),
                        dbc.Button("Hide/Show", id="result-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        dcc.Slider(
                            id='result-level-slider',
                            min=0,
                            max=4,
                            step=1,
                            value=1,
                            marks={
                                0: '0',
                                1: '1',
                                2: '2',
                                3: '3',
                                4: '4'
                            },
                        ),
                        html.Div(id='textarea-result-output',
                                 style={'whiteSpace': 'pre-line'}),
                        html.Hr(className="my-2"),
                    ], id="result-show-toggle", is_open=False),

                    # ---- SPARQL History section ----
                    create_row([
                        html.H6("SPARQL History"),
                        dbc.Button("Hide/Show", id="history-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        dcc.Slider(
                            id='query-history-length-slider',
                            min=1,
                            max=5,
                            step=1,
                            value=3,
                            marks={
                                1: '1',
                                2: '2',
                                3: '3',
                                4: '4',
                                5: '5'
                            },
                        ),
                        html.Div(id='sparql_query_history', style={
                                 'whiteSpace': 'pre-line'}),
                        html.Hr(className="my-2"),
                        dbc.Button("Clear", id="clear-query-history-button", outline=True, color="secondary",
                                   size="sm"),
                    ], id="history-show-toggle", is_open=False),

                    # ---- color section ----
                    create_row([
                        html.H6("Color"),  # heading
                        html.Div([
                            dbc.Button("Hide/Show", id="color-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),  # legend
                            dbc.Button("Legends", id="color-legend-toggle",
                                       outline=True, color="secondary", size="sm"),
                            # legend
                        ]),
                        # add the legends popup
                        dbc.Popover(
                            children=color_legends,
                            id="color-legend-popup", is_open=False,
                            target="color-legend-toggle"
                        ),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        get_select_form_layout(
                            form_id='color_nodes',
                            options=[{'label': opt, 'value': opt}
                                     for opt in cat_node_features],
                            label='Color nodes by',
                            description='Select the categorical node property to color nodes by'
                        ),
                        get_select_form_layout(
                            form_id='color_edges',
                            options=[{'label': opt, 'value': opt}
                                     for opt in cat_edge_features],
                            label='Color edges by',
                            description='Select the categorical edge property to color edges by'
                        ),
                    ], id="color-show-toggle", is_open=False),

                    # ---- size section ----
                    create_row([
                        html.H6("Size"),  # heading
                        dbc.Button("Hide/Show", id="size-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        get_select_form_layout(
                            form_id='size_nodes',
                            options=[{'label': opt, 'value': opt}
                                     for opt in num_node_features],
                            label='Size nodes by',
                            description='Select the numerical node property to size nodes by'
                        ),
                        get_select_form_layout(
                            form_id='size_edges',
                            options=[{'label': opt, 'value': opt}
                                     for opt in num_edge_features],
                            label='Size edges by',
                            description='Select the numerical edge property to size edges by'
                        ),
                    ], id="size-show-toggle", is_open=False),

                   ], className="card", style={'padding': '5px', 'background': '#e5e5e5'}),
            ], width=3, style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}, align="start"),
            # graph
            dbc.Col(
                visdcc.Network(
                    id='graph',
                    data=graph_data,
                    selection={'nodes': [], 'edges': []},
                    options=get_options(directed, vis_opts)),
                width=9, align="start")])
    ])
    if abox:
        logging.info(
            "returning app-layout with section for A-Box Data-Properties")
        return layout_with_abox
    logging.info("returning standard app-layout")
    return html.Div([
        create_row(html.H2(children="SPARQL Query Viz")),  # Title
        create_row(html.H3(children=onto.onto.name)),  # Subtitle
        create_row([
            dbc.Col([
                # setting panel
                dbc.Form([
                    # ---- search section ----
                    create_row([
                        html.H6("Search"),
                        dbc.Button("Un-/Freeze", id="freeze-physics", outline=True,
                                   color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    html.Hr(className="my-2"),
                    search_form,

                    # ---- edge selection section ----
                    create_row([
                        html.H6("Selected Edge"),
                        dbc.Button("Hide/Show", id="edge-selection-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        selected_edge_form,
                        html.Hr(className="my-2"),
                    ], id="edge-selection-show-toggle", is_open=False),

                    # ---- SPARQL Template section ----
                    create_row([
                        html.H6("SPARQL Templates"),
                        dbc.Button("Hide/Show", id="template-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        sparql_template_form,
                        html.Hr(className="my-2"),
                    ], id="template-show-toggle", is_open=False),

                    # ---- SPARQL Library section ----
                    create_row([
                        html.H6("SPARQL Library"),
                        dbc.Button("Hide/Show", id="library-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        sparql_library_form,
                        html.Hr(className="my-2"),
                    ], id="library-show-toggle", is_open=False),
                    #! --------------------------
                    create_row([
                        html.H6("Select Scenario"),
                        dbc.Button("Hide/Show", id="scenario-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        scenario_select_form,
                        html.Hr(className="my-2"),
                    ], id="scenario-show-toggle", is_open=False),

                    # ---- SPARQL Query section ----
                    create_row([
                        html.H6("SPARQL Query"),
                        dbc.Button("Hide/Show", id="filter-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                        dbc.Button("Info", id="info-sparql-query-button",
                                   outline=True, color="info", size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Popover(
                        html.Div("To compose a SPARQL query, use the syntax provided in the dropdown-menus or "
                                 "write your own queries into the input text field and click the Add-button. "
                                 "To insert graph elements into the query, toggle the Select Edge/Node-button"
                                 " and click on the element you like to add. To evaluate the query click the "
                                 "evaluate-button."),
                        id="info-sparql-popup", is_open=False,
                        target="info-sparql-query-button", style={'padding-left': '10px', 'width': '230px'}
                    ),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        filter_node_form,
                    ], id="filter-show-toggle", is_open=False),

                    # ---- SPARQL Result section ----
                    create_row([
                        html.H6("SPARQL Result"),
                        dbc.Button("Hide/Show", id="result-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        dcc.Slider(
                            id='result-level-slider',
                            min=0,
                            max=4,
                            step=1,
                            value=1,
                            marks={
                                0: '0',
                                1: '1',
                                2: '2',
                                3: '3',
                                4: '4'
                            },
                        ),
                        html.Div(id='textarea-result-output',
                                 style={'whiteSpace': 'pre-line'}),
                        html.Hr(className="my-2"),
                    ], id="result-show-toggle", is_open=False),

                    # ---- SPARQL History section ----
                    create_row([
                        html.H6("SPARQL History"),
                        dbc.Button("Hide/Show", id="history-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        dcc.Slider(
                            id='query-history-length-slider',
                            min=1,
                            max=5,
                            step=1,
                            value=3,
                            marks={
                                1: '1',
                                2: '2',
                                3: '3',
                                4: '4',
                                5: '5'
                            },
                        ),
                        html.Div(id='sparql_query_history', style={
                                 'whiteSpace': 'pre-line'}),
                        html.Hr(className="my-2"),
                        dbc.Button("Clear", id="clear-query-history-button", outline=True, color="secondary",
                                   size="sm"),
                    ], id="history-show-toggle", is_open=False),

                    # ---- color section ----
                    create_row([
                        html.H6("Color"),  # heading
                        html.Div([
                            dbc.Button("Hide/Show", id="color-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),  # legend
                            dbc.Button("Legends", id="color-legend-toggle",
                                       outline=True, color="secondary", size="sm"),
                            # legend
                        ]),
                        # add the legends popup
                        dbc.Popover(
                            children=color_legends,
                            id="color-legend-popup", is_open=False,
                            target="color-legend-toggle"
                        ),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        get_select_form_layout(
                            form_id='color_nodes',
                            options=[{'label': opt, 'value': opt}
                                     for opt in cat_node_features],
                            label='Color nodes by',
                            description='Select the categorical node property to color nodes by'
                        ),
                        get_select_form_layout(
                            form_id='color_edges',
                            options=[{'label': opt, 'value': opt}
                                     for opt in cat_edge_features],
                            label='Color edges by',
                            description='Select the categorical edge property to color edges by'
                        ),
                    ], id="color-show-toggle", is_open=False),

                    # ---- size section ----
                    create_row([
                        html.H6("Size"),  # heading
                        dbc.Button("Hide/Show", id="size-show-toggle-button", outline=True, color="secondary",
                                   size="sm"),
                    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                        'justify-content': 'space-between'}),
                    dbc.Collapse([
                        html.Hr(className="my-2"),
                        get_select_form_layout(
                            form_id='size_nodes',
                            options=[{'label': opt, 'value': opt}
                                     for opt in num_node_features],
                            label='Size nodes by',
                            description='Select the numerical node property to size nodes by'
                        ),
                        get_select_form_layout(
                            form_id='size_edges',
                            options=[{'label': opt, 'value': opt}
                                     for opt in num_edge_features],
                            label='Size edges by',
                            description='Select the numerical edge property to size edges by'
                        ),
                    ], id="size-show-toggle", is_open=False),

                ], className="card", style={'padding': '5px', 'background': '#e5e5e5'}),
            ], width=3, style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}, align="start"),
            # graph
            dbc.Col(
                visdcc.Network(
                    id='graph',
                    data=graph_data,
                    selection={'nodes': [], 'edges': []},
                    options=get_options(directed, vis_opts)),
                width=9, align="start")])
    ])
