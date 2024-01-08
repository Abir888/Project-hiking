# Libraries 

import pandas as pd 
import plotly.express as px
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dash_table import DataTable


# data cleaning
df = pd.read_csv("all_hiking_places.csv").iloc[:,1:]
df = df[~df["difficulty"].isnull()]

## split code of state from city name
df[["city", "code"]] = df['city'].str.split(',', n=1,expand=True)

## clean trail name from numbers and hastags & delete extra space in code

df["name"] = df['name'].str.replace('[^a-zA-Z\s]', '', regex=True).str.strip()
df["code"] = df["code"].str.strip()


## get usa data
i = df.loc[df['city'] == 'Konispol'].index[0]
world = df.loc[i:,:]
usa = df.loc[:i-1,:]
usa = usa[~usa["code"].isin(["D.C., DC", "Los Angeles, CA", "unknown"])]

## usa cities database 
usacities = pd.read_csv("uscities.csv")

## merge the two dataframe

dc = usa.merge(usacities [["city","state_id", "state_name","lat","lng"]], 
               left_on= ["code", "city"], right_on= ["state_id", "city"], how = "inner")
dc = dc[['name', 'state_id', 'state_name','city', 'lat', 'lng','length (km)', 'difficulty', 'review score',
       'number of reviews', 'trail url']]





app = dash.Dash(__name__)

# Define the layout with enhanced styling
app.layout = html.Div([
    #html.Img(src="/Users/ahajmi/Desktop/code/h.jpeg"), 
    html.H1("Hiking in USA", className="heading", style={'color': 'black', 'text-align': 'center', 'font-size': '3em', 'margin-top': '20px'}),

     # Container for the dropdowns
    html.Div([
        dcc.Dropdown(
            id="states-list",
            options=[
                
                {'label': state, 'value': state} for state in set(dc['state_name'])
            ],
            value=None,
            multi=False,
            style={'width': '30%', 'display': 'inline-block', 'margin-right': '10px', 'font-size': '0.8em'}  # Dropdown styling
        ),
        
        dcc.Dropdown(
            id="cities-list",
            options=[],
            multi=False,
            style={'width': '30%', 'display': 'inline-block', 'margin-right': '10px', 'font-size': '0.8em'}  # Dropdown styling
        ),
        
        dcc.Dropdown(
            id="difficulty-list",
            options=[
                
                {'label': difficulty, 'value': difficulty} for difficulty in set(dc['difficulty'])
            ],
            value=None,
            multi=False,
            style={'width': '30%', 'display': 'inline-block', 'font-size': '0.8em'}  # Dropdown styling
        ),
    ], style={'background-color': '#d3d3d3', 'padding': '20px', 'margin-top': '20px'}),  # Container styling

    # Graph
    dcc.Graph(
        id="usa_map",
        style={ 'margin': 'auto', 'marginTop': '20px', 'marginDown': '20px'}  # Center the graph
    ),
    
    
    # verical space
    html.Div(style={'height': '20px'}),

    # Table
    DataTable(
        id='trail-table',
        columns=[
            {'name': 'Trail Name', 'id': 'name'},
            {'name': 'State', 'id': 'state_name'},
            {'name': 'City', 'id': 'city'},
            {'name': 'Difficulty', 'id': 'difficulty'},
            {'name': 'Length (km)', 'id': 'length (km)'},
            {'name': 'Review Score', 'id': 'review score'},
            {'name': 'Number of reviews', 'id': 'number of reviews'},
            {'name': 'More info', 'id': 'trail url'}
        ],
        style_table={'height': '300px', 'overflowY': 'auto', 'margin': 'auto', 'font-family': 'Arial', 'font-size': '0.8em'}  # Center the table
    ),
], style={'margin': 'auto', 'width': '80%', 'background-color': '#f4f4f4'})  # Main container styling


   

# Callback to update the city dropdown based on selected state
@app.callback(
    Output("cities-list", "options"),
    [Input("states-list", "value")]
)
def update_city_dropdown(selected_state):
    if selected_state is None:
        return []  # No state selected, return empty options
    else:
        # Filter the data for the selected state
        cities_options = [{'label': city, 'value': city} for city in set(dc[dc["state_name"] == selected_state]['city'])]
        return cities_options

# Callback to update the graph based on selected state and city
@app.callback(
    [Output("usa_map", "figure"),
    Output("trail-table", "data")],
    [Input("states-list", "value"),
    Input("cities-list", "value"),
    Input("difficulty-list", "value")]
)
def update_graph(selected_state, selected_city, selected_difficulty):
    if selected_state is None:
        # No state selected, show whole USA data
        filtered_data = dc.copy()
    elif selected_city is None:
        # State selected but no city, show whole state data
        filtered_data = dc[dc["state_name"] == selected_state]
    else:
        # State and city selected, filter data accordingly
        filtered_data = dc[(dc["state_name"] == selected_state) & (dc["city"] == selected_city)]
        
    # Filter data based on selected difficulty
    if selected_difficulty is not None:
        filtered_data = filtered_data[filtered_data["difficulty"] == selected_difficulty]
    

    fig = px.scatter_mapbox(filtered_data, lat="lat", lon="lng", hover_name="city", hover_data=["state_name", "name"], color= "difficulty",
                        zoom=3, height=500)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=1.05, xanchor="left", x=0))
     
     # Prepare data for the table
    table_data = filtered_data[['name',  'state_name', "city", 'difficulty', 'length (km)',
        'review score', 'number of reviews', 'trail url']].to_dict('records')

    return fig, table_data

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)


