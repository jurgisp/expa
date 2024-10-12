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

"""expa api.

Start:
  uvicorn api:app --reload --host 0.0.0.0 --port 8010
"""

import contextlib
import io
import os
import re
import time
import traceback
from datetime import datetime
from typing import Optional

import fastapi
import numpy as np
import pandas as pd
import pydantic as pyd
import uvicorn
from fastapi import HTTPException
from fastapi.middleware import cors, gzip
from PIL import Image

import expa.db


def filter_regex(df: pd.DataFrame, column: str, pattern: str):
  if not pattern:
    return df
  df = df[~df[column].isna()]
  try:
    df = df[df[column].str.contains(pattern, case=False)]
  except re.error:
    # Fallback to substring match if invalid regex
    df = df[df[column].str.contains(pattern, case=False, regex=False)]
  return df


def parse_xids(xids: str = fastapi.Query(...)) -> list[int]:
  try:
    return [int(v) for v in xids.split(',') if v != '']
  except ValueError:
    raise HTTPException(status_code=400, detail=f'Not integers: {xids}')


def parse_rids(rids: str = fastapi.Query(None)) -> Optional[list[int]]:
  # Duplicating above because the argument name must match parameter name for
  # FastAPI to wire up argument parsing.
  if rids is None:
    return None
  try:
    return [int(v) for v in rids.split(',') if v != '']
  except ValueError:
    raise HTTPException(status_code=400, detail=f'Not integers: {rids}')


def parse_groupby(groupby: str = fastapi.Query('')) -> list[str]:
  return [v for v in groupby.split(',') if v != '']


def parse_facetby(facetby: str = fastapi.Query('')) -> list[str]:
  return [v for v in facetby.split(',') if v != '']


##################
# App
##################

DB = os.environ.get('EXPA_DB', 'postgresql://postgres:postgres@localhost/postgres')
DB_READONLY = os.environ.get('EXPA_DB_READONLY', 'False') == 'True'
FILESTORE = os.environ.get('EXPA_FILESTORE', './.expa_filestore')
LOG_QUERIES = os.environ.get('EXPA_LOG_QUERIES', 'False') == 'True'

repo = expa.db.Repository(DB, FILESTORE, readonly=DB_READONLY, log=LOG_QUERIES)


@contextlib.asynccontextmanager
async def lifespan(unused_app: fastapi.FastAPI):
  # Startup
  await repo.init()
  yield
  # Shutdown
  pass


app = fastapi.FastAPI(
    lifespan=lifespan,
    # orjson converts NaNs to nulls in response
    default_response_class=fastapi.responses.ORJSONResponse,
)
app.add_middleware(gzip.GZipMiddleware, minimum_size=1000)
app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(Exception)
async def debug_exception_handler(request: fastapi.Request, exc: Exception):
  return fastapi.Response(
      content=''.join(traceback.format_exception(exc)),
      status_code=500,
  )


@app.middleware('http')
async def log_requests(request: fastapi.Request, call_next):
  def timestamp():
    return datetime.now().strftime('%H:%M:%S.%f')[:12]

  start = time.time()
  method = request.method
  url = str(request.url)
  client = request.client.host if request.client else None
  print(f'{timestamp()}: [received] {method} {url} (from {client})')
  response: fastapi.Response = await call_next(request)
  elapsed = int((time.time() - start) * 1000)
  status = response.status_code
  print(f'{timestamp()}: [response={status} in {elapsed:.0f} ms] ' f'{url} (from {client})')
  return response


##################
# Read Endpoints
##################


@app.get('/')
async def ready():
  return 'ready'


@app.get('/experiments')
async def get_experiments(project: str, filter: str = '', max_age: int = 0, min_steps: int = 0):
  df = await repo.get_experiments(project)
  if not len(df):
    return {'experiments': []}
  df['age'] = time.time() - df['last_timestamp']
  df['age_complete'] = time.time() - df['last_timestamp_complete']
  for col in ['age', 'max_step', 'age_complete', 'max_step_complete']:
    df[col] = df[col].fillna(0).astype(int)

  if max_age:
    df = df[df['age'] < max_age]  # TODO: push down to SQL

  if min_steps:
    df = df[df['max_step'] >= min_steps]

  # TODO: generalize to some simple query language?
  for filt in filter.lower().split(' and '):
    filt = filt.strip()
    if filt:
      df_byname = filter_regex(df, 'name', filt)
      df_bynote = filter_regex(df, 'note', filt)
      df = pd.concat([df_byname, df_bynote]).drop_duplicates()

  df = df.sort_values('created_at', ascending=False)
  return {'experiments': df.to_dict(orient='records')}


@app.get('/runs')
async def get_runs(
    project: str,
    xids: list[int] = fastapi.Depends(parse_xids),
    filter: str = '',
):
  df = await repo.get_runs(project, xids)
  if not len(df):
    return {'runs': []}
  df = filter_regex(df, 'name', filter)
  df['age'] = (time.time() - df['last_timestamp'].fillna(0)).astype(int)
  df['max_step'] = df['max_step'].fillna(0).astype(int)
  df = df.sort_values(['exp', 'run'])
  return {'runs': df.to_dict(orient='records')}


@app.get('/metrics')
async def get_metrics(
    project: str,
    xids: list[int] = fastapi.Depends(parse_xids),
    filter: str = '',
    limit: int = 50,
):
  df = await repo.get_metrics(project, xids)
  if len(df):
    df = filter_regex(df, 'metric', filter)
    df['is_image'] = df['shape'].apply(
        lambda shape: shape is not None and len(shape.split(',')) == 3 and shape[-1] == '3'
    )
    df = df[df['is_scalar'] | df['is_image']]
  return {
      'metrics': df.head(limit).to_dict(orient='records'),
      'total': len(df),
      'truncated': len(df) > limit,
  }


@app.get('/plot')
async def plot(
    project: str,
    metric: str,
    xids: list[int] = fastapi.Depends(parse_xids),
    rids: Optional[list[int]] = fastapi.Depends(parse_rids),
    groupby: list[str] = fastapi.Depends(parse_groupby),
    facetby: list[str] = fastapi.Depends(parse_facetby),
    bins: int = 100,
    xaxis: str = 'step',
    xmin: Optional[int] = -1,
    xmax: Optional[int] = -1,
    stepagg: str = 'mean',
    runagg: str = 'mean',
    complete: bool = False,
    aligned: bool = True,
):
  xmin = None if xmin == -1 else xmin
  xmax = None if xmax == -1 else xmax
  if not xids:
    return {'facets': []}
  if not groupby:
    # group by (exp,run) by default
    groupby = ['exp', 'run'] if len(xids) > 1 else ['run']
  df = await repo.plot_metrics(
      project,
      metric,
      xids,
      rids,
      groupby=list(set(groupby + facetby)),
      bins=bins,
      xaxis=xaxis,
      xmin=xmin,
      xmax=xmax,
      stepagg=stepagg,
      runagg=runagg,
      complete=complete,
  )
  if not len(df):
    return {'facets': []}
  # We have a choice between using `step` or `bin` for x axis
  # - `step` contains the max observed step in the bin
  # - `bin` contains the upper bound (inclusive) for steps in the bin
  # If using `bin`, series will be aligned on x, if `step` - not.
  if aligned:
    df['step'] = df['bin']
  df['group'] = df[groupby].astype(str).agg(','.join, axis=1) if groupby else ''
  df['facet'] = df[facetby].astype(str).agg(','.join, axis=1) if facetby else ''
  df = df.groupby(['facet', 'group'], as_index=False).agg(
      {
          'step': list,
          'value': list,
      }
  )
  df = df.sort_values(['facet', 'group'])
  # TODO: in order to get truly consistent colors, we should calc group_index
  # based on all runs for given filters, whether or not metric has data.
  group_index = {g: i for i, g in enumerate(sorted(df['group'].unique()))}
  df['group_index'] = df['group'].map(group_index)  # for consistent colors
  return {
      'facets': [
          {
              'facet': facet,
              'groups': dfg.to_dict(orient='records'),
          }
          for facet, dfg in df.groupby('facet')
      ]
  }


@app.get('/image')
async def get_image(
    project: str,
    metric: str,
    xid: int,
    rid: int,
    step: int = -1,  # -1 means last
):
  data = await repo.get_tensor(project, metric, xid, rid, step)
  if data is None:
    raise HTTPException(status_code=404)
  # TODO: handle batch of images
  if not (len(data.shape) == 3 and data.shape[-1] == 3):
    raise ValueError(f'Bad image shape {data.shape}')
  if data.dtype != np.uint8:
    data = (data * 256).clip(0, 255).astype(np.uint8)
  image = Image.fromarray(data)
  with io.BytesIO() as buffer:
    image.save(buffer, 'PNG')
    buffer.seek(0)
    return fastapi.Response(buffer.read(), media_type='image/png')


##################
# Write Endpoints
##################


class LogMetricsRequest(pyd.BaseModel):
  data: dict[str, float]
  project: str
  user: str
  exp: str
  run: str
  step: int
  timestamp: float


@app.post('/log_metrics')
async def log_metrics(r: LogMetricsRequest):
  data = {k: np.asarray(v) for k, v in r.data.items()}
  await repo.write_metrics(data, r.project, r.user, r.exp, r.run, r.step, r.timestamp)


@app.post('/log_tensors')
async def process_data(
    file: fastapi.UploadFile = fastapi.File(...),
    project: str = fastapi.Form(default=''),
    user: str = fastapi.Form(default=''),
    exp: str = fastapi.Form(default=''),
    run: str = fastapi.Form(default=''),
    step: int = fastapi.Form(...),
    timestamp: float = fastapi.Form(...),
):
  contents = await file.read()
  with np.load(io.BytesIO(contents)) as npz:
    data = {k: npz[k] for k in npz}
  await repo.write_metrics(data, project, user, exp, run, step, timestamp)


class LogParamsRequest(pyd.BaseModel):
  params: dict[str, str]
  project: str
  user: str
  exp: str
  run: str


@app.post('/log_params')
async def log_params(r: LogParamsRequest):
  await repo.write_params(r.params, r.project, r.user, r.exp, r.run)


if __name__ == '__main__':
  uvicorn.run(app, host='0.0.0.0', port=8010)
