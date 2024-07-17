FROM debian:12.5
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && apt-get install --no-install-recommends -yq python3 python3-pip git python3-venv python3-dev

WORKDIR /app
RUN python3 -m venv .venv
ENV PYTHONPATH=/app/.venv/lib
ENV PATH=/app/.venv/bin:$PATH
COPY ./pyproject.toml .
RUN pip install -e .[prod]

COPY src src
RUN pip install -e .[prod]
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "pygeoapi.flask_app:APP", "--bind", "0.0.0.0:5000"]
ENV GUNICORN_CMD_ARGS="--workers=4"
EXPOSE 5000/TCP
