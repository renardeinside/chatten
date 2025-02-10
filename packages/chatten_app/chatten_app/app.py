from fastapi import FastAPI
from chatten_app.dash_app import create_dash_app
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware

from chatten_app.api_app import api_app


app = FastAPI()

dash_app = create_dash_app()

# note: the order of mounting is important!
app.mount("/api", api_app)
app.mount("/", WSGIMiddleware(dash_app.server))


