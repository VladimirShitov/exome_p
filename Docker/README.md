### Installation for development
1. Clone the repository

2. Install [poetry](https://python-poetry.org/). Recommended way:
```console
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
Alternative way (not recommended):
```console
$ pip install --user poetry
```

3. Install project's dependencies:
```console
$ poetry install
```

4. To build the Docker container, run:
```console
$ docker-compose -f Docker/docker-compose.yml build
```

5. To run the container:
```console
$ docker-compose -f Docker/docker-compose.yml up -d
```

If something went wrong, you can check logs by running:
```console
$ docker-compose -f Docker/docker-compose.yml logs -f
```