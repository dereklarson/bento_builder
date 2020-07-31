import importlib
import os

from bento import bento
from bento.common import logger

logging = logger.fancy_logger("entrypoint")

logging.info(f"Loading descriptor from {os.environ['APP']}/descriptor.py")
desc_file = importlib.import_module(f"{os.environ['APP']}.descriptor")

# This generates the app from the descriptor
app_def = bento.Bento(desc_file.descriptor)
if app_def.valid:
    app_def.write(app_output="bento_app.py")

    # Gunicorn requires an object containing the server: app.server
    from bento_app import app  # noqa

    bento_flask = app.server

# When not deploying on the web, you can run the entrypoint without Gunicorn
if __name__ == "__main__" and app_def.valid:
    logging.info("Running development server with hot-reload")
    app.run_server(host="0.0.0.0", port=os.environ["BENTO_PORT"], debug=True)
