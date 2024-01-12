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
import requests


class Client:
  """API client."""

  def __init__(self, api_url: str):
    self.api_url = api_url.rstrip('/')

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
    scalars = {
        k: float(v)
        for k, v in data.items()
        if v.ndim == 0 and np.issubdtype(v.dtype, np.number)
    }
    nonscalars = [k for k in data.keys() if k not in scalars]
    if nonscalars:
      print(f'WARN: dropping non-scalars in expa api client {nonscalars}')
    requests.post(
        self.api_url + '/log_metrics',
        json=dict(
            data=scalars,
            project=project,
            user=user,
            exp=exp,
            run=run,
            step=step,
            timestamp=timestamp,
        ),
    ).raise_for_status()

  def log_params(
      self,
      params: dict[str, str],
      project: str,
      user: str,
      exp: str,
      run: str,
  ):
    requests.post(
        self.api_url + '/log_params',
        json=dict(
            params=params,
            project=project,
            user=user,
            exp=exp,
            run=run,
        ),
    ).raise_for_status()

  def flush(self):
    pass
