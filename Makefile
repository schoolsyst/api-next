dev:
	poetry run \
		uvicorn schoolsyst_api.main:api --reload

dependency-graph:
	poetry run \
		pydeps schoolsyst_api --only schoolsyst_api -oDEPENDENCY_GRAPH.png -Tpng --rmprefix schoolsyst_api.

check-dead:
	poetry run \
		vulture schoolsyst_api

requirements-txt:
	poetry run \
		pip freeze > requirements.txt

prepush:
	$(MAKE) fmt
	$(MAKE) dependency-graph
	exit 0
