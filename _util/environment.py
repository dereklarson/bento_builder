"""This is an attempt to structure the ingesting of environment variables.
All used env variables should be in ENV_SPEC and the ENV export be used globally.
Generally, a docker-compose run would be supplying values for most of these. If the
run is outside of Docker, many of these attributes would fall to the defaults.
"""
import os
import re
from dataclasses import dataclass

from _util import logger
from _util.dictutil import Edict  # Allows set "&" syntax on dict keys

logging = logger.fancy_logger(__name__)


@dataclass
class ENV_SPEC:
    # Generic variables
    APP: str = ""
    DEV: bool = False

    # Determines where the application looks for resources
    APP_HOME: str = "."
    DATA_DIR: str = "data"
    STORAGE_DIR: str = "storage"
    BUILD_DIR: str = "build"

    # Where in your local environment to look for resources
    # (Usually, this is just provided by your usual $HOME)
    HOME: str = "."

    # Organization configuration: Cloud computing, etc
    REGISTRY: str = "local"
    BENTO_PORT: int = 7777


def parse_env_file(env_file: str) -> dict:
    """When not running in a container, the env_file won't be injected, so we need to
    process the environemnt variables manually using this function"""
    with open(env_file, "r") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            match = re.search(r"([A-Z_]+)=(.*)", line)
            try:
                name, val = match.groups()
                os.environ[name] = val
                logging.debug(f"  {name}: {val}")
            except AttributeError:
                pass


def init(env_file: str):
    # First load input env files into the
    parse_env_file(env_file)
    ENV = ENV_SPEC(**(Edict(os.environ) & Edict(ENV_SPEC())))
    # TODO Figure this out (order of ops problems with importing, logging, env-setting)
    # logging.setLevel(int(os.environ["LOGLEVEL"]))
    logging.debug("---Environment variables:")
    logging.debug(vars(ENV))
    return ENV
