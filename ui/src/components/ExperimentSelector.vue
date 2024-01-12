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
import { ref, watch, computed } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { state } from "@/state";
import { getExperiments } from "@/api";
import { cmd } from "@/commands";
import { formatAge, formatSteps, watchDebounced } from "@/utils";

import Checkbox from "./elements/Checkbox.vue";

// Filter box
const filterInput = ref("");
const filter = ref("");
watchDebounced(filterInput, (value) => (filter.value = value));
const filterElement = ref(null as HTMLInputElement | null);

// Running checkbox
const runningMaxAge = 300;
const running = ref(import.meta.env.DEV);  // DEBUG: defaults to running
const age = computed(() => (running.value ? runningMaxAge : 0));

// Experiment selection
const selected = ref([] as number[]);
watch(selected, (newSelected) => {
  state.value.experiments = [...newSelected].sort();
});

// Data
const { data, error, isFetching, refetch } = useQuery({
  queryKey: ["experiments", filter, age],
  queryFn: () => getExperiments(filter.value, age.value),
});
watch(data, (data) => {
  if (data) {
    // Deselect those that are not in the new list.
    const currentSelected = new Set([...selected.value]);
    const newExperiments = data.data.map((r) => r.xid);
    const newSelected = newExperiments
      .filter((r1) => currentSelected.has(r1))
      .sort();
    if (selected.value.join("|") != newSelected.join("|")) {
      selected.value = newSelected;
    }
    if (import.meta.env.DEV) {
      // DEBUG: select first by default
      if (currentSelected.size == 0 && newExperiments.length > 0) {
        selected.value = [newExperiments[0]];
      }
    }
  }
});

function triggerCheckbox(value) {
  // Emulates the effect of clicking the checkbox, since we override
  // the default click event
  const ix = selected.value.indexOf(value);
  selected.value =
    ix >= 0
      ? [...selected.value.slice(0, ix), ...selected.value.slice(ix + 1)]
      : [...selected.value, value];
}

// function selectPrev() {
//   if (!data || !data.value || data.value.data.length == 0) {
//     return;
//   }
//   const exps = data.value.data.map((r) => r.xid);
//   if (selected.value.length == 0) {
//     selected.value = [exps[exps.length - 1]];
//   } else if (selected.value.length == 1) {
//     const ix = exps.indexOf(selected.value[0]) - 1;
//     if (ix >= 0) {
//       selected.value = [exps[ix]];
//     }
//   }
// }

// function selectNext() {
//   if (!data || !data.value || data.value.data.length == 0) {
//     return;
//   }
//   const exps = data.value.data.map((r) => r.xid);
//   if (selected.value.length == 0) {
//     selected.value = [exps[0]];
//   } else if (selected.value.length == 1) {
//     const ix = exps.indexOf(selected.value[0]) + 1;
//     if (ix < exps.length) {
//       selected.value = [exps[ix]];
//     }
//   }
// }

cmd.on("refresh", refetch);
// cmd.on("prevExperiment", selectPrev);
// cmd.on("nextExperiment", selectNext);
</script>

<template>
  <div class="h-full w-full overflow-scroll bg-slate-200 text-sm">
    <!-- Filters -->
    <div class="border-b border-slate-400 text-xs p-1">
      <div>
        <input
          type="search"
          v-model="filterInput"
          class="p-1 text-xs w-full"
          placeholder="Experiment search"
          ref="filterElement"
        />
      </div>
      <div class="">
        <Checkbox label="Running" v-model="running" />
      </div>
    </div>
    <!-- Experiments -->
    <div class="bg-gray-100">
      <div v-if="error" class="bg-red-200 p-1 text-xs">
        {{ error.message }}
      </div>
      <div class="overflow-hidden relative" style="height: 0.125rem">
        <div v-if="isFetching" class="progress-bar bg-purple-400"></div>
      </div>
      <div v-if="data">
        <div
          v-for="exp in data.data"
          :key="exp.xid"
          class="whitespace-nowrap px-1 border-b border-gray-300 cursor-pointer"
          @click.stop="selected = [exp.xid]"
        >
          <div>
            <input
              type="checkbox"
              :value="exp.xid"
              v-model="selected"
              class="checkbox"
              @click.stop="triggerCheckbox(exp.xid)"
            />
            <span>{{ exp.name }}</span>
          </div>
          <div class="text-xs text-gray-600 pl-4">
            {{ exp.note }}
          </div>
          <div class="text-xs text-gray-400 pl-4">
            <span> {{ exp.run_count }} runs / </span>
            <span>{{ formatSteps(exp.max_step) }} steps / </span>
            <span :class="{ 'text-green-600': exp.age < 300 }">
              {{ formatAge(exp.age) }} ago
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
