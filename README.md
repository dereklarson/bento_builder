# Bento Builder

[![GitHub](https://img.shields.io/github/license/dereklarson/bento?style=for-the-badge)](https://github.com/dereklarson/bento/blob/master/LICENSE)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/dereklarson/bento?style=for-the-badge)](https://github.com/dereklarson/bento/graphs/contributors)

### *A workspace for running and Dockerizing [Bento](https://github.com/dereklarson/bento)*

This workspace will help you:
* Develop your dashboard with hot-reload
* Build a deployable Docker image
* Specify the deployment enviroment (docker-compose.yaml)
* Organize a repository of dashboard apps

## Quickstart
Dependencies: Python 3.7+ and Bento

To download Bento:
`pip3 install --index-url https://test.pypi.org/simple/ bento-dash==0.1.4`
(Bento is only up on the PyPI test server for now)

Clone this repo:
`git clone https://github.com/dereklarson/bento_builder.git`

Try generating the simplest example:
`./build.py simple_example`
You should see `bento_app.py` in `_build/simple_example`

Now locally run the simple example dashboard:
`./build.py simple_example -x` (using the -x "execute" flag)
The dashboard should be up at `localhost:7777` in your browser

You can then try building a Docker image and running a container:
`./build.py simple_example -bu` (using the -b "build" and -u "up" flags)

If you want to edit with hot-reload, it's recommended to use Docker. 
`./build.py simple_example -dbu` (includes the -d "dev" flag)
This adds in the dev-docker-compose.yaml specs, which mounts the project directory
into the container's working directory. Thus, editing your `descriptor.py` will cause
the Flask server to regenerate the Bento app and reflect your changes.

## Creating your own dashboard project

To initiate your own dashboard, I recommend the following steps:
* Create a new directory with your app name
* Copy `simple_example/descriptor.py` to the new directory
* Prepare code that can load a dataframe for Bento (see `covid_full/df_covid_us.py`)
* Connect your dataset to your Bento app
