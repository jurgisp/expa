# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Build:
#   docker build . -t expa
# Launch ingest worker:
#   docker run -it expa ingest.py
# Launch api:
#   docker run -it expa -m uvicorn api:app

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y \
    build-essential software-properties-common \
    && apt-get clean

# Python
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.11-dev python3.11-venv && apt-get clean
RUN python3.11 -m venv "/app/venv" --upgrade-deps
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools

WORKDIR /app/expa

# app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["/app/venv/bin/python", "-m", "uvicorn", "api:app", "--host=0.0.0.0", "--port=8010", "--workers=4"]
