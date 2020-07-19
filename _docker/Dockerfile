FROM derekalarson/bento:base

USER root

WORKDIR /app/
COPY . ./

# In a production environment, we use gunicorn for WSGI support
CMD gunicorn -b 0.0.0.0:$BENTO_PORT entrypoint:bento_flask
