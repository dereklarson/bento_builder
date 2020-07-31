import glob
import importlib
import sys

from _util import logger

logging = logger.fancy_logger(__name__)


def parse_versions() -> dict:
    """Grabs version string from each app's _version.py"""
    versions = {}
    for app in [appdir[:-1] for appdir in glob.glob("[a-z]*/")]:
        try:
            version_module = importlib.import_module(f"{app}._version")
            versions[app] = version_module.__version__
        except ModuleNotFoundError:
            logging.warning(f"No _version.py file for {app}")
            pass

    logging.debug(versions)
    return versions


def get_previous_version(versions: dict, app: str) -> str:
    """Looks in the app's .version_history to retrieve the prior version"""
    try:
        with open(f"{app}/.version_history", "r") as fh:
            lines = [line.strip() for line in fh]
    except FileNotFoundError:
        logging.warning(f"No .version_history for {app}")
        return ""

    if versions[app] != lines[-1]:
        logging.warning(
            f"Mismatch in data:\n\tCurrent version is {versions[app]}"
            f" but most recent line in .version_history is {lines[-1]}"
        )
        return ""
    elif len(lines) < 2:
        logging.warning("No prior version recorded")
        return ""
    return lines[-2]


def bump_version(versions: dict, app: str, level: str) -> None:
    """Increments a version string based on supplied level of release"""
    before = versions.get(app, "0.0.0")
    if level == "revert":
        after = get_previous_version(versions, app)
        if not after:
            logging.info("Declining to revert")
            sys.exit(1)
    else:
        parts = before.split(".")
        index = 0 if level == "major" else 1 if level == "minor" else 2
        parts[index] = str(int(parts[index]) + 1)
        # Set any lower indices to 0
        for smaller_index in range(2, index, -1):
            parts[smaller_index] = "0"
        after = ".".join(parts)

    versions[app] = after
    logging.info(f"Updating {app}:{before} to {versions[app]}")


def write_update(versions: dict, app: str) -> None:
    with open(f"{app}/_version.py", "w") as fh:
        fh.write("# Version is read/modified by build.py, edit carefully)\n")
        fh.write(f"""__version__ = "{versions[app]}"\n""")
    with open(f"{app}/.version_history", "a") as fh:
        fh.write(f"""{versions[app]}\n""")


def get_version(app: str) -> str:
    versions = parse_versions()
    return versions.get(app, "0.0.0")


def release(app: str, level: str = "patch") -> str:
    versions = parse_versions()
    bump_version(versions, app, level)
    write_update(versions, app)
    return versions[app]
