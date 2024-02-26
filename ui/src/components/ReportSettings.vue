<!--
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<script setup lang="ts">
import { ref, computed, watch } from "vue";

import { state } from "@/state";
import { cmd } from "@/commands";
import { watchDebounced } from "@/utils";

import Checkbox from "./elements/Checkbox.vue";

const groupbyInput = ref(state.report.groupBy);
const facetbyInput = ref(state.report.facetBy);
const xminInput = ref(state.report.xmin);
const xmaxInput = ref(state.report.xmax);

watch(
  // On report change
  computed(() => state.reportIndex),
  () => {
    // Update delay-bound fields.
    // TODO: implement two-way refSync with delay. Or delay loading not state
    groupbyInput.value = state.report.groupBy;
    facetbyInput.value = state.report.facetBy;
    xminInput.value = state.report.xmin;
    xmaxInput.value = state.report.xmax;
  }
);

watchDebounced(groupbyInput, (value) => {
  state.report.groupBy = value;
});
watchDebounced(facetbyInput, (value) => {
  state.report.facetBy = value;
});
watchDebounced(xminInput, (value) => {
  state.report.xmin = value;
});
watchDebounced(xmaxInput, (value) => {
  state.report.xmax = value;
});

const binsOptions = [20, 50, 100, 200, 500, 1000];

cmd.on("report.settings.toggleLegend", () => {
  state.report.legend = !state.report.legend;
});
for (let i = 1; i <= 5; i++) {
  cmd.on(`report.settings.bins${i}`, () => {
    state.report.bins = binsOptions[i - 1];
  });
}
</script>

<template>
  <div class="text-gray-400 flex flex-wrap">
    <div class="p-1 flex flex-wrap gap-2">
      <div>
        Step agg:
        <select
          class="text-xs text-black px-1 py-0 w-16"
          v-model="state.report.stepAgg"
        >
          <option>mean</option>
          <option>min</option>
          <option>max</option>
          <option>count</option>
        </select>
      </div>
      <div>
        bins:
        <select
          class="text-xs text-black px-1 py-0 w-16"
          v-model="state.report.bins"
        >
          <option v-for="bins in binsOptions" :value="bins">{{ bins }}</option>
        </select>
      </div>
      <div>
        <select
          class="text-xs text-black px-1 py-0 w-16"
          v-model="state.report.xaxis"
        >
          <option value="step">steps</option>
          <option value="runtime">time</option>
        </select>
      </div>
      <div>
        x:
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-16"
          v-model="xminInput"
        />
        -
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-16"
          v-model="xmaxInput"
        />
      </div>
      <div>
        y:
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-12"
          v-model="state.report.ymin"
        />
        -
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-12"
          v-model="state.report.ymax"
        />
      </div>
    </div>
    <div class="p-1 flex flex-wrap gap-2">
      <div>
        Run agg:
        <select
          class="text-xs text-black px-1 py-0 w-16"
          v-model="state.report.runAgg"
        >
          <option>mean</option>
          <option>median</option>
          <option>min</option>
          <option>max</option>
          <option>count</option>
        </select>
      </div>
      <div>
        group by:
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-16"
          v-model="groupbyInput"
        />
      </div>
      <div>
        facet by:
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-16"
          v-model="facetbyInput"
        />
      </div>
      <div>
        <Checkbox label="Hide partial" v-model="state.report.complete" />
      </div>
    </div>
  </div>
</template>
