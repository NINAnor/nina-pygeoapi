FROM python:3.11

RUN python3 -m pip install pdm

WORKDIR /app
COPY pyproject.toml pdm.lock .

RUN pdm install --no-self --group prod
COPY conf/config.yaml conf/
COPY nvdb/__init__.py nvdb/vegobjekter.py nvdb/
COPY update_config.py entrypoint.sh .

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
CMD ["pdm", "run", "gunicorn", "pygeoapi.flask_app:APP", "--bind", "0.0.0.0:5000"]
ENV GUNICORN_CMD_ARGS="--workers=4"
EXPOSE 5000/TCP
