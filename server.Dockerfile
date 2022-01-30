FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /server
WORKDIR /server

RUN apt update

COPY pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY ./server /server

ENV PYTHONPATH=/server

CMD python main.py