/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import axios, { type AxiosInstance } from "axios";

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL, // see .env.development
  timeout: 30000,
});

export function getExperiments(
  project: string,
  filter: string,
  max_age: number
) {
  return api.get("/experiments", {
    params: { project, filter, max_age },
  });
}

export function getRuns(project: string, xids: string) {
  return api.get("/runs", {
    params: { project, xids },
  });
}

export function getMetrics(
  project: string,
  xids: string,
  filter: string,
  limit: number
) {
  return api.get("/metrics", {
    params: { project, xids, filter, limit },
  });
}

export function getPlot(
  project: string,
  metric: string,
  xids: string,
  rids: string | null,
  groupby: string,
  facetby: string,
  bins: number,
  xaxis: string,
  xmin: number | null,
  xmax: number | null,
  stepagg: string,
  runagg: string,
  complete: boolean
) {
  return api.get("/plot", {
    params: {
      project,
      xids,
      rids,
      metric,
      groupby,
      facetby,
      bins,
      xaxis,
      xmin: xmin === null ? -1 : xmin,
      xmax: xmax === null ? -1 : xmax,
      stepagg,
      runagg,
      complete,
    },
  });
}
