#!/bin/bash -x

set -o errexit
set -o pipefail

export PYGEOAPI_CONFIG=/tmp/generated-config.yaml
export PYGEOAPI_OPENAPI=/tmp/generated-openapi.yaml
nina-pygeoapi_update_config ++server.url="$URL" ++logging.level="${LOGGING_LEVEL:-INFO}"
pygeoapi openapi generate "$PYGEOAPI_CONFIG" -of "$PYGEOAPI_OPENAPI"

exec "$@"
