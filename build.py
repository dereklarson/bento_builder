#!/usr/bin/env python3
import argparse
import fileinput
import glob
import os

# import signal
import subprocess
import sys

from common import versioning, util
from common.file_manager import FileManager as FM
from common.docker_manager import DockerManager


try:
    from common import logger

    logging = logger.fancy_logger("build")
except ImportError:
    import logging

LOCAL_ENV = "../ORG_ENV"


def tag(build_args):
    if build_args.release:
        version = versioning.release(build_args.app, level=build_args.release)
    else:
        version = versioning.get_version(build_args.app)
    build_args.version = version
    state = "" if not build_args.dev else "dev"
    build_args.tag = f"{os.environ['REGISTRY']}/{build_args.app}:{version}{state}"
    logging.info(f"Setting build tag to {build_args.tag}")


def prepare_stage(build_args):
    logging.info(f"Preparing staging directory: {build_args.stg_dir}")
    # Completely clean prior build and recreate with source code
    FM.recreate(build_args.stg_dir)
    FM.copy(f"{build_args.app}", f"{build_args.stg_dir}/{build_args.app}")


def add_docker(build_args):
    logging.info(f"Adding {build_args.app} docker materials => {build_args.stg_dir}")
    FM.copy("_docker/*", build_args.stg_dir)
    compose = f"{build_args.stg_dir}/{build_args.app}/docker-compose.yaml"
    dev_compose = f"{build_args.stg_dir}/{build_args.app}/dev-docker-compose.yaml"
    if build_args.dev:
        try:
            FM.merge_yaml(compose, dev_compose, outfile=dev_compose)
        except FileNotFoundError:
            logging.info(f"Couldn't merge docker-compose and dev-docker-compose")
    else:
        FM.remove(dev_compose, ignorable=True)


def prepare_entrypoint(build_args):
    dest = f"{build_args.stg_dir}/entrypoint.py"
    source = f"{build_args.entrypoint}.py"
    if not glob.glob(source):
        logging.info("Entrypoint file not found, presuming to ignore")
        return
    logging.info(f"Preparing entrypoint {source} => {dest}")
    FM.copy(source, dest)


def _prepare_run(build_args):
    os.environ["BARE"] = "True"
    os.chdir(build_args.stg_dir)
    sys.path.append(f"{os.environ['PYREPO']}/{build_args.stg_dir}")


def execute(build_args):
    _prepare_run(build_args)
    subprocess.run(["python3", "launch_app.py"])
    finish(None)


def finish(build_args, *args):
    sys.exit()


def build(build_args) -> None:
    logging.info("Building docker image ...")
    dm = DockerManager()
    # os.environ["DOCKER_BUILDKIT"] = "1"
    build_context = {
        "tag": build_args.tag,
        "path": build_args.stg_dir,
    }
    code = dm.build(build_context)
    if code:
        finish(None)


def push(build_args) -> None:
    logging.info("Pushing docker image ...")
    dm = DockerManager()
    dm.push(build_args.tag)


def enter(build_args) -> None:
    logging.info("Entering docker image ...")
    subprocess.run(["docker", "run", "-it", "--entrypoint=/bin/bash", build_args.tag])


def _env_file(build_args):
    """Creates the .env file for use with docker-compose"""
    logging.debug(f"...docker/.* => .env for docker compose support")
    in_files = [inf for inf in sorted(glob.glob("docker/.*")) if "swp" not in inf]
    in_files.append(LOCAL_ENV)
    logging.debug(f"    from {in_files}")
    with open(f"{build_args.stg_dir}/.env", "w") as fout:
        loglevel = 10 if build_args.verbose else 20
        fout.write(f"# Logging for modules\nLOGLEVEL_NAME={loglevel}\n\n")
        fout.write(
            "# Application Specs\n"
            f"APP={build_args.app}\n"
            f"APP_VERSION={build_args.version}\n\n"
        )
        with fileinput.input(in_files) as fin:
            for line in fin:
                fout.write(line)


def run(build_args) -> None:
    dev = "dev-" if build_args.dev else ""
    compose_file = f"{dev}docker-compose.yaml"
    _env_file(build_args)
    # Must move to staging to make use of .env file
    os.chdir(build_args.stg_dir)
    util.nice_command(["docker-compose", "-f", compose_file, "up"])


if __name__ == "__main__":
    # Immediately take in any organizational environment (added to os.environ)
    apps = os.environ["DASHBOARDS"].split(":")

    # Handle build arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=str, choices=apps, help=f"Choose app from {apps}")
    parser.add_argument(
        "--build_dir", type=str, default="_build", help=f"Choose build dir (_build)"
    )
    parser.add_argument(
        "--entrypoint",
        type=str,
        default="entrypoint",
        help=f"Choose entrypoint (entrypoint)",
    )
    parser.add_argument("-B", "--build", action="store_false", help="Avoid build")
    parser.add_argument("-d", "--dev", action="store_true", help="Dev build")
    parser.add_argument(
        "-i", "--interact", action="store_true", help="Enter docker image"
    )
    parser.add_argument("-p", "--push", action="store_true", help="Push image online")
    parser.add_argument("-q", "--quiet", action="store_true", help="No info output")
    parser.add_argument("-r", "--release", nargs="?", default="", help=f"Release (app)")
    parser.add_argument("-s", "--stage", action="store_true", help="Only prepare build")
    parser.add_argument("-t", "--tag", nargs="?", default="", help="Docker image tag")
    parser.add_argument("-u", "--up", action="store_true", help="Run after build")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debugging output")
    parser.add_argument("-x", "--execute", action="store_true", help="Run (no docker)")
    args = parser.parse_args()

    # NOTE This has issues with timing of imports. We probably need to add some more
    # clever way to adjust the logging levels of local modueles
    if args.quiet:
        logging.setLevel(30)

    if args.verbose:
        logging.setLevel(10)

    # Point staging directory to app-specific directory
    args.stg_dir = f"{args.build_dir}/{args.app}"

    logging.debug("---Build args:")
    logging.debug(vars(args))

    # Ordered series of operations to run
    steps = [
        tag,
        prepare_stage,
        add_docker,
        prepare_entrypoint,
        execute if args.execute else None,
        finish if args.stage else None,
        build if args.build else None,
        push if args.push else None,
        enter if args.interact else None,
        run if args.up else None,
    ]

    # Run build methods
    for step in steps:
        if not step:
            continue
        step(args)
