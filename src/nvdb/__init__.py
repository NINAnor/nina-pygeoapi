import os

URL = "https://nvdbapiles-v3.atlas.vegvesen.no/"

mapping = str.maketrans(
    {
        "æ": "ae",
        "ø": "oe",
        "å": "aa",
    }
)


def normalize(value):
    """Change column and vector names to [a-z][a-z0-9_]*

    - General rule: make the string lowercase
    - GRASS requires [A-Za-z][A-Za-z0-9_]*
      https://github.com/OSGeo/grass/blob/7.8.5/vector/v.in.ogr/main.c#L1067
      https://github.com/OSGeo/grass/blob/7.8.5/lib/vector/Vlib/legal_vname.c#L19-L21
    """
    value = value.lower()
    value = value.translate(mapping)
    value = value.replace(" ", "_")
    value = "".join(v for v in value if v in "_0123456789abcdefghijklmnopqrstuvwxyz")
    if value[0] in "0123456789":
        value = "_" + value
    return value


if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
    )
    print('sentry ready')
