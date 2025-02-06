create-app:
	databricks apps -p $(profile) create $(app_name)

deploy:
	uv run pip freeze --exclude-editable >./requirements.txt
	databricks sync -p $(profile) ./ $(path) --full
	databricks apps -p $(profile) deploy $(app_name) --source-code-path $(path)

