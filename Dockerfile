FROM python:3.8.3-alpine

# set work directory
WORKDIR /usr/src/exome_p

COPY pyproject.toml poetry.lock /usr/src/exome_p/

# Install system-level dependencies
RUN apk add build-base libffi-dev libressl-dev postgresql-dev gcc python3-dev musl-dev \
            zlib-dev bzip2-dev xz-dev

# Install htslib
RUN cd /usr/bin && \
    wget https://github.com/samtools/htslib/releases/download/1.9/htslib-1.9.tar.bz2 && \
    tar -vxjf htslib-1.9.tar.bz2 && \
    cd htslib-1.9 && \
    make


RUN pip install --upgrade pip && \
    pip install poetry==1.*

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY ./  /usr/src/exome_p/
COPY ./entrypoint.sh /usr/src/exome_p/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/usr/src/exome_p/entrypoint.sh"]
