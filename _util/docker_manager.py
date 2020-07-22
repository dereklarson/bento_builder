"""A high-level wrapper around docker-py
"""
import docker
import pathlib
import re
import tqdm
import parse
from jinja2 import Environment, PackageLoader

from _util import logger, logutil
from _util.structure import ENV

logging = logger.fancy_logger("docker")


class DockerManager:
    def __init__(self):
        self.template_file = "docker_v1"
        self.docksock = "unix://var/run/docker.sock"

    @logutil.loginfo(level="debug")
    def list(self, substr=""):
        images = []
        client = docker.from_env()
        for image in client.images.list():
            for valid_tag in [tag for tag in image.tags if ENV.DOCKER_PREFIX in tag]:
                matchstr = f"{ENV.REGISTRY}/{ENV.DOCKER_PREFIX}{{tag}}"
                match = parse.parse(matchstr, valid_tag)
                # Also try a match without a registry prefix
                if not match:
                    matchstr = f"{ENV.DOCKER_PREFIX}{{tag}}"
                    match = parse.parse(matchstr, valid_tag)
                if match and substr in match["tag"]:
                    images.append(valid_tag)
                    logging.info(f"Found {match['tag']}")

        return images

    @logutil.loginfo(level="debug")
    def push_matching(self, substr=""):
        images = self.list(substr=substr)
        for tag in images:
            self.push(tag)

    @logutil.loginfo(level="debug")
    def build(self, context, metadata=None):
        metadata = metadata or {}
        self.completion = 0
        self.linebuffer = ""
        client = docker.APIClient(base_url=self.docksock)
        output = client.build(decode=True, tag=context["tag"], path=context["path"])

        if metadata.get("stream"):
            return output

        for chunk in output:
            result = self.process_output_chunk(chunk)
        logging.info(self.linebuffer)

        # Return the error code
        return result["status"]

    def process_output_chunk(self, chunk):
        msg = {"text": self.linebuffer, "completion": self.completion, "status": 0}
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                if "Step" in line:
                    if self.linebuffer:
                        logging.info(self.linebuffer)
                    self.linebuffer = line
                    match = re.search(r"Step (\d{1,3})\/(\d{1,3})", line)
                    if match:
                        num, den = match.groups()
                        self.completion = int(num) / int(den)
                        msg = {
                            "text": self.linebuffer,
                            "completion": self.completion,
                            "status": 0,
                        }
                elif "cache" in line:
                    self.linebuffer = "Cached: " + self.linebuffer
        elif "error" in chunk:
            logging.warning(chunk["error"])
            msg = {"text": chunk["error"], "completion": self.completion, "status": 1}

        return msg

    @logutil.loginfo(level="debug")
    def push(self, tag, metadata=None) -> None:
        metadata = metadata or {}
        logging.info("Pushing docker image ...")
        # os.environ["DOCKER_BUILDKIT"] = "1"
        client = docker.APIClient(base_url=self.docksock)
        output = client.push(tag, decode=True, stream=True)
        if metadata.get("stream"):
            return output

        bars = {}
        for line in output:
            self.process_push_chunk(line, bars)

    def process_push_chunk(self, line, bars):
        if "id" not in line:
            return
        lid = line["id"]
        status = line["status"]
        desc = f"{lid}:{status: >24}"
        if lid in bars:
            if line["progressDetail"]:
                try:
                    total = line["progressDetail"]["total"]
                    incr = line["progressDetail"]["current"] - bars[lid]["bytes"]
                    bars[lid]["bar"].update(incr)
                    bars[lid]["bar"].total = total
                    bars[lid]["bytes"] += incr
                except Exception:
                    logging.warning(f"Can't process line: {line}")

            bars[lid]["bar"].desc = desc
        else:
            bars[lid] = {
                "bar": tqdm.tqdm(range(100), desc=desc),
                "bytes": 0,
            }

    @logutil.loginfo(level="debug")
    def write_template(self, context):
        try:
            pathlib.Path(context["path"]).mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        env_args = {"trim_blocks": True, "lstrip_blocks": True}
        jenv = Environment(loader=PackageLoader(__name__), **env_args)
        template = jenv.get_template(self.template_file)
        filename = f"{context['path']}/Dockerfile"
        with open(filename, "w") as fh:
            fh.write(template.render(context))

    def _text2cmds(self, text):
        """Parses a docker pseudo-file into a list of cmds and args"""
        parsed_results = {"commands": []}
        comment_buffer = []
        multiline_buffer = []
        for line in text.split("\n"):
            parts = line.strip().split(" ")
            if not parts[0]:
                # A blank line will reset a multiline block
                multiline_buffer = []
                continue
            # We store up comments to associate with the following command
            if parts[0].startswith("#"):
                comment_buffer.append(line)
                continue
            if parts[0] in ("USER", "FROM"):
                parsed_results[parts[0].lower()] = parts[1]
                continue
            if multiline_buffer:
                multiline_buffer.append(parts)
                if not line.strip().endswith("\\"):
                    multiline_buffer = []
                continue
            command = {
                "comments": comment_buffer,
                "cmd": parts[0],
                "lines": [parts[1:]],
            }
            if line.strip().endswith("\\"):
                multiline_buffer = command["lines"]
            comment_buffer = []
            parsed_results["commands"].append(command)

        return parsed_results

    @logutil.loginfo(level="debug")
    def generate_build_context(self, vertices, corpus, metadata):
        stage_contexts = []
        traversing = True

        curr_id = metadata["build_id"]
        while traversing:
            # TODO Assume, for now, there's a single parent per docker node
            # TODO handle versions in build chains
            context = {
                "uid": curr_id,
                "tag": f"{ENV.REGISTRY}/{ENV.DOCKER_PREFIX}{curr_id}:latest",
                "path": f"{ENV.BUILD_DIR}/{curr_id}",
                **self._text2cmds(corpus[curr_id]["text"]),
            }
            stage_contexts = [context] + stage_contexts
            parents = vertices[curr_id]["parents"]
            if parents:
                curr_id = list(parents.keys())[0]
            else:
                traversing = False

        self.write_template(stage_contexts[0])
        for base, context in zip(stage_contexts[:-1], stage_contexts[1:]):
            if "from" not in context:
                context["from"] = base["tag"]
            if "user" not in context:
                context["user"] = base.get("user") or "root"
            self.write_template(context)
        return {"build_orders": stage_contexts}
