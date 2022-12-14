#!/usr/bin/env python3


import datetime
import os
from urllib.parse import urljoin

import requests
import yaml

from nvdb import URL


def main(pygeoapi_config):
    with open(pygeoapi_config) as config_file:
        config = yaml.safe_load(config_file)

    object_types = requests.get(urljoin(URL, "/vegobjekttyper")).json()
    for object_type in object_types:
        resource = {
            "type": "collection",
            "title": f"[NVDB] {object_type['navn']}",
            "description": (
                f"{object_type.get('beskrivelse')}\n"
                f"VegObjekter ID: {object_type['id']}"
            ).lstrip(),
            "keywords": ["NVDB", "VegObjekter"],
            "links": [],
            "extents": {
                "spatial": {
                    "bbox": [-180, -90, 180, 90],
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                },
            },
            "providers": [
                {
                    "type": "feature",
                    "name": "nvdb.vegobjekter.VegObjekter",
                    "data": "/dev/null",
                    "options": {"obj_id": object_type["id"]},
                }
            ],
        }
        temporal_end = object_type.get("objektliste_dato")
        if temporal_end:
            resource["temporal"] = {"end": datetime.date.fromisoformat(temporal_end)}
        config["resources"][f"nvdb_{object_type['kortnavn']}"] = resource

    dumped_yaml = yaml.dump(config)
    with open(pygeoapi_config, "w") as config_file:
        config_file.write(dumped_yaml)


if __name__ == "__main__":
    pygeoapi_config = os.environ["PYGEOAPI_CONFIG"]
    main(pygeoapi_config)
