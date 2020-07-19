import glob
import os
import pathlib
import shutil
import yaml

from common import logger, dictutil

logging = logger.fancy_logger(__name__)


class FileManager:
    @classmethod
    def dump(cls, state, path):
        with open(path, "w") as fh:
            yaml.dump(state, fh, sort_keys=False)

    @classmethod
    def load(cls, filepath, filetype="yaml", key=None):
        with open(filepath, "r") as fh:
            if filetype == "yaml":
                if key:
                    return yaml.load(fh, Loader=yaml.Loader)[key]
                return yaml.load(fh, Loader=yaml.Loader)

    @classmethod
    def merge_yaml(cls, filepath1, filepath2, outfile=None, clean=True):
        """Merge filepath2 keys into filepath1, write to outfile"""
        outfile = outfile or filepath1
        combined = dictutil.merge(cls.load(filepath1), cls.load(filepath2))
        if clean:
            cls.remove(filepath1)
            cls.remove(filepath2)
        cls.dump(combined, outfile)

    @classmethod
    def remove(cls, path, ignorable=False):
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

    @classmethod
    def create(cls, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    @classmethod
    def recreate(cls, path):
        cls.remove(path)
        cls.create(path)

    @classmethod
    def copy(cls, src, dest):
        if "*" in src:
            for fname in glob.glob(src):
                shutil.copy(fname, f"{dest}/")
        else:
            try:
                shutil.copytree(src, dest)
            except NotADirectoryError:
                shutil.copyfile(src, dest)
