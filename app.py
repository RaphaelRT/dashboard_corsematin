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
            children=[
                html.Div(children=[
                  html.Img(src="https://d2p1ubzgqn8tkf.cloudfront.net/storage/logo.svg"),
                  html.Div(children=[
                    dcc.Location(id='url', refresh=False),
                    dcc.Link('Home', href='/'),
                    dcc.Link('Origine du trafic', href='/trafic-origin'),
                  ], className="navBar")
                ], className="nav"),
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
            id="loading-container",
            color="#e74c3c",
            type="default",
            className="loading",
            parent_className="loading"
        ),
    ]
)
@app.callback([Output("loading-container", "children")],[Input('url', 'pathname')])
def displayPage(pathname):
  if pathname == "/":
    return home_layout
  if pathname == "/trafic-origin":
    return trafic_origin_layout

if __name__ == "__main__":
    app.run_server(debug=True)