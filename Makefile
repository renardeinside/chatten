

deploy:
	databricks -p $(profile) \
		bundle deploy \
			--var="catalog=$(catalog)"
		
run-rag:
	databricks -p $(profile) \
		bundle run chatten_rag \
			--var="catalog=$(catalog)"

all-rag: deploy run-rag

build-app:
	rm -rf ./.build
	uv build --all-packages --wheel -o ./.build
	cd .build && ls *.whl > requirements.txt

run-app:
	databricks -p $(profile) \
		bundle run chatten \
			--var="catalog=$(catalog)"

all-app: build-app deploy run-app

