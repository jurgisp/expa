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

import { reactive } from "vue";
import {
  reactiveComputed,
  useEventListener,
  useStorage,
  watchDeep,
} from "@vueuse/core";
import { deepCopy, parseFloatInput, parseIntInput } from "@/utils";

interface Card {
  metric: string;
}

interface Report {
  cards: Card[];
  name: string;
  bins: number;
  groupBy: string;
  facetBy: string;
  stepAgg: string;
  runAgg: string;
  complete: boolean;
  xaxis: string;
  xmin: string; // Keep as strings for easier binding
  xmax: string;
  ymin: string;
  ymax: string;
  legend: boolean;
}

interface State {
  project: string;
  experiments: string[];
  runs: string[] | null; // Null means all
  metrics: Card[]; // Search result metrics  // TODO: maybe not part of state?
  report: Report; // Current report (in edited state)
  reportIndex: number; // Which report is being edited
}

const defaultReport: Report = {
  cards: [],
  name: "New",
  bins: 200,
  groupBy: "",
  facetBy: "",
  stepAgg: "mean",
  runAgg: "mean",
  complete: false,
  xaxis: "step",
  xmin: "",
  xmax: "",
  ymin: "",
  ymax: "",
  legend: false,
};

// State (not persisted, reflected in URL)
export const state = reactive({
  project: "default",
  experiments: [],
  runs: null,
  metrics: [],
  report: deepCopy(defaultReport),
  reportIndex: 0,
} as State);

// Computed state properties
export const stateComp = reactiveComputed(() => ({
  xids: state.experiments.join(","),
  rids: state.runs?.join(",") ?? null,
  report: {
    xmin: parseIntInput(state.report.xmin),
    xmax: parseIntInput(state.report.xmax),
    ymin: parseFloatInput(state.report.ymin),
    ymax: parseFloatInput(state.report.ymax),
  },
}));

// Reports (persisted)
export const reports = useStorage("reports", [
  deepCopy(defaultReport), // First is special "New" report
] as Report[]);

// Patch reports
reports.value[0] = deepCopy(defaultReport);
reports.value.forEach((report, i) => {
  if (Object.keys(report).join(",") !== Object.keys(defaultReport).join(",")) {
    console.log(`Patching report: ${report.name}`);
    Object.keys(defaultReport).forEach((key) => {
      if (!(key in report)) {
        report[key] = deepCopy(defaultReport[key]);
      }
    });
    Object.keys(report).forEach((key) => {
      if (!(key in defaultReport)) {
        console.log("DEBUG: delete key", key);
        delete report[key];
      }
    });
  }
});

//##################
// URL state
//##################

interface UrlParams {
  // Params track non-default state values
  project?: string;
  xids?: string;
  rids?: string;
  ymin?: string;
  ymax?: string;
}

function getStateParams(state: State): UrlParams {
  const params = {} as UrlParams;
  if (state.project != "default") params.project = state.project;
  if (state.experiments.length) params.xids = state.experiments.join(",");
  if (state.runs?.length) params.rids = state.runs.join(",");
  if (state.report.ymin) params.ymin = state.report.ymin;
  if (state.report.ymax) params.ymax = state.report.ymax;
  // TODO: all report properties (solve delay bound)
  // TODO: metric search query
  return params;
}

function setStateParams(state: State, params: UrlParams) {
  state.project = params.project ?? "default";
  state.experiments = params.xids?.split(",") ?? [];
  state.runs = params.rids?.split(",") ?? null;
  state.report.ymin = params.ymin ?? "";
  state.report.ymax = params.ymax ?? "";
}

function buildUrl(params: UrlParams): string {
  const pathname = params["project"] ?? "";
  delete params["project"];
  const search = Object.entries(params)
    .map(([key, value]) => `${key}=${encode(value)}`)
    .join("&");
  return `/${pathname}${search ? "?" : ""}${search}`;
}

function parseUrl(): UrlParams {
  const pathname = window.location.pathname.replace(/^\//, "");
  const search = window.location.search.replace(/^\?/, "");
  const params = {} as UrlParams;
  if (pathname) params.project = pathname;
  if (search) {
    search.split("&").forEach((pair) => {
      let [key, value] = pair.split("=");
      params[key] = decodeURIComponent(value);
    });
  }
  return params;
}

function setUrl(url: string) {
  const oldUrl = window.location.pathname + window.location.search;
  if (oldUrl == url) {
    // Url->State->Url conversion must be consistent, for this to prevent
    // pushing another url to history after navigating back.
    return;
  }
  window.history.pushState(null, "", url);
  console.log("setUrl:", oldUrl, "->", url);
}

function encode(str: string) {
  // Leave commas alone for readability
  return encodeURIComponent(str).replace(/%2C/g, ",");
}

function setStateFromUrl() {
  console.log("From URL:", window.location.href, parseUrl());
  setStateParams(state, parseUrl());
}

setStateFromUrl();
console.log("State initial:", JSON.stringify(state));

watchDeep(state, () => {
  console.log("State changed:", JSON.stringify(state));
  setUrl(buildUrl(getStateParams(state)));
});

useEventListener(window, "popstate", setStateFromUrl, false);
