from dash import dcc, html, Input, Output, State, callback, dcc
import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime as dt


app = dash.Dash(__name__)

# Setup for DatePickerRange component with an allowable date range
app.layout = html.Div([
    html.H1("Parameter Analysis"),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=dt(2019, 1, 1),
        max_date_allowed=dt(2022, 12, 31),
        start_date=dt(2019, 1, 1),
        end_date=dt(2022, 12, 31)
    ),
    dcc.Dropdown(id='params', multi=True),
    html.Button('Update Graph', id='update-graph-button', n_clicks=0),
    dcc.Graph(id='histogram')
])


def fetch_data_from_api(start_date, end_date):
    """Fetch and filter data from the ArcGIS REST API based on the selected date range."""
    query_url = "https://services2.arcgis.com/sJvSsHKKEOKRemAr/arcgis/rest/services/EPAPittFinal/FeatureServer/0/query"
    params = {
        "where": f"Date_Local >= DATE '{start_date.strftime('%Y-%m-%d')}' AND Date_Local <= DATE '{end_date.strftime('%Y-%m-%d')}'",
        "outFields": "*",
        "f": "json",
        "resultOffset": "0",
        "resultRecordCount": "2000",
    }

    response = requests.get(query_url, params=params)
    if response.status_code == 200:
        data = response.json()['features']
        df = pd.DataFrame([feature['attributes'] for feature in data])
        return df
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()


@app.callback(
    [Output('params', 'options'), Output('params', 'value')],
    [Input('update-graph-button', 'n_clicks')],
    [State('date-picker-range', 'start_date'), State('date-picker-range', 'end_date')]
)
def update_parameters_options(n_clicks, start_date, end_date):
    if n_clicks > 0:
        df = fetch_data_from_api(pd.to_datetime(start_date), pd.to_datetime(end_date))
        if not df.empty:
            parameters = df['Parameter_Name'].unique()
            options = [{'label': param, 'value': param} for param in parameters]
            return options, parameters.tolist()[0:3]
    return [], []


@app.callback(
    Output('histogram', 'figure'),
    [Input('update-graph-button', 'n_clicks')],
    [State('params', 'value'), State('date-picker-range', 'start_date'), State('date-picker-range', 'end_date')]
)
def update_histogram(n_clicks, selected_params, start_date, end_date):
    if n_clicks > 0 and selected_params:
        df = fetch_data_from_api(pd.to_datetime(start_date), pd.to_datetime(end_date))
        if not df.empty:
            filtered_df = df[df['Parameter_Name'].isin(selected_params)]
            fig = px.histogram(filtered_df, x='Arithmetic_Mean', color='Parameter_Name', barmode='group',
                               labels={'Arithmetic_Mean': 'Arithmetic Mean'},
                               title='Histogram of Arithmetic Means for Selected Parameters Over Time')
            return fig
    return go.Figure()


if __name__ == '__main__':
    app.run_server(debug=True)
