import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
from utils_func import Utils
import plotly.express as px
import plotly.graph_objs as go
from statsmodels.tsa.seasonal import seasonal_decompose
from urllib.request import urlopen
import json
import geopandas
import ssl
from flask_caching import Cache
import time


ssl._create_default_https_context = ssl._create_unverified_context

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Corse Matin Analysis"
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

TIMEOUT = 30
utils = Utils()
@cache.memoize(timeout=TIMEOUT)
def get_initial_datas():
    #BASE
    tic = time.perf_counter()
    df = pd.read_csv("./data/2015 - 2020.csv")
    df["Months_char"] = df["Months"]
    df["Months"] = utils.months_to_number_dataset(df["Months"])
    df["Day"] = 1
    df["Date"] = pd.to_datetime(df[["Months", "Years", "Day"]])
    region = geopandas.read_file('./data/regions.geojson')
    region.rename({'nom': 'd_geo_region'}, axis=1, inplace=True)
    region = region[region['d_geo_region'].apply(lambda g : utils.is_in_metro(g))]
    region['d_geo_region'] = region['d_geo_region'].apply(lambda g : utils.format_region(g))
    toc = time.perf_counter()
    app.logger.info(f"get_initial_datas finished in {toc - tic:0.4f} seconds")
    return [df, region]

initial_datas = get_initial_datas()
df = initial_datas[0]
region = initial_datas[1]


@cache.memoize(timeout=TIMEOUT)
def get_datas(filtered_data):
    #non_agg_chart
    df_non_agg_chart = filtered_data.copy()
    df_non_agg_chart = df_non_agg_chart.groupby("Date").sum()["m_visits"]
    df_non_agg_chart = df_non_agg_chart.to_frame()

    #agg_chart
    df_agg_chart = filtered_data.copy()
    df_agg_chart = df_agg_chart.groupby(['Months_char']).sum()["m_visits"].sort_index(key=utils.sorter)

    #staked_line
    df_staked_line = filtered_data.copy()
    df_staked_line = df_staked_line.groupby(["Months_char", "Years"]).sum()["m_visits"].unstack().sort_index(key=utils.sorter)

    #timeseries
    df_timeseries = df_non_agg_chart
    decomposed = seasonal_decompose(df_timeseries["m_visits"], model='additive')
    trend = decomposed.trend
    seasonal = decomposed.seasonal

    #map
    df_map = filtered_data.copy()
    df_map['d_geo_region'] = df_map['d_geo_region'].apply(lambda g : utils.format_region(g))
    
    merged_map = geopandas.pd.merge(region, 
                  df_map,
                  on='d_geo_region')
    #merged_map = region.set_index('d_geo_region').join(df_map.set_index('d_geo_region'))

    merged_map.to_file("./data/regions.json", driver='GeoJSON')
    with open('./data/regions.json') as response:
        regions = json.load(response)
    
    #pie chart
    df_pie_chart = filtered_data.copy()
    df_pie_chart["d_geo_region"] = df_pie_chart["d_geo_region"].apply(lambda g : utils.format_region(g))
    df_pie_chart["d_geo_region"] = df_pie_chart["d_geo_region"].apply(utils.categorize_region)
    df_pie_chart_sum = df_pie_chart.groupby(["d_geo_region"]).sum()["m_visits"]

    #mutiple bar
    df_multiple_bar_chart = df_pie_chart
    df_multiple_bar_chart = df_multiple_bar_chart.groupby(["Years", "d_geo_region"]).sum()["m_visits"].groupby(level=0).apply(
        lambda x: 100 * x / x.sum()
    ).unstack()

    return {
        "df_non_agg_chart": df_non_agg_chart,
        "df_agg_chart": df_agg_chart,
        "df_staked_line": df_staked_line,
        "df_timeseries": df_timeseries,
        "trend": trend,
        "seasonal": seasonal,
        "map": regions,
        "merged_map": merged_map,
        "df_pie_chart_sum": df_pie_chart_sum,
        "df_multiple_bar_chart":df_multiple_bar_chart
        }

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.Img(src="https://d2p1ubzgqn8tkf.cloudfront.net/storage/logo.svg"),
                html.H1(
                    children="📈 Dashboard Corse Matin", className="header-title"
                ),
                html.P(
                    children="Analyses et prédiction sur l'audience"
                    " de tout les sites"
                    " entre 2015 and 2020",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            display_format='MM/Y',
                            min_date_allowed=df.Date.min().date(),
                            max_date_allowed=df.Date.max().date(),
                            start_date=df.Date.min().date(),
                            end_date=df.Date.max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        dcc.Loading(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children=dcc.Graph(
                                id="non-agg-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="agg-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="stacked-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="trend-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=[
                                html.Span(
                                    className="seasonal-label",
                                    children= "Saison estival",
                                ),
                                dcc.Graph(
                                    id="seasonal-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="map-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="pie-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="multiple-chart_bar-chart",
                                config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        
                    ],
                    className="wrapper",
                ),
                
            ],
            color="#e74c3c", type="dot", fullscreen= True
        ),
    ]
)


@app.callback(
    [
        Output("non-agg-chart", "figure"),
        Output("agg-chart", "figure"),
        Output("stacked-chart", "figure"),
        Output("trend-chart", "figure"),
        Output("seasonal-chart", "figure"),
        Output("map-chart", "figure"),
        Output("pie-chart", "figure"),
        Output("multiple-chart_bar-chart", "figure")
        
    ],
    [
        #Input("region-filter", "value"),
        #Input("type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(start_date, end_date):
    tic = time.perf_counter()
    mask = (
        #(data.region == region)
        #& (data.type == avocado_type)
        (df.Date >= start_date)
        & (df.Date <= end_date)
    )
    filtered_data = df.loc[mask, :]
    datas = get_datas(filtered_data)

    non_agg_chart_figure = {
        "data": [
            {
                "x": datas["df_non_agg_chart"].index,
                "y": datas["df_non_agg_chart"]["m_visits"],
                "type": "lines",
                "hovertemplate": "%{y:.2f}"
                                    "<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Nombre de visites de 2015 à 2020 sur tout les sites",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {
                'title':'Années',
                "fixedrange": True
            },
            "yaxis": {
                "fixedrange": True,
                'title':'Visite en Millions'
            },
            "colorway": ["#e74c3c"],
        }
    }
    
    agg_chart_figure = {
        "data": [
            {
                "x": datas["df_agg_chart"].index.values,
                "y": datas["df_agg_chart"].values,
                "type": "lines",
                "hovertemplate": "%{y:.2f}"
                                    "<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Nombre de visite par mois agréger de 2015 à 2020",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {
                'title':'Mois',
                'type':'category'
            },
            "yaxis": {
                "fixedrange": True,
                'title':'Visite en Millions'
            },
            "colorway": ["#e74c3c"]
        }
    }
    
    dict_of_fig = dict({
    "layout": {"title": {
                "text": "Nombre de visite par mois de 2015 à 2020",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {
                'title':'Mois',
                'type':'category'
            },
            "yaxis": {
                "fixedrange": True,
                'title':'Visite en Millions'
            },
            "plot_bgcolor" : 'rgb(253, 253, 253)'
        }
    })
    fig = go.Figure(dict_of_fig)
    for col in datas["df_staked_line"].columns:
        fig.add_trace(
            go.Scatter(
                x=datas["df_staked_line"].index.tolist(),
                y=datas["df_staked_line"][col].tolist(),
                name=str(col)
            )
        )
    fig.update_traces(mode='lines+markers')
    #fig.update_layout(plot_bgcolor='rgb(10,10,10)')

    stacked_chart_figure = fig
    
    trend_chart_figure = {
        "data": [
            {
                "x": datas["trend"].index,
                "y": datas["trend"].values,
                "type": "lines",
                "hovertemplate": "%{y:.2f}"
                                    "<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Tendance du nombre de visite 2015 à 2020",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {
                'title':'Années',
                "tickformat":"%Y"
            },
            "yaxis": {
                "fixedrange": True,
                'title':'Visite en Millions'
            },
            "colorway": ["#e74c3c"],
        }
    }
    
    def colored_year(months):
        shapes = []
        years = set([date.year for date in datas["df_timeseries"]["m_visits"].index])
        for i, year in enumerate(years):
            shapes.append(
                {
                    'type': 'rect',
                    'xref': 'x',
                    'yref': 'paper',
                    'x0': f'{year}-{months[0]}-01',
                    'y0': 0,
                    'x1': f'{year}-{months[1]}-01',
                    'y1': 1,
                    'fillcolor': '#f1c40f',
                    'opacity': 0.2,
                    'line': {
                        'width': 0,
                    }
                }
            )
        return shapes

    seasonal_chart_figure = {
        "data": [
            {
                "x": datas["seasonal"].index,
                "y": datas["seasonal"].values,
                "type": "lines",
                "hovertemplate": "%{y:.2f}"
                                    "<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Saisonalité du nombre de visite 2015 à 2020",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {
                'title':'Années',
                "tickformat":"%Y"
            },
            "yaxis": {
                "fixedrange": True,
                'title':'Visite en Millions'
            },
            "colorway": ["#e74c3c"],
            'shapes': colored_year([6,9])
        }
    }

    

    #df_map = px.data.election()
    #geojson = px.data.election_geojson()

    fig = px.choropleth(datas["merged_map"], geojson=datas["map"], color="m_visits",
                    locations="d_geo_region", featureidkey="properties.d_geo_region",
                    projection="mercator", color_continuous_scale="orrd", labels={"m_visits": "Nombres de visites"}
                   )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=600, title="Heatmap du nombre de visite en france métropolitaine")

    map_chart_figure = fig

 
    fig = px.pie(datas["df_pie_chart_sum"], values=datas["df_pie_chart_sum"].values, names=datas["df_pie_chart_sum"].index, title='Répartition des visites sur les régions de 2015 à 2020')
    pie_chart_figure = fig
    
    layout = go.Layout(
        barmode='stack',
        title="Part des visiteurs par localisation par années"
    )
    fig = go.Figure(layout=layout)
    for col in datas["df_multiple_bar_chart"].columns:
        fig.add_trace(
            go.Bar(
                x=datas["df_multiple_bar_chart"].index,
                y=datas["df_multiple_bar_chart"][col].values,
                name=str(col)
            )
        )
    multiple_pie_chart_bar_figure = fig
    toc = time.perf_counter()
    app.logger.info(f"Update finished in {toc - tic:0.4f} seconds")

    return\
        non_agg_chart_figure,\
        agg_chart_figure,\
        stacked_chart_figure,\
        trend_chart_figure,\
        seasonal_chart_figure,\
        map_chart_figure,\
        pie_chart_figure,\
        multiple_pie_chart_bar_figure


if __name__ == "__main__":
    app.run_server(debug=True)