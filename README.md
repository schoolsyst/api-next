<center><p align="center">
<img src="https://raw.githubusercontent.com/schoolsyst/presentation/master/assets/logo-black.svg" alt="schoolsyst logo" height="150px">
<h1>schoolsyst's (next) API</h1>
<img src="https://travis-ci.com/schoolsyst/api-next.svg?branch=master&status=passed" alt="Build status">&nbsp;<img alt="Code coverage" src="https://img.shields.io/codecov/c/github/schoolsyst/api-next">
</p></center>

Schoolsyst's next API implementation, built with [FastAPI](https://fastapi.tiangolo.com)

~~See documentation at <https://dev.schoolsyst.com/docs>~~ for now, the docs can only be accessed by [installing the API locally](#installation) and accessing <http://localhost:8000/>.

## Installation

**Note** _A docker image is in the works (the database part is not ready yet)_

1. Install [Poetry](https://python-poetry.org) if you don't have it yet.
2. Clone the repository
    ```
    git clone https://github.com/schoolsyst/api-next
3. Install dependencies
    ```
    poetry install
    ```
4. [Install ArangoDB](https://www.arangodb.com/download/)
5. Start arangodb (no need for this if you used the docker image instead)
    ```bash
    sudo systemctl start arangodb3 # with soystemd
    sudo service arangodb3 start # with systemv init
    ```
6. Test to make sure everything is alright
    ```
    make test
    ```
7. Start it (_finally!_)
    ```
    make dev
    ```
