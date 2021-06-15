import dash
import dash_core_components as dcc
import dash_html_components as html
from utils_func import Utils

utils = Utils()
initial_datas = utils.get_initial_datas()
df = initial_datas[0]
reco = initial_datas[2]
#print(reco["section_name"].values)
menu =  html.Div(
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
        )

home_layout = [
    html.Div(
        children = [
            menu,
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
    ), 
]
trafic_origin_layout = [
    html.Div(
        children = [
            menu,
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
    )
]
sections_name = reco.sort_values(by=['section_name'])["section_name"].values
reco_layout = [ 
  html.Div(
        className="wrapper",
        id="wrapper",
        children = [
            html.Div(
                children=[
                    html.Div(children=[
                        html.Label(children="Catégories :", className="label_title"),
                        dcc.Dropdown(
                            id='section_name_dropdown',
                            options=[ {'label': r, 'value': r} for r in sections_name],
                            value=sections_name[0]
                        ),
                        html.Div(children=[
                                html.Label(children="Titre :", className="label_title"),
                                dcc.Textarea(
                                    id='title_input_area',
                                    style={'width': '72%', 'height': 30},
                                )
                        ], className="title_container"),
                        html.Div(children=[
                            html.Div(children=[
                                html.Label(children="Article :", className="label_title"),
                                dcc.Textarea(
                                    id='input_area',
                                    style={'width': '100%', 'height': 300},
                                )
                            ],
                            className="articles_container"
                            )
                        ],
                        className="content_reco"
                        )
                    ],className="inputs_container"
                    ),
                    html.Div(children=[
                        html.Button('Valider', id='submit_button', className="submit_button", n_clicks=0),
                        html.Div(id="info_content", className="info_content"),
                        html.Label(children="Reco :", className="label_title"),
                        html.Div(
                            id='reco_container',
                            className="reco_container"
                        )
                    ],className="infos_container"
                    ),  
                ],
                className="reco_algo",
            )
        ]
    )
]
