map_page = {
    "dataid": "zillow_2020",
    "banks": {
        "axes": {
            "type": "axis_controls",
            "width": 3,
            "args": {"use": "z", "default": "Zillow Rent Index", "scale": False},
        },
        "statemap": {
            "type": "graph",
            "args": {"category": "map", "variant": "choropleth", "geo": "states"},
        },
    },
    "layout": [["axes"], ["statemap"]],
    "connections": {"axes": {"statemap"}},
}

descriptor = {
    "name": "simple",
    "theme": "dark sparse flat",
    "appbar": {"title": "US Housing Market", "subtitle": "Data from Zillow in 2020",},
    "data": {"zillow_2020": {"module": "housing.df_snapshot"},},
    "pages": {"map": map_page},
}
