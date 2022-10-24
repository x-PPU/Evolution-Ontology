import logging
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
import visdcc
from dash import dcc, html
from ontor import OntoEditor

def fetch_flex_row_style():
    return {'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'align-items': 'center'}

def create_row(children, style=None):
    if style is None:
        style = fetch_flex_row_style()
    return dbc.Row(children,
                   style=style,
                   className="column flex-display")

scenario_select_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='scenario_select_dropdown',
                options=[
                    {'label': 'Scenario 1', 'value': 'scen1'},
                    {'label': 'Scenario 2', 'value': 'scen2'},
                    {'label': 'Scenario 3', 'value': 'scen3'}
                ],
                placeholder='Select Scenario',
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
            'justify-content': 'space-between'}
        ), color='primary'
    )])