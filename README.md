# Bento Builder

[![GitHub](https://img.shields.io/github/license/dereklarson/bento_builder?style=for-the-badge)](https://github.com/dereklarson/bento_builder/blob/master/LICENSE)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/dereklarson/bento_builder?style=for-the-badge)](https://github.com/dereklarson/bento_builder/graphs/contributors)

### *A workspace for running and Dockerizing [Bento](https://github.com/dereklarson/bento)*

This workspace will help you:
* Develop your dashboard with hot-reload
* Build a deployable Docker image
* Specify the deployment enviroment (docker-compose.yaml)
* Organize a repository of dashboard apps

## Quickstart
Dependencies: Python 3.7+ and [Bento](https://github.com/dereklarson/bento)

You will also want [Docker installed](https://docs.docker.com/get-docker/)
to get the most out of this repository.

##### Clone this repo:
`git clone https://github.com/dereklarson/bento_builder.git`

##### Try locally serving the simple example dashboard:
`./build.py simple_example -x` (using the -x "execute" flag)

*After some log output, the dashboard should be up at `localhost:7777` in your browser.*

This is useful if you're not familiar with Docker yet, or want to determine whether
a bug is dependent on the Docker environment.

##### Also try building a Docker image and running a container:
`./build.py simple_example -bu` (using the -b "build" and -u "up" flags)

In this case the dataset is included in the build (it's small), so you could now
use this image in a deployment.

##### Test editing with hot-reload, it's recommended to use Docker: 
`./build.py simple_example -dbu` (includes the -d "dev" flag)

This adds in the dev-docker-compose.yaml specs, which mounts the project directory
into the container's working directory. Thus, editing `simple_example/descriptor.py`
will cause the Flask server to regenerate the Bento app and reflect your changes.

## Creating your own dashboard project

To initiate your own dashboard, I recommend the following steps:
* Create a new directory with your app name
* Copy `housing/descriptor.py` to the new directory
* Prepare code that can load a dataframe for Bento (see `housing/df_snapshot.py`)
* Connect your dataset to your Bento app by modifying `descriptor.py`
