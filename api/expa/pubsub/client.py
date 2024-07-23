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

import numpy as np

from . import pubsub


class Client:
  """GCP PubSub-based client for writing data only."""

  def __init__(self, project: str, topic: str, credentials):
    self._pub = pubsub.Publisher(project, topic, credentials)

  def log_metrics(
      self,
      data: dict[str, np.ndarray],
      project: str,
      user: str,
      exp: str,
      run: str,
      step: int,
      timestamp: float,
  ):
    self._pub.send_metrics(
        pubsub.DataMessage(
            data=data,
            project=project,
            user=user,
            exp=exp,
            run=run,
            step=step,
            timestamp=timestamp,
        ),
    )

  def log_params(
      self,
      params: dict[str, str],
      project: str,
      user: str,
      exp: str,
      run: str,
  ):
    self._pub.send_params(
        pubsub.ParamsMessage(
            params=params,
            project=project,
            user=user,
            exp=exp,
            run=run,
        ),
        block=True,
    )

  def flush(self):
    self._pub.wait()
