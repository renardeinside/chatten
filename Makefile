build-app:
	rm -rf ./.build
	uv build --all-packages --wheel -o ./.build
	cd .build && ls *.whl > requirements.txt



deploy-app: 
	databricks -p $(profile) \
		bundle deploy \
			--var="serving_endpoint=$(serving_endpoint)" \
			--var="volume_path=$(volume_path)" \
		

run-app:
	databricks -p $(profile) \
		bundle run chatten \
			--var="serving_endpoint=$(serving_endpoint)" \
			--var="volume_path=$(volume_path)"

all-app: build-app deploy-app run-app