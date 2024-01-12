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

import { ref, computed, watchEffect } from "vue";
import { useStorage } from "@vueuse/core";
import { deepCopy } from "@/utils";

interface State {
  experiments: number[];
  runs: number[] | null; // Null means all
  metrics: { metric: string }[]; // Should this be a card?
  report: Report; // This represenets current edited report
  reportIndex: number; // Which report is being edited
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
  xmin: number | null;
  xmax: number | null;
  ymin: number | null;
  ymax: number | null;
  legend: boolean;
}

interface Card {
  metric: string;
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
  xmin: null,
  xmax: null,
  ymin: null,
  ymax: null,
  legend: false,
};

// Saved reports
const reports = useStorage("reports", [
  deepCopy(defaultReport), // First is special "New" report
] as Report[]);
// Patch reports
reports.value.forEach((report, i) => {
  if (Object.keys(report).join(",") !== Object.keys(defaultReport).join(",")) {
    console.log("Patching report with new fields");
    reports.value[i] = {...defaultReport, ...report};
  }
});

// Non-saved state
const state = ref({
  experiments: [],
  runs: null,
  metrics: [],
  report: deepCopy(defaultReport),
  reportIndex: 0,
} as State);

const experimentsJoin = computed(() => state.value.experiments.join(","));
const runsJoin = computed(() => state.value.runs?.join(",") ?? null);

// TODO: state from URL
// watchEffect(() => {
//   const params = [] as string[];
//   params.push(`xids=${experimentsJoin.value ?? ""}`);
//   if (runsJoin.value) {
//     params.push(`rids=${runsJoin.value ?? ""}`);
//   }
//   const url = "/?" + params.join("&");
//   window.history.pushState(null, "", url);
// });

export { state, reports, experimentsJoin, runsJoin };
