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

from typing import Optional
import numpy as np
import pandas as pd

from . import sql_store


class Repository:

  def __init__(
      self,
      dsn: str,
      readonly: bool = False,
      max_conn: int = 20,
      log: bool = False,
  ):
    self._db = sql_store.PgSqlStore(
        dsn, readonly=readonly, max_conn=max_conn, log=log
    )

  async def init(self):
    await self._db.init()
    print(f'Connected to {self._db.dsn}')

  ##################
  # Write
  ##################

  async def write_metrics(
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
        if v.ndim == 0 and np.issubdtype(v.dtype, np.number) and k != ''
    }
    # TODO: silently ignores non-scalars for now
    if scalars:
      await self._db.write_metrics(
          scalars, project, user, exp, run, step, timestamp
      )

  async def write_params(
      self,
      params: dict[str, str],
      project: str,
      user: str,
      exp: str,
      run: str,
  ):
    params = {k: v for k, v in params.items() if k != ''}
    await self._db.write_params(params, project, user, exp, run)

  ##################
  # Read
  ##################

  async def get_experiments(
      self, project: str, with_stats=True
  ) -> pd.DataFrame:
    if with_stats:
      return await self._db.get_experiments_with_stats(project)
    else:
      return await self._db.get_experiments(project)

  async def get_runs(self, project: str, xids: list[int]) -> pd.DataFrame:
    df = await self._db.get_runs(project, xids)
    return df

  async def get_metrics(self, project: str, xids: list[int]) -> pd.DataFrame:
    return await self._db.get_metrics(project, xids)

  async def plot_metrics(
      self,
      project: str,
      metric: str,
      xids: list[int],
      rids: Optional[list[int]],
      *,
      groupby: list[str],
      bins: int,
      xaxis: str = 'step',
      xmin: Optional[int] = None,
      xmax: Optional[int] = None,
      stepagg: str = 'mean',
      runagg: str = 'mean',
      complete: bool = False,
  ) -> pd.DataFrame:
    return await self._db.plot_metrics(
        project,
        metric,
        xids,
        rids,
        groupby,
        bins,
        xaxis,
        xmin,
        xmax,
        stepagg,
        runagg,
        complete,
    )
