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

import re
import time
from typing import Any

import numpy as np

from . import client as api_client

DEFAULT_CREDENTIALS = None


def set_credentials(credentials):
  global DEFAULT_CREDENTIALS
  DEFAULT_CREDENTIALS = credentials


class Logger:

  def __init__(
      self,
      exp: str,
      run: str,
      project: str = 'default',
      user: str = '',
      api_url: str = '',
      credentials=None,
  ):
    assert api_url, 'api_url required'
    self.exp = exp
    self.run = run
    self.project = project
    self.user = user
    if not api_url.startswith('pubsub://'):
      self._client = api_client.Client(api_url)
    else:
      from . import pubsub

      m = re.match(r'pubsub://([^/]+)/([^/]+)', api_url)
      assert m, 'Use pubsub://project/topic for sending data over PubSub'
      gcp_project, topic = m.groups()
      credentials = credentials or DEFAULT_CREDENTIALS
      self._client = pubsub.Client(gcp_project, topic, credentials=credentials)

    self._nonscalars = set()

  def log(self, data: dict[str, Any], step: int):
    step = int(step)
    data_np = {k: np.asarray(v) for k, v in data.items()}
    self._client.log_metrics(
        data_np,
        self.project,
        self.user,
        self.exp,
        self.run,
        step,
        time.time(),
    )

  def log_params(self, params: dict[str, Any]):
    self._client.log_params(
        {k: str(v) for k, v in params.items()},
        self.project,
        self.user,
        self.exp,
        self.run,
    )

  def flush(self):
    self._client.flush()
