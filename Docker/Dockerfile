FROM python:3.8.3-alpine

# set work directory
WORKDIR /usr/src/exome_p

COPY pyproject.toml poetry.lock /usr/src/exome_p/

# Install gcc and C++ dependencies
RUN apk add build-base libffi-dev libressl-dev
# musl-dev

RUN pip install --upgrade pip && \
    pip install poetry==1.*

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY ./exome_p  /usr/src/exome_p/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# TODO: change
#ENTRYPOINT ["poetry", "run", "gunicorn", "-c", "/data/gunicorn_cfg.py", "chem_mol_props:app"]
