FROM python:3.8.5-slim

LABEL base_on="Grega Vrbančič <grega.vrbancic@gmail.com"
LABEL developedBy="Mickey Perlstein <corp.mp@gmail.com"

ENV DOCKER=true

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry install

EXPOSE 8000