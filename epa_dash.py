import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime as dt

app = dash.Dash(__name__)

# Define the style for the buttons
button_style = {
    'background-color': '#4CAF50',
    'color': 'white',
    'padding': '10px 24px',
    'margin': '10px 0',
    'border': 'none',
    'cursor': 'pointer',
}

app.layout = html.Div([
    html.H1("Pitt County Air quality Data Analysis"),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=dt(2019, 1, 1),
        max_date_allowed=dt(2022, 12, 31),
        start_date=dt(2021, 1, 1),
        end_date=dt(2021, 1, 31)
    ),
    dcc.Dropdown(id='params', multi=True),
    html.Button('Load Data', id='update-data-button', n_clicks=0, style=button_style),

    dcc.Tabs(id='tabs', children=[
        dcc.Tab(label='Plot', children=[
            dcc.Graph(id='histogram'),
        ]),
        dcc.Tab(label='Data', children=[
            dash_table.DataTable(id='data-table',
                                 style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                                 style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                                 ),
        ]),
    ])
])


def fetch_data_from_api(start_date, end_date):
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
    [Input('update-data-button', 'n_clicks')],
    [State('date-picker-range', 'start_date'), State('date-picker-range', 'end_date')]
)
def update_parameters_options(n_clicks, start_date, end_date):
    if n_clicks > 0:
        df = fetch_data_from_api(pd.to_datetime(start_date), pd.to_datetime(end_date))
        if not df.empty:
            parameters = df['Parameter_Name'].unique()
            options = [{'label': param, 'value': param} for param in parameters]
            return options, parameters.tolist()[:3]  # Select first 3 by default
    return [], []


@app.callback(
    Output('histogram', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    [Input('update-data-button', 'n_clicks')],
    [State('params', 'value'), State('date-picker-range', 'start_date'), State('date-picker-range', 'end_date')]
)
def update_content(n_clicks, selected_params, start_date, end_date):
    if n_clicks > 0 and selected_params:
        df = fetch_data_from_api(pd.to_datetime(start_date), pd.to_datetime(end_date))
        if not df.empty:
            filtered_df = df[df['Parameter_Name'].isin(selected_params)]
            fig = px.histogram(filtered_df, x='Arithmetic_Mean', color='Parameter_Name', barmode='group',
                               labels={'Arithmetic_Mean': 'Arithmetic Mean'},
                               title='Histogram of Arithmetic Means for Selected Parameters Over Time')
            columns = [{"name": i, "id": i} for i in filtered_df.columns]
            data = filtered_df.to_dict('records')
            return fig, data, columns
    return go.Figure(), [], []


if __name__ == '__main__':
    app.run_server(debug=True)
