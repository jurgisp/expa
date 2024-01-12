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
import { parseIntInput, watchDebounced } from "@/utils";

import Checkbox from "./elements/Checkbox.vue";

const groupbyInput = ref(state.value.report.groupBy);
const facetbyInput = ref(state.value.report.facetBy);
const xminInput = ref((state.value.report.xmin ?? "").toString());
const xmaxInput = ref((state.value.report.xmax ?? "").toString());
const yminInput = ref((state.value.report.ymin ?? "").toString());
const ymaxInput = ref((state.value.report.ymax ?? "").toString());

watch(
  // On report change
  computed(() => state.value.reportIndex),
  () => {
    // Update delay-bound fields.
    // TODO: implement two-way refSync with delay
    groupbyInput.value = state.value.report.groupBy;
    facetbyInput.value = state.value.report.facetBy;
    xminInput.value = (state.value.report.xmin ?? "").toString();
    xmaxInput.value = (state.value.report.xmax ?? "").toString();
    yminInput.value = (state.value.report.ymin ?? "").toString();
    ymaxInput.value = (state.value.report.ymax ?? "").toString();
  }
);

// TODO: maybe instead of delay-binding to state, we should have delay watch
// on data load.
watchDebounced(groupbyInput, (value) => {
  state.value.report.groupBy = value;
});
watchDebounced(facetbyInput, (value) => {
  state.value.report.facetBy = value;
});
watchDebounced(xminInput, (value) => {
  state.value.report.xmin = parseIntInput(value);
});
watchDebounced(xmaxInput, (value) => {
  state.value.report.xmax = parseIntInput(value);
});
// yrange applied without delay because it doesn't cause data reload
watch(yminInput, (value) => {
  state.value.report.ymin = parseIntInput(value);
});
watch(ymaxInput, (value) => {
  state.value.report.ymax = parseIntInput(value);
});

const binsOptions = [20, 50, 100, 200, 500, 1000];

cmd.on("report.settings.toggleLegend", () => {
  state.value.report.legend = !state.value.report.legend;
});
for (let i = 1; i <= 5; i++) {
  cmd.on(`report.settings.bins${i}`, () => {
    state.value.report.bins = binsOptions[i - 1];
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
          v-model="yminInput"
        />
        -
        <input
          type="text"
          class="text-xs text-black px-1 py-0 w-12"
          v-model="ymaxInput"
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
