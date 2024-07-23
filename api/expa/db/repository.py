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

from .sql_store import PgSqlStore
from .kv_store import FileKVStore


class Repository:

  def __init__(
      self,
      sql_dsn: str,
      filestore_dir: str,
      readonly: bool = False,
      max_conn: int = 20,
      log: bool = False,
  ):
    self._db = PgSqlStore(sql_dsn, readonly=readonly, max_conn=max_conn, log=log)
    self._kv = FileKVStore(filestore_dir)

  async def init(self):
    await self._db.init()

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
    data.pop('', None)  # Empty key not allowed

    scalars = {
        k: float(v)
        for k, v in data.items()
        if v.ndim == 0 and np.issubdtype(v.dtype, np.number)
    }
    if scalars:
      await self._db.write_metrics(
          scalars, project, user, exp, run, step, timestamp
      )

    tensors = {k: v for k, v in data.items() if k not in scalars}
    if tensors:
      # Metadata about tensors is written to SQL, and the actual data to KV store
      shapes_dtypes = {
          k: (','.join(str(d) for d in v.shape), str(v.dtype))
          for k, v in tensors.items()
      }
      pid, xid, rid, mids = await self._db.write_tensors_meta(
          shapes_dtypes, project, user, exp, run, step, timestamp
      )
      self._kv.write_tensors_data(tensors, pid, xid, rid, mids, step)

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
