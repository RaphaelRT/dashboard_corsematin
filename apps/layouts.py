import dash
import dash_core_components as dcc
import dash_html_components as html

home_layout = [
    html.Div(
        className="wrapper",
        id="wrapper",
        children = [
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
            )

        ]
    ),     
]
trafic_origin_layout = [ 
  html.Div(
        className="wrapper",
        id="wrapper",
        children = [
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
            )
        ]
    )
]
