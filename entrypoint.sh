#!/bin/bash

set -euxo pipefail

export PYGEOAPI_CONFIG=/tmp/generated-config.yaml
export PYGEOAPI_OPENAPI=/tmp/generated-openapi.yaml
pdm run ./update_config.py ++server.url="$URL" ++logging.level="${LOGGING_LEVEL:-INFO}"
pdm run pygeoapi openapi generate "$PYGEOAPI_CONFIG" -of "$PYGEOAPI_OPENAPI"

exec "$@"
