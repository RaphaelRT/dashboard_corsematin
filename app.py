import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import ssl
from dash_app import app
from apps.layouts import *
from apps.callbacks import *

ssl._create_default_https_context = ssl._create_unverified_context
app.title = "Corse Matin Analysis"
server = app.server
app.layout = html.Div(
    children=[
        html.Div(
            id="header",
            children=[
                html.Div(children=[
                  html.Img(src="https://d2p1ubzgqn8tkf.cloudfront.net/storage/logo.svg"),
                  html.Div(children=[
                    dcc.Location(id='url', refresh=False),
                    dcc.Link('Home', href='/'),
                    dcc.Link('Origine du trafic', href='/trafic-origin'),
                    dcc.Link('Recommandations', href='/reco'),
                  ], className="navBar")
                ], className="nav"),
                html.H1(
                    children="📈 Dashboard Corse Matin", className="header-title"
                ),
                html.P(
                    children="Analyses et recommandations sur l'audience"
                    " de tout les sites"
                    " entre 2015 et 2020",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        dcc.Loading(
            id="loading-container",
            color="#e74c3c",
            type="default",
            className="loading",
            parent_className="loading",
            fullscreen=True
        ),
    ]
)
@app.callback([Output("loading-container", "children"), Output("header", "style")],[Input('url', 'pathname')])
def displayPage(pathname):
  if pathname == "/":
    return home_layout, {"height": "288px"}
  if pathname == "/trafic-origin":
    return trafic_origin_layout, {"height": "288px"}
  if pathname == "/reco":
      return reco_layout, {"padding-bottom": "1.1rem"}

if __name__ == "__main__":
    app.run_server(debug=False)