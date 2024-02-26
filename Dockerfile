FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY pyproject.toml .
COPY src/nvdb/__init__.py src/nvdb/vegobjekter.py src/nvdb/
RUN python3 -m pip install .[prod]

COPY conf/config.yaml conf/
COPY update_config.py entrypoint.sh .

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
CMD ["gunicorn", "pygeoapi.flask_app:APP", "--bind", "0.0.0.0:5000"]
ENV GUNICORN_CMD_ARGS="--workers=4"
EXPOSE 5000/TCP
