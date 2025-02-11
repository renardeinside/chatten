
build-app:
	rm -rf ./.build
	uv build --package chatten --wheel -o ./.build
	uv build --package chatten_ui --wheel -o ./.build
	uv build --package chatten_app --wheel -o ./.build
	cd .build && ls *.whl > requirements.txt

deploy: build-app
	databricks -p $(profile) \
		bundle deploy \
			--var="catalog=$(catalog)"
		
run-rag:
	databricks -p $(profile) \
		bundle run chatten_rag \
			--var="catalog=$(catalog)"

# make sure you're running the app after the RAG pipeline
run-app:
	databricks -p $(profile) \
		bundle run chatten \
			--var="catalog=$(catalog)"


all-rag: deploy run-rag
all-app: deploy run-app

