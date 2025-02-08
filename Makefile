	# uv build --all-packages --wheel -o ./.build
	# ls ./.build/*.whl > ./.build/requirements.txt

build-app:
	rm -rf ./.build
	uv build --all-packages --wheel -o ./.build
	cd .build && ls *.whl > requirements.txt



deploy: 
	databricks -p $(profile) \
		bundle deploy \
			--var="serving_endpoint=$(serving_endpoint)" \
			--var="volume_path=$(volume_path)" \
		

run:
	databricks -p $(profile) \
		bundle run chatten \
			--var="serving_endpoint=$(serving_endpoint)" \
			--var="volume_path=$(volume_path)"

all: build-app deploy run