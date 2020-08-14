import os
import yaml
from utils.dotdict import DotDict


def get_config():
    config = DotDict({})
    # get default config
    if os.path.isfile("config.yml"):
        with open("config.yml", "r") as fd:
            config = DotDict(yaml.safe_load(fd))
    # override with any environment-specific (dev, test, prod) updates
    # via config.dev.yml, config.prod.yml, etc
    if os.environ.get("ENVIRONMENT", None):
        environment = os.environ.get("ENVIRONMENT", "")
        if os.path.isfile(f"config.{environment}.yml"):
            with open(f"config.{environment}.yml", "r") as fd:
                config.update(DotDict(yaml.safe_load(fd)))

    # lastly, if any config key exists in our os.environ, use that instead
    for key in config.keys():
        if os.environ.get(key, None):
            config[key] = os.environ.get(key)
    # any key set to 'none', set it to None
    for key in config.keys():
        if config.get(key) in ["NONE", "none", "None"]:
            config[key] = None
    return config
