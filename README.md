# Usage

```
redis=$(docker run --rm -p 6379:6379 --name pygeoapi-nina-redis -d redis)
pdm install --no-self
export PYGEOAPI_CONFIG=config.yml
export PYGEOAPI_OPENAPI=openapi.yml
pdm run pygeoapi openapi generate config.yml -of $PYGEOAPI_OPENAPI
pdm run pygeoapi serve # CTRL+C
docker stop $redis
```
