from chatten_ui import ChattenUi
import dash 

if __name__ == '__main__':
    app = dash.Dash(__name__, title="Chatten UI", external_scripts=["https://cdn.tailwindcss.com"])
    app.layout = ChattenUi(id="chat")
    app.run_server(debug=True)
