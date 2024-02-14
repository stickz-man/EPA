import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import requests

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Parameter Analysis"),
    html.P("TO USE THE APP, CLICK ON 'LOAD DATA' TO LOAD DEFAULT DATA, THEN USE THE SEARCH BAR TO ADD PARAMETERS YOU WOULD LIKE TO ANALYSE"),
    html.Button('Load Data', id='load-button', n_clicks=0),
    dcc.Dropdown(id='params', multi=True),
    dcc.Graph(id='histogram')
])

@app.callback(
    [Output('params', 'options'), Output('params', 'value')],
    Input('load-button', 'n_clicks'),
    prevent_initial_call=True
)
def load_parameters(n_clicks):
    query_url = "https://services2.arcgis.com/sJvSsHKKEOKRemAr/arcgis/rest/services/EPAPittFinal/FeatureServer/0/query"
    params = {
        "where": "1=1",  # This fetches all records
        "f": "json",
        "outFields": "Parameter_Name,Arithmetic_Mean",
        "resultOffset": "0",
        "resultRecordCount": "1000",
    }

    response = requests.get(query_url, params=params)
    if response.status_code == 200:
        data = response.json()['features']
        df = pd.DataFrame([feature['attributes'] for feature in data])
        parameters = df['Parameter_Name'].unique()
        options = [{'label': param, 'value': param} for param in parameters]
        return options, parameters.tolist()[0:3]  # Return the first 3 parameters as default selection
    else:
        return [], []

@app.callback(
    Output('histogram', 'figure'),
    Input('params', 'value')
)
def update_histogram(selected_params):
    if not selected_params:
        return {}

    query_url = "https://services2.arcgis.com/sJvSsHKKEOKRemAr/arcgis/rest/services/EPAPittFinal/FeatureServer/0/query"
    params = {
        "where": f"Parameter_Name IN ({','.join([f"'{param}'" for param in selected_params])})",
        "f": "json",
        "outFields": "Parameter_Name,Arithmetic_Mean",
        "resultOffset": "0",
        "resultRecordCount": "1000",
    }

    response = requests.get(query_url, params=params)
    if response.status_code == 200:
        data = response.json()['features']
        df = pd.DataFrame([feature['attributes'] for feature in data])
        fig = px.histogram(df, x='Arithmetic_Mean', color='Parameter_Name', barmode='group')
        fig.update_layout(
            title="Histogram of Arithmetic Means for Selected Parameters",
            xaxis_title="Arithmetic Mean",
            yaxis_title="Count"
        )
        return fig
    else:
        return {}

if __name__ == '__main__':
    app.run_server(debug=True)
