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
make all \
    profile=profile-name \
    serving_endpoint=name-of-the-endpoint \
    volume_path=/Volumes/...
```

## Serving endpoint requirements

The serving endpoint should return the whole response in one single ChatMessage. The response should be a string-encoded JSON array with the following structure:
```json
[
    {
        "type": "ai_response",
        "content": "message content"
    },
    {
        "type": "tool_response",
        "responses": [
            {
                "metadata": {
                    "file_name": "file.pdf",
                    "year": 2021,
                    "chunk_num": 0,
                    "char_length": 1000
                },
                "content": "retrieved text from file"
            },
        ]
    }
]
```

The `/chat` API endpoint will take care of parsing the response and sending the messages to the chat.
    
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