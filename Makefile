.PHONY: requirements.txt

dev:
	poetry run \
		uvicorn schoolsyst_api.main:api --reload

dependency-graph:
	poetry run \
		pydeps schoolsyst_api --only schoolsyst_api -o DEPENDENCY_GRAPH.png -T png --rmprefix schoolsyst_api. --noshow

check-dead:
	poetry run \
		vulture schoolsyst_api

requirements.txt:
	poetry export -f requirements.txt > requirements.txt

test:
	poetry run \
		python -m doctest schoolsyst_api/*.py \
	;poetry run \
		pytest --cov=schoolsyst_api

# TODO: include make dependency-graph in pre-commit config
prepush:
	$(MAKE) fmt
	$(MAKE) dependency-graph
	exit 0
