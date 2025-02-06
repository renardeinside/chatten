from chatten_ui import ChattenUi
import dash


def create_dash_app() -> dash.Dash:
    """Create a Dash app with the Chatten UI.
    Note that chatten is heavily styled with Tailwind CSS, so you need to include the CDN link.
    """
    app = dash.Dash(__name__, title="Chatten UI", external_scripts=["https://cdn.tailwindcss.com"])
    app.layout = ChattenUi(id="chatten")
    return app
