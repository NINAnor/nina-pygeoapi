import logging
import os
from urllib.parse import urljoin

import requests
import shapely.ops
import shapely.wkt
import walrus
from pygeoapi.provider.base import BaseProvider

from . import URL

db = walrus.Database(
    host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379))
)
cache = db.cache()

url = urljoin(URL, "/vegobjekter/")

mapping = str.maketrans(
    {
        "æ": "ae",
        "ø": "oe",
        "å": "aa",
    }
)


def normalize(value):
    """Change column names to [a-z][a-z0-9_]*

    - General rule: make the string lowercase
    - GRASS requires [A-Za-z][A-Za-z0-9_]*
      https://github.com/OSGeo/grass/blob/889ed601c30bb609d73eb11a0bb3f985cff3b57d/vector/v.in.ogr/main.c#L1067
    """
    value = value.lower()
    value = value.translate(mapping)
    value = value.replace(" ", "_")
    value = "".join(v for v in value if v in "0123456789abcdefghijklmnopqrstuvwxyz")
    if value[0] in "0123456789":
        value = "_" + value
    return value


class VegObjekter(BaseProvider):
    def __init__(self, provider_def):
        super().__init__(provider_def)
        self.max_items = 300  # 300 seems to be the maximum number of items per page
        self.obj_id = self.options["obj_id"]

    def fix_geometry(self, y, x, z=None):
        """Drop Z and switch coordinates
        https://github.com/LtGlahn/nvdbapi-V3/issues/38
        """
        return x, y

    def wkt2geom(self, wkt):
        return shapely.ops.transform(self.fix_geometry, shapely.wkt.loads(wkt))

    def obj2feature(self, obj):
        if "geometri" not in obj:
            # example: https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/452/301561867/1
            obj["geometri"] = {"wkt": "POLYGON EMPTY"}

        geometry = self.wkt2geom(obj["geometri"]["wkt"])

        properties = {}
        for prop in obj["egenskaper"]:
            # https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper/datatyper
            if prop["navn"].startswith("Geom"):
                continue
            value = prop.get("verdi", None)
            if value is not None:
                properties[normalize(prop["navn"])] = value

        return {
            "type": "Feature",
            "id": obj["id"],
            "geometry": shapely.geometry.mapping(geometry),
            "properties": properties,
        }

    def quick_pagination(self, stop, step):
        for _ in range(stop // step):
            yield step
        if stop % step > 0:
            yield stop % step

    @cache.cached(timeout=60 * 60)
    def get_start(self, **params):
        return requests.get(urljoin(url, str(self.obj_id)), params=params).json()[
            "metadata"
        ]["neste"]["start"]

    @cache.cached(timeout=60 * 60)
    def query(
        self,
        offset=0,
        limit=10,
        resulttype="results",
        bbox=[],
        datetime_=None,
        properties=[],
        sortby=[],
        select_properties=[],
        skip_geometry=False,
        **kwargs,
    ):

        params = {
            "srid": 4326,
            "inkluder": "alle",
        }

        if bbox:
            params["kartutsnitt"] = ",".join(map(str, bbox))

        if offset > 0:
            pagination_params = params.copy()
            pagination_params.update(
                {
                    "inkluder": "minimum",
                }
            )
            for antall in self.quick_pagination(offset, self.max_items):
                pagination_params["antall"] = antall
                pagination_params["start"] = self.get_start(**pagination_params)
            params["start"] = pagination_params["start"]

        features = []

        for antall in self.quick_pagination(limit, self.max_items):
            params["antall"] = antall
            response = requests.get(
                urljoin(url, f"{self.obj_id}"), params=params
            ).json()
            if "objekter" not in response:
                logging.error(response)
            for obj in response["objekter"]:
                features.append(self.obj2feature(obj))
            params["start"] = response["metadata"]["neste"]["start"]

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def get(self, identifier, **kwargs):
        params = {
            "srid": 4326,
            "inkluder": "alle",
        }
        obj = requests.get(
            urljoin(url, f"{self.obj_id}/{identifier}"),
            params=params,
        ).json()
        return self.obj2feature(obj)

    def get_schema():
        return (
            "application/geo+json",
            {"$ref": "https://geojson.org/schema/Feature.json"},
        )
