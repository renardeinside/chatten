import chatten_ui
import dash

app = dash.Dash(__name__,
                 external_scripts=["https://cdn.tailwindcss.com"], title="Chatten"
)

app.layout = chatten_ui.Chatten(id='component')


if __name__ == '__main__':
    app.run_server(debug=True)
