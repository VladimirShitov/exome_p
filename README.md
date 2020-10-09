# Installation for development
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

4. To build and run the Docker container, execute:
```console
$ docker-compose --env-file exome_p/.env up -d --build
```

If something went wrong, you can check logs by running:
```console
$ docker-compose logs -f
```

# Useful commands

## Executing commands in the container
To execute a command in container, run: 
```console
$ docker-compose exec web poetry run <command>
```

For example:
```console
$ docker-compose exec web poetry run python manage.py migrate
```

## Getting access to the database

To get access to the database, first set the environment variables:
```console
$ export SQL_USER=<username>
$ export SQL_DATABASE=<database name> 

``` 
The run:
```console
$ docker-compose exec db psql --username=${SQL_USER} --dbname=${SQL_DATABASE}
```
