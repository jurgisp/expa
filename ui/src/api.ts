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

export interface ExperimentsResponse {
  experiments: {
    xid: number;
    name: string;
    note: string;
    run_count: number;
    max_step: number;
    max_step_complete: number;
    age: number;
    age_complete: number;
  }[];
}
export function getExperiments(
  project: string,
  filter: string,
  max_age: number
) {
  return api.get<ExperimentsResponse>("/experiments", {
    params: { project, filter, max_age },
  });
}

export interface RunsResponse {
  runs: {
    rid: number;
    name: string;
    exp: string;
    max_step: number;
    age: number;
  }[];
}
export function getRuns(project: string, xids: string) {
  return api.get<RunsResponse>("/runs", {
    params: { project, xids },
  });
}

export interface MetricsResponse {
  metrics: { metric: string }[];
  total: number;
  truncated: boolean;
}
export function getMetrics(
  project: string,
  xids: string,
  filter: string,
  limit: number
) {
  return api.get<MetricsResponse>("/metrics", {
    params: { project, xids, filter, limit },
  });
}

export interface PlotResponse {
  facets: PlotResponseFacet[];
}
export interface PlotResponseFacet {
  facet: string;
  groups: {
    group: string;
    group_index: number;
    step: number[];
    value: (number | null)[];
  }[];
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
  return api.get<PlotResponse>("/plot", {
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
