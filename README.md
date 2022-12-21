# Usage

Set `URL` variable first.

```
redis=$(docker run --rm -p 6379:6379 --name pygeoapi-nina-redis -d redis)
pdm install --no-self
export PYGEOAPI_CONFIG=generated-config.yaml
export PYGEOAPI_OPENAPI=generated-openapi.yaml
pdm run ./update_config.py ++server.url=$URL
pdm run pygeoapi openapi generate $PYGEOAPI_CONFIG -of $PYGEOAPI_OPENAPI
pdm run pygeoapi serve # CTRL+C
docker stop $redis
```
