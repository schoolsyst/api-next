.PHONY: requirements.txt DEPENDENCY_GRAPH.png

dev:
	sudo systemctl start arangodb3; \
	poetry run \
		uvicorn schoolsyst_api.main:api --reload

update:
	poetry update && $(MAKE) requirements.txt

DEPENDENCY_GRAPH.png:
	poetry run \
		pydeps schoolsyst_api --only schoolsyst_api -o DEPENDENCY_GRAPH.png -T png --rmprefix schoolsyst_api. --noshow -x schoolsyst_api.{database,models}

check-dead:
	poetry run \
		vulture schoolsyst_api

requirements.txt:
	poetry export -f requirements.txt > requirements.txt
	poetry export -f requirements.txt --dev > requirements_dev.txt

test:
	poetry run \
		python -m doctest -v schoolsyst_api/**.py \
	&& poetry run \
		pytest --cov=schoolsyst_api

tidy:
	poetry run \
		autoflake --remove-all-unused-imports --expand-star-imports --in-place **.py \
	&& poetry run \
		black **.py
