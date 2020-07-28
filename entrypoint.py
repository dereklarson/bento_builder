import importlib

from bento import bento
from bento.common.structure import ENV
from bento.common import logger

logging = logger.fancy_logger("entrypoint")

# This generates the app from the descriptor
logging.info(f"Loading descriptor from {ENV.APP}/descriptor.py")
desc_file = importlib.import_module(f"{ENV.APP}.descriptor")
app_def = bento.Bento(desc_file.descriptor)
app_def.write(app_output="bento_app.py")

# Gunicorn requires an object containing the server: app.server
from bento_app import app  # noqa

bento_flask = app.server

# When not deploying on the web, you can run the entrypoint without Gunicorn
if __name__ == "__main__":
    logging.info("Running development server with hot-reload")
    app.run_server(host="0.0.0.0", port=ENV.BENTO_PORT, debug=True)
