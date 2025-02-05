import _chatten_ui.chatten_ui as chatten_ui
import dash


def create_dash_app() -> dash.Dash:
    app = dash.Dash(__name__, external_scripts=["https://cdn.tailwindcss.com"])
    app.layout = chatten_ui.Chatten(id="component")
    return app
