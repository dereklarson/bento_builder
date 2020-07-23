stock_page = {
    # This defines what dataframe the page will presume to use by default
    # Individual banks can set their data source via {"args": {"dataid": ...}}
    "dataid": "stock",
    "banks": {
        # The simplest bank entry: a uid key with the type specified in the dictionary
        "window": {"type": "window_controls"},
        # Supply args to the bank to control its behavior and appearance
        # In this case, we're indicating the filter dropdowns should stack vertically
        "filters": {"type": "filter_set", "args": {"vertical": True}},
        "axes": {"type": "axis_controls", "args": {"use": "y", "default": "open"},},
        "traces": {
            "type": "graph",
            # These arguments are passed into the method that constructs the bank
            "args": {"x_column": "date", "x_scale": "date", "mode": "lines"},
        },
    },
    # Defines a 2D grid of banks, determining their layout on the page
    "layout": [["axes", "filters", "window"], ["traces"]],
    # Lastly, this specifies which banks feed their outputs as inputs to other banks.
    # Callbacks will be generated via the template based on these.
    "connections": {"axes": {"traces"}, "filters": {"traces"}, "window": {"traces"},},
}

descriptor = {
    "name": "simple",
    # Supply theme keywords to quickly change the look
    # E.g. dark, flat, sparse
    "theme": "dark",
    "appbar": {
        "title": "Tech Stock Prices",
        "subtitle": "A simple Bento starting point",
    },
    "data": {"stock": {"module": "bento.sample_data.stock"}},
    "pages": {"stock": stock_page},
}
