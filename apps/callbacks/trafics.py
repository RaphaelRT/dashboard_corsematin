import dash
from dash.dependencies import Output, Input
from utils_func import Utils
import plotly.express as px
import plotly.graph_objs as go
import time
from dash_app import app

utils = Utils()

def trafic_callbacks(cache, TIMEOUT, region, df):
  @cache.memoize(timeout=TIMEOUT)
  def get_datas(filtered_data, pathname):
    if pathname == "/trafic-origin":
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
      datas = get_datas(filtered_data, pathname)
      #print(datas["map"])
      fig = px.choropleth(datas["merged_map"], geojson=datas["map"], color="m_visits",
                      locations="geoids", featureidkey="properties.geoids",
                      projection="mercator", color_continuous_scale="orrd", labels={"m_visits": "Nombres de visites"})
      
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