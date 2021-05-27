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
from dash_app import app
from drive import data_files


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
    df = pd.read_csv(data_files['2015 - 2020.csv'])
    df["Months_char"] = df["Months"]
    df["Months"] = utils.months_to_number_dataset(df["Months"])
    df["Day"] = 1
    df["Date"] = pd.to_datetime(df[["Months", "Years", "Day"]])
    region = geopandas.read_file('https://france-geojson.gregoiredavid.fr/repo/regions.geojson')
    region['d_geo_region'] = region['nom'].apply(lambda g : utils.format_region(g) if utils.is_in_metro(g) else None)
    region['geoids'] = region.index
    #print(region)
    #for i, feat in enumerate(region['features']):
      #f#eat['id'] = i
    #print("OK",region['features'][0])
    #regiondf = pd.DataFrame(data={
        # geoid must match county-shape-ids in json file (must start with 0 and increase with no missing one)
        #'geoids' :    [feat['id']                             for feat in region['features']],
        #"code" : [feat['properties'].get('code')                            for feat in region['features']],
        #'nom'  :    [utils.format_region(feat['properties'].get('nom')) if utils.is_in_metro(feat['properties'].get('nom')) else None for feat in region['features']],
        #'geometry' :    [feat['geometry']                             for feat in region['features']]
    #})
    #print(regiondf[])
    #with open(data_files['regions.json']) as json_file:
      #region = json.load(json_file)
    #region = geopandas.read_file(data_files['regions.geojson'])
    #region['d_geo_region'] = region['nom'].apply(lambda g : utils.format_region(g) if utils.is_in_metro(g) else None)

    toc = time.perf_counter()
    app.logger.info(f"get_initial_datas finished in {toc - tic:0.4f} seconds")
    return [df, region]

initial_datas = get_initial_datas()
df = initial_datas[0]
region = initial_datas[1]

@cache.memoize(timeout=TIMEOUT)
def get_datas(filtered_data, pathname):
  if pathname == "home":
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
      return {
        "df_non_agg_chart": df_non_agg_chart,
        "df_agg_chart": df_agg_chart,
        "df_staked_line": df_staked_line,
        "df_timeseries": df_timeseries,
        "trend": trend,
        "seasonal": seasonal
        }
  if pathname == "trafic-orifin":
      df_group_region = filtered_data.copy()
      df_group_region['d_geo_region'] = df_group_region['d_geo_region'].apply(lambda g : utils.format_region(g))
      #map
      df_map = df_group_region.copy()
      #df_map['d_geo_region'] = df_map['d_geo_region'].apply(lambda g : utils.format_region(g))
      merged_map = region.set_index('d_geo_region').join(df_map.set_index('d_geo_region'), how='inner')
      #print(merged_map.head(1))

      
      #pie chart
      df_pie_chart = df_group_region.copy()
      #df_pie_chart["d_geo_region"] = df_pie_chart["d_geo_region"].apply(lambda g : utils.format_region(g))
      df_pie_chart["d_geo_region"] = df_pie_chart["d_geo_region"].apply(utils.categorize_region)
      df_pie_chart_sum = df_pie_chart.groupby(["d_geo_region"]).sum()["m_visits"]

      #mutiple bar
      df_multiple_bar_chart = df_pie_chart
      df_multiple_bar_chart = df_multiple_bar_chart.groupby(["Years", "d_geo_region"]).sum()["m_visits"].groupby(level=0).apply(
          lambda x: 100 * x / x.sum()
      ).unstack()

      return {
          "map": region,
          "merged_map": merged_map,
          "df_pie_chart_sum": df_pie_chart_sum,
          "df_multiple_bar_chart":df_multiple_bar_chart
          }

@app.callback(
    [
        Output("non-agg-chart", "figure"),
        Output("agg-chart", "figure"),
        Output("stacked-chart", "figure"),
        Output("trend-chart", "figure"),
        Output("seasonal-chart", "figure")
        
    ],
    [
        #Input("region-filter", "value"),
        #Input("type-filter", "value"),
        Input('url', 'pathname'),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(pathname, start_date, end_date):
    print(pathname)
    default_color = "#e74c3c"
    default_theme = "gridon"

    tic = time.perf_counter()
    mask = (
        #(data.region == region)
        #& (data.type == avocado_type)
        (df.Date >= start_date)
        & (df.Date <= end_date)
    )
    filtered_data = df.loc[mask, :]
    datas = get_datas(filtered_data, "home")
    non_agg_chart_figure = px.line(
      datas["df_non_agg_chart"],
      x=datas["df_non_agg_chart"].index,
      y="m_visits",
      title='Nombre de visites de 2015 à 2020 sur tout les sites',
      labels={"m_visits": "Nombres de visites", "Date": "Années"},
      template=default_theme,
      color_discrete_sequence= [default_color]
    )

    agg_chart_figure = px.line(
      datas["df_agg_chart"],
      x=datas["df_agg_chart"].index,
      y=datas["df_agg_chart"].values,
      title='Nombre de visite par mois agréger de 2015 à 2020',
      labels={"y": "Nombres de visites", "Months_char": "Mois"},
      template=default_theme,
      color_discrete_sequence= [default_color]
    )
    
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
    trend_chart_figure = px.line(
      datas["trend"],
      x=datas["trend"].index,
      y=datas["trend"].values,
      title='Tendance du nombre de visite 2015 à 2020',
      labels={"y": "Visite en Millions", "Date": "Années"},
      template=default_theme,
      color_discrete_sequence= [default_color]
    )
    
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

    toc = time.perf_counter()
    app.logger.info(f"Update finished in {toc - tic:0.4f} seconds")

    return\
        non_agg_chart_figure,\
        agg_chart_figure,\
        stacked_chart_figure,\
        trend_chart_figure,\
        seasonal_chart_figure,\


@app.callback(
    [
        Output("map-chart", "figure"),
        Output("pie-chart", "figure"),
        Output("multiple-chart_bar-chart", "figure")
        
    ],
    [
        #Input("region-filter", "value"),
        #Input("type-filter", "value"),
        Input('url', 'pathname'),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(pathname, start_date, end_date):
    print(pathname)
    tic = time.perf_counter()
    mask = (
        #(data.region == region)
        #& (data.type == avocado_type)
        (df.Date >= start_date)
        & (df.Date <= end_date)
    )
    filtered_data = df.loc[mask, :]
    datas = get_datas(filtered_data, "trafic-orifin")
    print(datas["map"])
    fig = px.choropleth(datas["merged_map"], geojson=datas["map"], color="m_visits",
                    locations="geoids", featureidkey="properties.geoids",
                    projection="mercator", color_continuous_scale="orrd", labels={"m_visits": "Nombres de visites"})
    #fig = px.choropleth(datas["merged_map"], geojson=region, color=datas["merged_map"]["m_visits"],
                    #locations=datas["merged_map"]["geoids"],color_continuous_scale="orrd", labels={"m_visits": "Nombres de visites"}
                  #)
    #print(datas["merged_map"].geoids[0])
    #fig = go.Figure(go.Choroplethmapbox(
          #geojson=region,
          #locations=datas["merged_map"].geoids,
          #featureidkey="geoids",
          #z=datas["merged_map"].m_visits,
          #colorscale="orrd",
          #colorbar=dict(thickness=20, ticklen=3, title="Neuinfektionen pro 100.000 Einwohner und Tag", titleside="right"),
          #zmin=0, zmax=10,
          #marker_opacity=0.5, marker_line_width=0,
          #hovertemplate=
              #"<b>%{text}</b><br>" +
              #"%{z:.2f}<br>" +
              #"<extra></extra>",
              #))
    #fig.update_layout(
                        #uirevision=True, # keep zoom,panning, etc. when updating
                        #autosize=True,
                        #legend=dict(
                        #    # Adjust click behavior
                        #    itemclick="toggleothers",
                        #    itemdoubleclick="toggle",
                        #),
                        #xaxis=dict(
                        #    autorange='reversed',
                        #    fixedrange=True
                        #),
                        #yaxis=dict(
                        #    autorange='reversed',
                        #    fixedrange=True
                        #),
                        #width=500, height=450,
                        #mapbox_style="open-street-map", # https://plotly.com/python/mapbox-layers/
                        #mapbox_zoom=4.5,
                        #mapbox_center = {"lat": 51.30, "lon": 10.45},
                        #margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=600, title="Heatmap du nombre de visite en france métropolitaine")

    map_chart_figure = fig
    #print(type(map_chart_figure))

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
        map_chart_figure,\
        pie_chart_figure,\
        multiple_pie_chart_bar_figure