"""A high-level wrapper around docker-py
"""
import docker
import re
import tqdm

from _util import logger, logutil

logging = logger.fancy_logger("docker")


class DockerManager:
    def __init__(self):
        self.template_file = "docker_v1"
        self.docksock = "unix://var/run/docker.sock"

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
