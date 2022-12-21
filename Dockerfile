FROM python:3.11

RUN python3 -m pip install pdm

WORKDIR /app
COPY pyproject.toml pdm.lock .

RUN pdm install --no-self
COPY conf/config.yaml conf/
COPY nvdb/__init__.py nvdb/vegobjekter.py nvdb/
COPY update_config.py entrypoint.sh .

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
CMD ["pdm", "run", "pygeoapi", "serve"]
EXPOSE 5000/TCP
