import dash
from dash.dependencies import Output, Input
from utils_func import Utils
import plotly.express as px
import plotly.graph_objs as go
import time
from dash_app import app
from statsmodels.tsa.seasonal import seasonal_decompose

utils = Utils()

def home_callbacks(cache, TIMEOUT, region, df):
  @cache.memoize(timeout=TIMEOUT)
  def get_datas(filtered_data, pathname):
    if pathname == "/":
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
        cache.clear()
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
        datas = get_datas(filtered_data, pathname)
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
            seasonal_chart_figure