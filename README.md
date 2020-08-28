<img alt="schoolsyst logo" src="https://raw.githubusercontent.com/schoolsyst/presentation/master/assets/logo-black.svg" height="100px"/>

# schoolsyst's (next) API

![Build status](https://travis-ci.com/schoolsyst/api-next.svg?branch=master&status=passed) ![Code coverage](https://img.shields.io/codecov/c/github/schoolsyst/api-next) [![time tracker](https://wakatime.com/badge/github/schoolsyst/api-next.svg)](https://wakatime.com/badge/github/schoolsyst/api-next)

Schoolsyst's next API implementation, built with [FastAPI](https://fastapi.tiangolo.com)

See documentation at <https://beta.api.schoolsyst.com/>

## Installation

**Note** _A docker image is in the works (the database part is not ready yet)_

1. Install [Poetry](https://python-poetry.org) if you don't have it yet.
2. Clone the repository
    ```
    git clone https://github.com/schoolsyst/api-next
3. Make your `.env` file and fill it with your values:
    ```
    cp .env.example .env
    nano .env
    ```
3. Install dependencies
    ```
    poetry install
    ```
4. [Install ArangoDB](https://www.arangodb.com/download/) (no need if you have docker)
5. Start arangodb
    ```bash
    # with soystemd
    sudo systemctl start arangodb3
    # with systemv
    sudo service arangodb3 start
    # with docker (easier)
    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=<your_.env_file's_password> arangodb/arangodb:3.6.5
    ```
6. Test to make sure everything is alright
    ```
    make test
    ```
7. Start it (_finally!_)
    ```
    make dev
    ```
