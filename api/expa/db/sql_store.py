# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import time
from typing import Optional

import asyncpg as pg
import pandas as pd


class PgSqlStore:
  """PostgreSQL/AlloyDB based storage for scalar metric."""

  def __init__(
      self,
      dsn: str,
      readonly: bool = False,
      max_conn: int = 20,
      log: bool = False,
  ):
    self.dsn = dsn.replace('postgresql+alloydb://', 'postgresql://')
    self.alloydb = dsn.startswith('postgresql+alloydb://')
    self.readonly = readonly
    self.max_conn = max_conn
    self.log = log
    self._pool = None
    # project -> pid
    self._pid_cache: dict[str, int] = {}
    # (pid, exp) -> xid
    self._xid_cache: dict[tuple[int, str], int] = {}
    # (xid, run) -> rid
    self._rid_cache: dict[tuple[int, str], int] = {}
    # (pid, metric) -> mid
    self._mid_cache: dict[tuple[int, str], int] = {}
    # (rid, metric)
    self._run_metric_cache: set[tuple[int, str]] = set()

  async def init(self):
    print(f'Connecting to SQL store {self.dsn}...')
    settings = {}
    if self.alloydb:
      # Use row scan instead of index for fresh rowstore data in columnar query
      settings['google_columnar_engine.rowstore_scan_mode'] = '1'
    self._pool = await pg.create_pool(
        self.dsn,
        min_size=min(10, self.max_conn),
        max_size=self.max_conn,
        connection_class=LoggingConnection if self.log else pg.Connection,
        command_timeout=300,
        server_settings=settings
    )
    if not self.readonly:
      print('Initializing DB schema...')
      await self._init_schema()
    print(f'Connected to {self.dsn}')
    return self

  def _connect(self):
    assert self._pool is not None
    return self._pool.acquire()

  async def _init_schema(self):
    async with self._connect() as conn:
      await conn.execute(
          """
          CREATE SCHEMA IF NOT EXISTS expa;
          CREATE TABLE IF NOT EXISTS expa.projects (
              pid serial PRIMARY KEY,
              name text UNIQUE,
              creator text
          );
          CREATE TABLE IF NOT EXISTS expa.project_metrics (
              mid serial PRIMARY KEY,
              pid integer REFERENCES expa.projects(pid),
              metric text,
              UNIQUE (pid, metric)
          );
          CREATE TABLE IF NOT EXISTS expa.experiments (
              xid serial PRIMARY KEY,
              pid integer REFERENCES expa.projects(pid),
              name text,
              creator text,
              created_at float,
              UNIQUE (pid, name)
          );
          CREATE TABLE IF NOT EXISTS expa.runs (
              rid serial PRIMARY KEY,
              xid integer REFERENCES expa.experiments(xid),
              name text,
              creator text,
              created_at float,
              last_timestamp float,
              max_step bigint,
              UNIQUE (xid, name)
          );
          CREATE TABLE IF NOT EXISTS expa.run_metrics (
              rmid serial PRIMARY KEY,
              rid integer REFERENCES expa.runs(rid),
              mid integer REFERENCES expa.project_metrics(mid),
              metric text,
              is_scalar bool DEFAULT true,
              shape text,
              dtype text,
              UNIQUE (rid, mid)
          );
          CREATE TABLE IF NOT EXISTS expa.run_params (
              rpid serial PRIMARY KEY,
              rid integer REFERENCES expa.runs(rid),
              param text,
              value text,
              UNIQUE (rid, param)
          );
          CREATE TABLE IF NOT EXISTS expa.scalar_data (
              xid integer,
              rid integer,
              mid integer,
              step bigint,
              value float,
              timestamp float
          );
          CREATE INDEX IF NOT EXISTS ix_scalar_data
          ON expa.scalar_data (xid, mid, rid, step) INCLUDE (value, timestamp);
          CREATE TABLE IF NOT EXISTS expa.tensor_metadata (
              xid integer,
              rid integer,
              mid integer,
              step bigint,
              shape text,
              dtype text,
              timestamp float
          );
          CREATE INDEX IF NOT EXISTS ix_tensor_metadata
          ON expa.tensor_metadata (xid, mid, rid, step);
          """
      )

  ##################
  # Write
  ##################

  async def write_metrics(
      self,
      metrics: dict[str, float],
      project: str,
      user: str,
      exp: str,
      run: str,
      step: int,
      timestamp: float,
  ):
    assert not self.readonly
    pid = await self._get_or_create_project(project, user)
    xid = await self._get_or_create_exp(exp, pid, user)
    rid = await self._get_or_create_run(run, xid, user)
    await asyncio.gather(
        *[  # parallel calls
            self._maybe_create_run_metric(pid, rid, metric, True, None, None)
            for metric in metrics.keys()
        ]
    )
    await self._write_metrics(pid, xid, rid, metrics, step, timestamp)

  async def write_tensors_meta(
      self,
      shapes_dtypes: dict[str, tuple[str, str]],
      project: str,
      user: str,
      exp: str,
      run: str,
      step: int,
      timestamp: float,
  ) -> tuple[int, int, int, dict[str, int]]:
    assert not self.readonly
    pid = await self._get_or_create_project(project, user)
    xid = await self._get_or_create_exp(exp, pid, user)
    rid = await self._get_or_create_run(run, xid, user)
    await asyncio.gather(
        *[  # parallel calls
            self._maybe_create_run_metric(pid, rid, metric, False, shape, dtype)
            for metric, (shape, dtype) in shapes_dtypes.items()
        ]
    )
    # Calling _get_or_create_project_metric before ensures _mid_cache is filled
    mids = {m: self._mid_cache[(pid, m)] for m in shapes_dtypes.keys()}
    await self._write_tensor_meta(pid, xid, rid, shapes_dtypes, step, timestamp)
    return pid, xid, rid, mids

  async def write_params(
      self,
      params: dict[str, str],
      project: str,
      user: str,
      exp: str,
      run: str,
  ):
    assert not self.readonly
    pid = await self._get_or_create_project(project, user)
    xid = await self._get_or_create_exp(exp, pid, user)
    rid = await self._get_or_create_run(run, xid, user)
    await self._write_params(rid, params)

  async def _get_or_create_project(self, project: str, user: str) -> int:
    if pid := self._pid_cache.get(project):
      return pid
    async with self._connect() as conn:
      await conn.execute(
          """
          INSERT INTO expa.projects (name, creator)
          VALUES ($1, $2)
          ON CONFLICT (name) DO NOTHING
          """,
          project,
          user,
      )
      pid = await conn.fetchval(
          """
          SELECT pid FROM expa.projects
          WHERE name = $1
          """,
          project,
      )
      assert pid is not None
      self._pid_cache[project] = pid
      return pid

  async def _get_or_create_exp(self, exp: str, pid: int, user: str) -> int:
    if xid := self._xid_cache.get((pid, exp)):
      return xid
    async with self._connect() as conn:
      created_at = time.time()
      # TODO: this creates gaps in xids. Would be nice to have sequential xids
      await conn.execute(
          """
          INSERT INTO expa.experiments (
            pid,
            name,
            creator,
            created_at
          )
          VALUES ($1, $2, $3, $4)
          ON CONFLICT (pid, name) DO NOTHING
          """,
          pid,
          exp,
          user,
          created_at,
      )
      xid = await conn.fetchval(
          """
          SELECT xid FROM expa.experiments
          WHERE pid = $1 AND name = $2
          """,
          pid,
          exp,
      )
      assert xid is not None
      self._xid_cache[(pid, exp)] = xid
      return xid

  async def _get_or_create_run(self, run: str, xid: int, user: str) -> int:
    if rid := self._rid_cache.get((xid, run)):
      return rid
    async with self._connect() as conn:
      created_at = time.time()
      await conn.execute(
          """
          INSERT INTO expa.runs (
            xid,
            name,
            creator,
            created_at,
            last_timestamp
          )
          VALUES ($1, $2, $3, $4, $5)
          ON CONFLICT (xid, name) DO NOTHING
          """,
          xid,
          run,
          user,
          created_at,
          created_at,
      )
      rid = await conn.fetchval(
          """
          SELECT rid FROM expa.runs
          WHERE xid = $1 AND name = $2
          """,
          xid,
          run,
      )
      assert rid is not None
      self._rid_cache[(xid, run)] = rid
      return rid

  async def _maybe_create_run_metric(
      self,
      pid: int,
      rid: int,
      metric: str,
      is_scalar: bool,
      shape: str | None,
      dtype: str | None,
  ) -> None:
    if (rid, metric) in self._run_metric_cache:
      return
    mid = await self._get_or_create_project_metric(pid, metric)
    async with self._connect() as conn:
      # The shape of a metric is assumed not to change within a run
      await conn.execute(
          """
          INSERT INTO expa.run_metrics (rid, mid, metric, is_scalar, shape, dtype)
          VALUES ($1, $2, $3, $4, $5, $6)
          ON CONFLICT (rid, mid) DO NOTHING
          """,
          rid,
          mid,
          metric,
          is_scalar,
          shape,
          dtype,
      )
      self._run_metric_cache.add((rid, metric))

  async def _get_or_create_project_metric(self, pid: int, metric: str) -> int:
    if mid := self._mid_cache.get((pid, metric)):
      return mid
    async with self._connect() as conn:
      await conn.execute(
          """
          INSERT INTO expa.project_metrics (pid, metric)
          VALUES ($1, $2)
          ON CONFLICT (pid, metric) DO NOTHING
          """,
          pid,
          metric,
      )
      mid = await conn.fetchval(
          """
          SELECT mid FROM expa.project_metrics
          WHERE pid = $1 AND metric = $2
          """,
          pid,
          metric,
      )
      assert mid is not None
      self._mid_cache[(pid, metric)] = mid
      return mid

  async def _write_metrics(
      self,
      pid: int,
      xid: int,
      rid: int,
      metrics: dict[str, float],
      step: int,
      timestamp: float,
  ):
    assert metrics
    # Calling _get_or_create_project_metric before ensures _mid_cache is filled
    mids = {m: self._mid_cache[(pid, m)] for m in metrics.keys()}
    async with self._connect() as conn:
      await conn.executemany(
          """
          INSERT INTO expa.scalar_data (mid, xid, rid, step, value, timestamp)
          VALUES ($1, $2, $3, $4, $5, $6)
          """,
          [
              (mids[metric], xid, rid, step, clean_float(value), timestamp)
              for metric, value in metrics.items()
          ],
      )
      await conn.execute(
          """
          UPDATE expa.runs
          SET
            max_step = GREATEST($2, max_step),
            last_timestamp = GREATEST($3, last_timestamp)
          WHERE rid = $1
          """,
          rid,
          step,
          timestamp,
      )

  async def _write_tensor_meta(
      self,
      pid: int,
      xid: int,
      rid: int,
      shapes_dtypes: dict[str, tuple[str, str]],
      step: int,
      timestamp: float,
  ):
    assert shapes_dtypes
    # Calling _get_or_create_project_metric before ensures _mid_cache is filled
    mids = {m: self._mid_cache[(pid, m)] for m in shapes_dtypes.keys()}
    async with self._connect() as conn:
      await conn.executemany(
          """
          INSERT INTO expa.tensor_metadata (mid, xid, rid, step, shape, dtype, timestamp)
          VALUES ($1, $2, $3, $4, $5, $6, $7)
          """,
          [
              (mids[metric], xid, rid, step, shape, dtype, timestamp)
              for metric, (shape, dtype) in shapes_dtypes.items()
          ],
      )
      await conn.execute(
          """
          UPDATE expa.runs
          SET
            max_step = GREATEST($2, max_step),
            last_timestamp = GREATEST($3, last_timestamp)
          WHERE rid = $1
          """,
          rid,
          step,
          timestamp,
      )

  async def _write_params(self, rid: int, params: dict[str, str]) -> None:
    async with self._connect() as conn:
      await conn.executemany(
          """
          INSERT INTO expa.run_params (rid, param, value)
          VALUES ($1, $2, $3)
          ON CONFLICT (rid, param) DO NOTHING
          """,
          [(rid, k, v) for k, v in params.items()],
      )

  ##################
  # Read
  ##################

  async def get_experiments(
      self,
      project: str,
      xids: Optional[list[int]] = None,
  ) -> pd.DataFrame:
    async with self._connect() as conn:
      rows = await conn.fetch(
          f"""
          SELECT *
          FROM expa.experiments
          WHERE
            pid = (SELECT pid FROM expa.projects WHERE name = $1)
            AND ({xids is None} OR xid = ANY($2::integer[]))
          """,
          project,
          xids or [],
      )
    return pd.DataFrame([dict(r) for r in rows])

  async def get_experiments_with_stats(
      self,
      project: str,
      xids: Optional[list[int]] = None,
  ) -> pd.DataFrame:
    async with self._connect() as conn:
      # TODO: note on experiment
      rows = await conn.fetch(
          f"""
          SELECT
            x.*,
            COUNT(r.rid) AS run_count,
            MAX(r.last_timestamp) AS last_timestamp,
            MAX(r.max_step) AS max_step,
            MIN(r.last_timestamp) AS last_timestamp_complete,
            MIN(r.max_step) AS max_step_complete,
            MAX(p.value) AS note
          FROM expa.experiments x
          LEFT JOIN expa.runs r ON r.xid = x.xid
          LEFT JOIN expa.run_params p
            ON p.rid = r.rid AND p.param = 'note'
          WHERE
            x.pid = (SELECT pid FROM expa.projects WHERE name = $1)
            AND ({xids is None} OR x.xid = ANY($2::integer[]))
          GROUP BY x.xid
          """,
          project,
          xids or [],
      )
    return pd.DataFrame([dict(r) for r in rows])

  async def get_runs(
      self,
      project: str,
      xids: list[int],
      rids: Optional[list[int]] = None,
      with_params: Optional[list[str]] = None,
  ) -> pd.DataFrame:
    with_params = with_params or []
    async with self._connect() as conn:
      rows = await conn.fetch(
          f"""
          SELECT
            r.rid,
            r.name,
            r.created_at,
            r.last_timestamp,
            r.max_step,
            x.xid,
            x.name as exp,
            x.creator
          FROM expa.runs r
          JOIN expa.experiments x ON r.xid = x.xid
          WHERE
            x.pid = (SELECT pid FROM expa.projects WHERE name = $1)
            AND r.xid = ANY($2::integer[])
            AND ({rids is None} OR r.rid = ANY($3::integer[]))
          """,
          project,
          xids or [],
          rids or [],
      )
      df = pd.DataFrame([dict(r) for r in rows])
      if not len(df):
        return df
      # TODO: nicer way to handle "special params" such as run, exp, etc?
      df['run'] = df['name']
      if with_params:
        rows = await conn.fetch(
            """
            SELECT rid, param, value
            FROM expa.run_params
            WHERE
              param = ANY($1::text[])
              AND rid = ANY($2::integer[])
            """,
            with_params,
            df['rid'].tolist(),
        )
        dfp = pd.DataFrame([dict(r) for r in rows])
        if not len(dfp):
          # TODO: would be nice to have query method which returns empty table
          # with the right columns.
          dfp = pd.DataFrame([], columns=['rid', 'param', 'value'])

        df = df.set_index('rid')
        dfp = dfp.set_index('rid')
        for col in with_params:
          if col in df.columns:
            if col in dfp.columns:
              print(f'WARN: ignoring `{col}` param, it is a reserved column')
            continue
          df[col] = dfp[dfp['param'] == col]['value']
          df[col] = df[col].fillna('')
        df = df.reset_index()

    return df

  async def get_metrics(self, project: str, xids: list[int]) -> pd.DataFrame:
    runs_df = await self.get_runs(project, xids)
    if not len(runs_df):
      return pd.DataFrame()
    rids = runs_df['rid'].tolist()
    async with self._connect() as conn:
      rows = await conn.fetch(
          """
          SELECT DISTINCT metric, is_scalar, shape, dtype
          FROM expa.run_metrics
          WHERE rid = ANY($1::integer[])
          ORDER BY metric;
          """,
          rids,
      )
    return pd.DataFrame([dict(r) for r in rows])

  async def get_mid(self, project: str, metric: str) -> int | None:
    async with self._connect() as conn:
      mid = await conn.fetchval(
          """
          SELECT mid FROM expa.project_metrics
          WHERE
            pid = (SELECT pid FROM expa.projects WHERE name = $1)
            AND metric = $2
          """,
          project,
          metric,
      )
      return mid

  async def plot_metrics(
      self,
      project: str,
      metric: str,
      xids: list[int],
      rids: Optional[list[int]],
      groupby: list[str],
      bins: int,
      xaxis: str = 'step',
      xmin: Optional[int] = None,
      xmax: Optional[int] = None,
      stepagg: str = 'mean',
      runagg: str = 'mean',
      complete: bool = False,
  ) -> pd.DataFrame:
    assert bins <= 10_000, 'Sanity check'

    mid = await self.get_mid(project, metric)
    runs_df = await self.get_runs(
        project,
        xids,
        rids=rids,
        with_params=groupby,
    )
    if not mid or len(runs_df) == 0:
      return pd.DataFrame()

    async with self._connect() as conn:
      if xaxis == 'step':
        xmax = xmax or runs_df['max_step'].fillna(0).max()
        stepcol = 'step'

      elif xaxis == 'runtime':
        t0 = runs_df['created_at'].min()  # TODO: per-run offset
        xmax = xmax or (runs_df['last_timestamp'].max() - t0)
        stepcol = f'(timestamp - {t0})'

      else:
        assert False, xaxis

      # Determine bin size
      # For binsize=10, the bins are 1..10, 11..20, ...
      # So for bins=100 and xmax=1000 we should get binsize=10,
      # and for xmax=1001 should get binsize=11.
      binsize = (max(int(xmax), 1) - 1) // bins + 1  # type: ignore

      # Keep the query simple and just filter and group by run ids, do the rest
      # in Python. There shouldn't be too much data once it is aggregated per
      # run,stepbin.
      stepagg = {
          'mean': 'AVG',
          'min': 'MIN',
          'max': 'MAX',
          'count': 'COUNT',
      }[stepagg]
      rows = await conn.fetch(
          f"""
          SELECT
            rid,
            (CEIL({stepcol}::float / {binsize})::bigint * {binsize}) AS bin,
            MAX({stepcol}) AS step,
            {stepagg}(value) AS value
          FROM expa.scalar_data
          WHERE
            mid = {mid}
            AND xid = ANY($1::integer[])
            AND ({rids is None} OR rid = ANY($2::integer[]))
            AND {stepcol} >= $3 AND {stepcol} <= $4
          GROUP BY rid, bin
          ORDER BY rid, bin
          """,
          xids,
          rids or [],
          xmin or 0,
          xmax,
      )
      df = pd.DataFrame([dict(r) for r in rows])
      if len(df) == 0:
        return pd.DataFrame()
      if complete:
        # Drop last bin of each run as incomplete
        df = df.drop(df.groupby('rid')['bin'].idxmax())  # type: ignore

    # Aggregate runs by group
    df = df.merge(runs_df[['rid'] + groupby], on='rid')
    assert runagg in ('mean', 'min', 'max', 'count', 'median')
    df['runs'] = 1
    df = df.groupby(groupby + ['bin'], as_index=False).agg({
        'step': 'max',
        'value': runagg,
        'runs': 'sum',
    })
    df = df.sort_values(groupby + ['bin'])
    if complete:
      # Filter out incomplete groups, where runs < total_runs
      runs_df['total_runs'] = 1
      total_runs = runs_df.groupby(groupby, as_index=False).agg(
          {'total_runs': 'sum'}
      )
      df = df.merge(total_runs, on=groupby)
      df = df[df['runs'] == df['total_runs']].copy()

    return df

  async def select_tensors(
      self,
      project: str,
      metric: str,
      xids: list[int],
      rids: Optional[list[int]],
  ) -> pd.DataFrame:
    mid = await self.get_mid(project, metric)
    runs_df = await self.get_runs(
        project,
        xids,
        rids=rids,
    )
    if not mid or len(runs_df) == 0:
      return pd.DataFrame()
    async with self._connect() as conn:
      rows = await conn.fetch(
          f"""
          SELECT mid, rid, step
          FROM expa.tensor_metadata
          WHERE
            mid = {mid}
            AND xid = ANY($1::integer[])
            AND ({rids is None} OR rid = ANY($2::integer[]))
          ORDER BY step DESC
          LIMIT 100
          """,
          xids,
          rids or [],
      )
      df = pd.DataFrame([dict(r) for r in rows])
      return df


class LoggingConnection(pg.Connection):

  async def execute(self, *args, **kwargs):
    return await self._with_log(super().execute, *args, **kwargs)

  async def executemany(self, *args, **kwargs):
    return await self._with_log(super().executemany, *args, **kwargs)

  async def fetch(self, *args, **kwargs):
    return await self._with_log(super().fetch, *args, **kwargs)

  async def fetchval(self, *args, **kwargs):
    return await self._with_log(super().fetchval, *args, **kwargs)

  async def _with_log(self, func, *args, **kwargs):
    start_time = time.time()
    try:
      result = await func(*args, **kwargs)
      dt = time.time() - start_time
      if 'CLOSE ALL' not in args[0]:  # Ignore connection close queries
        print(f'Query: {args[0]}\nargs: {args[1:]}\ntime: {dt:.3f} sec')
      return result
    except Exception as e:
      raise Exception(f'Error in query: {args[0]}\nargs: {args[1:]}') from e



def clean_float(value: float) -> Optional[float]:
  # Don't use special values (NaN, Infinity, -Infinity) in DB.
  # Even though SQL supports them, it causes downstream issues.
  import math

  import numpy as np

  if math.isnan(value):
    return None  # NaNs -> NULL
  elif value == float('inf'):
    return float(np.finfo(np.float64).max)  # inf -> 1.798e308
  elif value == float('-inf'):
    return float(np.finfo(np.float64).min)  # -inf -> -1.798e308
  else:
    return value
