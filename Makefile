dev:
	poetry run \
		uvicorn schoolsyst_api.main:api --reload

dependency-graph:
	poetry run \
		pydeps schoolsyst_api --only schoolsyst_api -oDEPENDENCY_GRAPH.png -Tpng --rmprefix schoolsyst_api.

fmt:
	poetry run black .
	poetry run isort -y

check-dead:
	poetry run \
		vulture schoolsyst_api --min-confidence 61

