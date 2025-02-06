create-app:
	databricks apps -p $(profile) create $(app_name)



build:
	rm -rf ./.build
	mkdir -p ./.build
	uv build --wheel -o ./.build
	cd packages/chatten_ui && npm run build && uv build --wheel -o ../../.build
	cd ./.build && ls *.whl > requirements.txt
	cp app.yml ./.build

deploy: build
	databricks -p $(profile) workspace import-dir --overwrite ./.build $(path)
	databricks apps -p $(profile) deploy $(app_name) --source-code-path $(path)