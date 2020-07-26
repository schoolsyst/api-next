FROM python:3.8.3-slim-buster

# Set the working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Deactivate some unneeded python features
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Regular build dependencies (not runtime ones)
RUN apt-get update && apt-get -y install netcat gcc g++ git make -y

# Install the package manager
RUN pip install 'poetry>=1.0'

# Copy over manifest files
COPY ./pyproject.toml ./poetry.lock ./

# Install stuff
RUN poetry install

# Copy the whole app
COPY . .
