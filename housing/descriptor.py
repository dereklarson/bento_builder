map_page = {
    "dataid": "housing",
    "banks": {
        "axes": {
            "type": "axis_controls",
            "args": {"use": "z", "default": "Zillow Rent Index"},
        },
        "statemap": {
            "type": "graph",
            "args": {"category": "map", "variant": "choropleth", "geo": "states"},
        },
    },
    "layout": [["axes", "filters"], ["statemap"]],
    "connections": {"axes": {"statemap"}},
}

descriptor = {
    "name": "simple",
    "theme": "dark",
    "appbar": {"title": "US Housing Market", "subtitle": "Data from Zillow in 2020",},
    "data": {"housing": {"module": "housing.df_housing"}},
    "pages": {"map": map_page},
}
