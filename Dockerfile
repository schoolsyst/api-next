FROM python:3.8.3-slim-buster

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y install netcat gcc g++ git make -y

RUN pip install 'poetry>=1.0'
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install

COPY . .
