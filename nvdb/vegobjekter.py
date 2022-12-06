from urllib.parse import urljoin

import requests
import shapely.ops
import shapely.wkt
import walrus
from pygeoapi.provider.base import BaseProvider

db = walrus.Database()
cache = db.cache()


# URL = "https://nvdbapiles-v3.atlas.vegvesen.no/"
URL = "https://nvdbapiles-v3.test.atlas.vegvesen.no/"


class TrafikMengde(BaseProvider):
    """NVDB - TrafikMengde"""

    def __init__(self, provider_def):
        """Inherit from parent class"""
        super().__init__(provider_def)
        self.max_items = 300  # 300 seems to be the maximum number of items per page

    def fix_geometry(self, y, x, z=None):
        """Drop Z and switch coordinates
        https://github.com/LtGlahn/nvdbapi-V3/issues/38
        """
        return x, y

    def wkt2geom(self, wkt):
        return shapely.ops.transform(self.fix_geometry, shapely.wkt.loads(wkt))

    def obj2feature(self, obj):
        geometry = self.wkt2geom(obj["geometri"]["wkt"])

        properties = {}
        for prop in obj["egenskaper"]:
            if prop["egenskapstype"] == "Heltall":
                properties[prop["navn"]] = prop["verdi"]

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
        return requests.get(urljoin(URL, "vegobjekter/540"), params=params).json()[
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
                urljoin(URL, "vegobjekter/540"), params=params
            ).json()
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
            f"https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/540/{identifier}",
            params=params,
        ).json()
        return self.obj2feature(obj)

    def get_schema():
        return (
            "application/geo+json",
            {"$ref": "https://geojson.org/schema/Feature.json"},
        )
