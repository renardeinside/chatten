# Chatten

RAG with sources, built with Dash, FastAPI and Databricks platform.

## Setup

1. Clone the repo
2. Install uv 
3. Run sync:

```bash
uv sync
```

4. Install frontend dependencies:

```bash
cd packages/chatten_ui
npm install
```


Don't forget to configure the environment variables in the `.env` file:

```bash
# provide necessary Databricks Authentication details
DATABRICKS_...

# provide service details
VOLUME_PATH=/Volumes/...
SERVING_ENDPOINT=name-of-the-endpoint
```

## Development

1. Install frontend dependencies:

```bash
cd packages/chatten_ui
npm install
```

2. Run frontend in one console:

```bash
npm run watch
```

3. Run the server in another console:

```bash
uvicorn chatten.app:app --port 6006 --reload
```

## Deployment

1. Authenticate with Databricks:

```bash
databricks auth login -p <profile-name>
```

2. Deploy the app:

```bash
make deploy profile=profile-name app_name=app-name path=/Workspace/Users/username@company.com/apps/app-name
```

## Implementation details

The implementation is based on a FastApi backend, which has two sub-apps:
1. The `/` route is served by the Dash app, which uses a custom component to render the chat
2. The `/api` route is served by the FastApi app, which provides the API for the chat

The chat is implemented as a custom Dash component, which is a React component that communicates with the FastApi backend.

The `/api` app communicates with the Databricks Serving endpoint to get chat requests and responses. Another route on the `/api` app is used to serve PDF files from the Databricks Volume.


## Code structure

The code is structured as follows:
- main package (`chatten`): contains the FastApi app and the Dash app. Main entrypoint is in `/src/chatten/app.py`.
- UI package (`packages/chatten_ui`): contains the Dash app and the custom Dash component. The Chat code is in `packages/chatten_ui/src/ts/blocks/Chat.tsx`.