FROM python:3.8.3-alpine

# set work directory
WORKDIR /usr/src/exome_p

COPY pyproject.toml poetry.lock /usr/src/exome_p/

# Install system-level dependencies
RUN apk add build-base libffi-dev libressl-dev postgresql-dev gcc python3-dev musl-dev \
            zlib-dev bzip2-dev xz-dev git curl

# Install htslib
RUN cd /usr/bin && \
    wget https://github.com/samtools/htslib/releases/download/1.9/htslib-1.9.tar.bz2 && \
    tar -vxjf htslib-1.9.tar.bz2 && \
    cd htslib-1.9 && \
    make

# install fastNGSadmix
RUN git clone https://github.com/e-jorsboe/fastNGSadmix.git && \
    cd fastNGSadmix && \
    make && \
    cp fastNGSadmix /usr/bin/

# Install plink
RUN wget http://s3.amazonaws.com/plink1-assets/plink_linux_x86_64_20201019.zip && \
    unzip plink_linux_x86_64_20201019.zip && \
    cp plink /usr/bin/

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"
#ENV PATH="${HOME}/.cargo/bin:${PATH}"

RUN pip install --upgrade pip && \
    pip install poetry==1.*

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY ./  /usr/src/exome_p/
COPY ./entrypoint.sh /usr/src/exome_p/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN ["chmod", "+x", "/usr/src/exome_p/entrypoint.sh"]
ENTRYPOINT ["/usr/src/exome_p/entrypoint.sh"]
