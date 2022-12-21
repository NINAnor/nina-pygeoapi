#!/usr/bin/env python3

import datetime
import os
import tempfile
from urllib.parse import urljoin

import hydra
import requests
import yaml
from omegaconf import OmegaConf, open_dict

from nvdb import URL


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg):
    pygeoapi_config = os.environ["PYGEOAPI_CONFIG"]

    OmegaConf.set_struct(cfg, True)
    with open_dict(cfg):
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
                resource["temporal"] = {"end": temporal_end}
            cfg["resources"][f"nvdb/{object_type['kortnavn']}"] = resource

    with open(pygeoapi_config, "w") as config_file:
        config_file.write(OmegaConf.to_yaml(cfg))


if __name__ == "__main__":
    main()
