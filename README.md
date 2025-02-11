# 🚀 Chatten

RAG with sources, built with **Dash**, **FastAPI**, and the **Databricks** platform.

---

## 🛠 Developer Setup

To install the project, ensure you have the following dependencies:

- 📦 [uv](https://docs.astral.sh/uv/): for managing the project
- 🚀 [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html): for deploying the app
- 🌐 [Node.js](https://nodejs.org/en/): for building the UI

### 📥 Installation Steps

1. Clone the repo:

   ```bash
   git clone <repo-url>
   ```

2. Run sync:

   ```bash
   uv sync --all-packages
   ```

3. Configure environment variables in the `.env` file:

   ```bash
   # Name of your Databricks profile
   CHATTEN_PROFILE=...
   
   # Optionally, you can include any bundle or Chatten variables:
   CHATTEN_CATALOG=...
   
   BUNDLE_VAR_vsi_endpoint=one-env-shared-endpoint-3
   ```

---

## 🏗 Development

1. Start the UI watcher in one terminal:

   ```bash
   cd packages/chatten_ui && npm run watch
   ```

2. Run the server in another terminal:

   ```bash
   uvicorn chatten_app.app:app --reload
   ```

---

## 🚀 Deployment

1. Authenticate with Databricks:

   ```bash
   databricks auth login -p <profile-name>
   ```

2. Deploy the app:

   ```bash
   # See Makefile for additional variables
   make deploy profile=fe-az-ws catalog=<catalog-name>
   ```

3. Run the RAG workflow:

   ```bash
   # See Makefile for additional variables
   make run-rag profile=fe-az-ws catalog=<catalog-name>
   ```

4. Grant app principal access to the Volume.
5. Run the app:

   ```bash
   make run-app profile=fe-az-ws catalog=<catalog-name>
   ```

6. Open the app from **Databricks Workspace** 🎉

---

## 🤖 Agent Serving Endpoint Response Parsing

Check the [`api_app`](packages/chatten_app/chatten_app/api_app.py) source code for details on how the agent serving endpoint response is parsed.

Specifically, the `/chat` API endpoint handles:
- Parsing responses
- Sending messages to the chat interface

---

## 🏛 App Implementation Details

The implementation consists of a **FastAPI** backend with two sub-apps:

1. **Dash app (`/` route)**: Uses a custom component to render the chat UI.
2. **FastAPI app (`/api` route)**: Provides API endpoints for the chat.

The chat is implemented as a **custom Dash component**, which is a React-based UI element that communicates with the FastAPI backend.

The `/api` app interacts with the **Databricks Serving Endpoint** to handle chat requests and responses. Another route is responsible for serving PDF files from **Databricks Volume**.

---

## 📂 Code Structure

```
📦 chatten  # Main package (FastAPI + Dash app)
 ┣ 📂 packages/chatten_ui  # Dash UI & custom chat component
 ┣ 📂 packages/chatten_rag  # RAG workflow implementation
 ┣ 📂 packages/chatten_app  # FastAPI & Dash apps
 ┣ 📂 src/chatten  # Common config & utilities
 ┣ 📂 src/chatten/app.py  # Main entry point
```

---

## 🏗 Technologies Used

### 🔥 Core Platform
- [Databricks](https://databricks.com/)
  - [Apps](https://www.databricks.com/product/databricks-apps) - App serving
  - [Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) - Deployment
  - [Mosaic AI Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/index.html) - Model serving
  - [Mosaic AI Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html) - Vector search

### 🏗 Frameworks & Libraries
- 🖥 [Dash](https://dash.plotly.com/) - UI framework
- ⚡ [FastAPI](https://fastapi.tiangolo.com/) - Backend API
- 🎨 [Tailwind CSS](https://tailwindcss.com/) - Styling
- 📄 [react-pdf](https://github.com/wojtekmaj/react-pdf) - PDF rendering
- 🔍 [Fuse.js](https://www.fusejs.io/) - Client-side fuzzy search
- 📜 [pypdf](https://pypdf.readthedocs.io/en/stable/) - Server-side PDF text extraction
- ⚡ [RapidFuzz](https://pypi.org/project/RapidFuzz/) - Fuzzy string matching
- 📦 [uv](https://docs.astral.sh/uv/) - Dependency management
