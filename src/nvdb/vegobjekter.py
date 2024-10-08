import os
from urllib.parse import urljoin

import backoff
import requests
import shapely.ops
import shapely.wkt
import walrus
from pygeoapi.provider.base import BaseProvider

import nvdb

db = walrus.Database(
    host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379))
)
cache = db.cache()
# cache invalidation by checking /transaksjon?

url = urljoin(nvdb.URL, "/vegobjekter/")
url_typer = urljoin(nvdb.URL, "/vegobjekttyper/")


class VegObjekter(BaseProvider):
    def __init__(self, provider_def):
        super().__init__(provider_def)
        self.max_items = 100  # maximum number of items per page
        self.obj_id = self.options["obj_id"]

    def fix_geometry(self, y, x, z=None):
        """Drop Z and switch coordinates
        https://github.com/LtGlahn/nvdbapi-V3/issues/38
        """
        return x, y

    def wkt2geom(self, wkt):
        return shapely.ops.transform(self.fix_geometry, shapely.wkt.loads(wkt))

    @cache.cached(timeout=60 * 60)
    def get_columns(self):
        typer = requests.get(
            urljoin(url_typer, str(self.obj_id)),
            params={"inkluder": "egenskapstyper"},
            timeout=10,
        ).json()
        # https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper/datatyper
        return [
            item["navn"]
            for item in typer["egenskapstyper"]
            if not item["navn"].startswith("Geom")
            and not item["navn"].startswith("Assosierte")
        ]

    def obj2feature(self, obj):
        if "geometri" not in obj:
            # example: https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/452/301561867/1
            obj["geometri"] = {"wkt": "POLYGON EMPTY"}

        geometry = self.wkt2geom(obj["geometri"]["wkt"])

        properties = {}
        for column in self.get_columns():
            name = nvdb.normalize(column)
            for prop in obj["egenskaper"]:
                if prop["navn"] == column:
                    value = prop.get("verdi", "")
                    break
            else:
                value = None
            properties[name] = value

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
        return requests.get(
            urljoin(url, str(self.obj_id)), params=params, timeout=10
        ).json()["metadata"]["neste"]["start"]

    @cache.cached(timeout=60 * 60)
    @backoff.on_exception(
        backoff.expo, requests.exceptions.RequestException, max_time=60
    )
    def query(
        self,
        offset=0,
        limit=10,
        resulttype="results",
        bbox=None,
        datetime_=None,
        properties=None,
        sortby=None,
        select_properties=None,
        skip_geometry=False,
        **kwargs,
    ):
        if select_properties is None:
            select_properties = []
        if sortby is None:
            sortby = []
        if properties is None:
            properties = []
        if bbox is None:
            bbox = []
        params = {
            "srid": 4326,
            "inkluder": "alle",
        }

        if bbox:
            params["kartutsnitt"] = ",".join(map(str, bbox))

        if datetime_:
            if ".." in datetime_:
                raise Exception("does not support interval")
            else:
                params["tidspunkt"] = datetime_

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
                urljoin(url, f"{self.obj_id}"), params=params, timeout=10
            )
            response.raise_for_status()
            response = response.json()
            if "objekter" not in response:
                raise Exception(
                    "does not contain 'objekter', please check this endpoint"
                )
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
            timeout=10,
        ).json()
        return self.obj2feature(obj)

    def get_schema():
        return (
            "application/geo+json",
            {"$ref": "https://geojson.org/schema/Feature.json"},
        )
