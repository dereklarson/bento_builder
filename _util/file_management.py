import glob
import os
import pathlib
import shutil
import yaml

from _util import logger, dictutil

logging = logger.fancy_logger(__name__)


def dump(state, path):
    with open(path, "w") as fh:
        yaml.dump(state, fh, sort_keys=False)


def load(filepath, filetype="yaml", key=None):
    with open(filepath, "r") as fh:
        if filetype == "yaml":
            if key:
                return yaml.load(fh, Loader=yaml.Loader)[key]
            return yaml.load(fh, Loader=yaml.Loader)


def merge_yaml(filepath1, filepath2, outfile=None, clean=True):
    """Merge filepath2 keys into filepath1, write to outfile"""
    outfile = outfile or filepath1
    combined = dictutil.merge(load(filepath1), load(filepath2))
    if clean:
        remove(filepath1)
        remove(filepath2)
    dump(combined, outfile)


def remove(path, ignorable=False):
    if path.startswith(("~", "/")):
        logging.error("Use only relative paths for deletion")
        raise FileNotFoundError
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        if not ignorable:
            logging.warning(f"When removing, {path} not found")
            raise FileNotFoundError
    except NotADirectoryError:
        os.remove(path)


def create(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def recreate(path):
    remove(path, ignorable=True)
    create(path)


def copy(src, dest):
    if "*" in src:
        for fname in glob.glob(src):
            shutil.copy(fname, f"{dest}/")
    else:
        try:
            shutil.copytree(src, dest)
        except NotADirectoryError:
            shutil.copyfile(src, dest)
