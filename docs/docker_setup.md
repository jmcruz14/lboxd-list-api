# Docker Setup

### About

Docker is a containerizer application which allows the user to run
specific process, workloads, or applications on a virtual machine.

For the purposes of this build, I've used Docker to run my API from a
remote source to ensure my machine does not run into additional performance
issues from running the API in the background. (ex. Executing `./run_fastapi.sh`)

### Containerization Steps
1. Ensure you have a Dockerfile in your root folder. This is a sample Dockerfile content based from my own Dockerfile

```Dockerfile
# syntax=docker/dockerfile:1.7-labs

FROM python:3.11.7-slim
WORKDIR /app/
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

a. To omit unnecessary files from being copied over in the Docker container, create a `.dockerignore` in the same folder. Within this `.dockerignore`, you may add the files and paths that are not needed for porting.

2. To start containerizing, you must first **build an image**. 

```zsh
docker build -t <IMAGE_NAME>:<TAG_NAME> .
```

This statement simply executes a `docker build` command to create an image named `IMAGE_NAME` with the tag `TAG_NAME` from the current working directory.

_Example_: lboxd-api:v0.2

3. After Step 2, the image should be built and you can check it by running `docker images`. If you see it in the list of images, the image is confirmed to have been stored in Docker's repository.

4. To create the corresponding container, we use the `docker run` statement to execute containerization of the image.

```zsh
docker run --name <CONTAINER_NAME> -p <PORT_CONNECTION> -d <IMAGE_NAME>:<TAG_NAME>
```

This executes a `docker run` command to run a new container named `CONTAINER_NAME` at port `PORT_CONNECTION` in **detached mode** (-d) using image `IMAGE_NAME`. If no `TAG_NAME` is stated, Docker will pull the latest image with the same name.

5. Your docker container with the image should now be running!



Full docs: [Docker](https://docs.docker.com/)