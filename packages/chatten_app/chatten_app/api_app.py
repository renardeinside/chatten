from fastapi import FastAPI

from chatten_app.state import AppState


class StatefulApp(FastAPI):
    """FastAPI app with a state object that contains the client and file cache.
    Again, subclassing is used to add strong typing.

    Note that initialization happens only once, when the app is starting.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: AppState  = AppState()


api_app = StatefulApp()