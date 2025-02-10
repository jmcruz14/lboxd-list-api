# syntax=docker/dockerfile:1.7-labs

FROM python:3.11.7-slim

# install uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh
# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh
# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

ADD . /app
WORKDIR /app/
RUN uv sync
ENV PATH="/app/.venv/bin:$PATH"

# COPY requirements.txt .
# RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
