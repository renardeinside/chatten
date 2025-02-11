# Chatten

RAG with sources, built with Dash, FastAPI and Databricks platform.

## Developer setup

To install the project, following dependencies are required:
- [uv](https://docs.astral.sh/uv/): for managing the project
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html): for deploying the app
- [Node.js](https://nodejs.org/en/): for building the UI

To install the project, follow these steps:
1. Clone the repo
3. Run sync:

```bash
uv sync --all-packages
```


Don't forget to configure the environment variables in the `.env` file:

```bash
# name of your Databricks profile
CHATTEN_PROFILE=... 

# optionally, you can include any bundle or chatten variables like so:
CHATTEN_CATALOG=...

BUNDLE_VAR_vsi_endpoint=one-env-shared-endpoint-3
```

## Development

1. Start the npm watcher in one console:

```bash
cd packages/chatten_ui && npm run watch
```

1. Run the server in another console:

```bash
 uvicorn chatten_app.app:app --reload
```

## Deployment

1. Authenticate with Databricks:

```bash
databricks auth login -p <profile-name>
```

1. Deploy

```bash
# see makefile for additional variables
make deploy profile=fe-az-ws catalog=<catalog-name>
```

2. Run RAG workflow

```bash
# see makefile for additional variables
make run-rag profile=fe-az-ws catalog=<catalog-name>
```

2. Grant app principal access to the Volume
3. Run the app:

```bash
make run-app profile=fe-az-ws catalog=<catalog-name>
```

4. Open the app from Workspace

## Agent serving endpoint response parsing

Check the [api_app](packages/chatten_app/chatten_app/api_app.py) source code for details on how the agent serving endpoint response is parsed.
Specifically, the `/chat` API endpoint will take care of parsing the response and sending the messages to the chat.
    
## App implementation details

The implementation is based on a FastApi backend, which has two sub-apps:
1. The `/` route is served by the Dash app, which uses a custom component to render the chat
2. The `/api` route is served by the FastApi app, which provides the API for the chat

The chat is implemented as a custom Dash component, which is a React component that communicates with the FastApi backend.

The `/api` app communicates with the Databricks Serving endpoint to get chat requests and responses. Another route on the `/api` app is used to serve PDF files from the Databricks Volume.


## Code structure

The code is structured as follows:
- main package (`chatten`): contains the FastApi app and the Dash app. Main entrypoint is in `/src/chatten/app.py`.
- UI package (`packages/chatten_ui`): contains the Dash app and the custom Dash component. The Chat code is in `packages/chatten_ui/src/ts/blocks/Chat.tsx`.
- RAG package (`packages/chatten_rag`): contains the RAG related workflow
- App package (`packages/chatten_app`): contains the FastApi and Dash apps
- Common library (`src/chatten`): contains config parsing


## Technologies used 

- [Databricks](https://databricks.com/): Databricks platform
  - [Databricks Apps](https://www.databricks.com/product/databricks-apps) - app serving
  - [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) - deployment
  - [Mosaic AI Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/index.html) - model serving
  - [Mosaic AI Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html) - vector search
- [Dash](https://dash.plotly.com/): for the UI
- [FastApi](https://fastapi.tiangolo.com/): for the backend
- [Tailwind CSS](https://tailwindcss.com/): for styling
- [react-pdf](https://github.com/wojtekmaj/react-pdf): for rendering PDFs
- [Fuse.js](https://www.fusejs.io/): client-side fuzzy search in PDFs
- [pypdf](https://pypdf.readthedocs.io/en/stable/): for extracting text from PDFs on server side
- [RapidFuzz](https://pypi.org/project/RapidFuzz/): for fuzzy string matching on server side
- [uv](https://docs.astral.sh/uv/): managing the project
