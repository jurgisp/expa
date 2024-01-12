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

import { state, experimentsJoin } from "@/state";
import { getRuns } from "@/api";
import { cmd } from "@/commands";
import { regexFilter, watchDebounced } from "@/utils";

const multiExp = computed(() => state.value.experiments.length > 1);

// Filter box
const filter = ref("");
const filterElement = ref(null as HTMLInputElement | null);
watch(experimentsJoin, () => {
  // Reset on experiment change
  // TODO: if something is selected and experiment changes, the rid filter
  // is applied to new experiment with previously selected rids, until new
  // runs are loaded. We should clear runs right away, but it's tricky.
  filter.value = "";
});

// Data
// TODO: disable if no experiment selected
const { data, error, isFetching, refetch } = useQuery({
  queryKey: ["runs", experimentsJoin],
  queryFn: () => getRuns(experimentsJoin.value),
});
const runsAll = computed(() =>
  data.value ? (data.value.data as any[]) : null
);
const runsFiltered = computed(() => {
  let runs = runsAll.value;
  if (!runs) return null;
  // Filter applied on client side
  if (filter.value !== "") {
    runs = regexFilter(runs, filter.value, (r) => r.name);
  }
  return runs;
});

// Run selection
const selected = ref([] as number[]);
watch(runsFiltered, (runs, runsPrev) => {
  const rids = runs?.map((r) => r.rid);
  const ridsPrev = runsPrev?.map((r) => r.rid);
  if (rids && rids?.join(",") !== ridsPrev?.join(",")) {
    // Select all on filter change
    selected.value = rids;
  }
});
watchDebounced(selected, (rids) => {
  if (runsAll.value && rids.length < runsAll.value.length) {
    // Filter or selection applied
    state.value.runs = [...rids].sort();
  } else {
    // No filter
    state.value.runs = null;
  }
});

// UI

function triggerCheckbox(value) {
  // Emulates the effect of clicking the checkbox, since we override
  // the default click event
  const ix = selected.value.indexOf(value);
  let newSelected =
    ix >= 0
      ? [...selected.value.slice(0, ix), ...selected.value.slice(ix + 1)]
      : [...selected.value, value];
  if (newSelected.length == 0) {
    // Deselecting all => Select all
    if (runsFiltered.value && runsFiltered.value.length > 0) {
      newSelected = runsFiltered.value.map((r) => r.rid);
    }
  }
  selected.value = newSelected;
}

cmd.on("refresh", refetch);
cmd.on("focusRunFilter", () => filterElement.value?.focus());
</script>

<template>
  <div class="h-full w-full overflow-scroll bg-slate-200 text-sm">
    <!-- Filters -->
    <div class="border-b border-slate-400 text-xs p-1">
      <div>
        <input
          type="search"
          v-model="filter"
          class="p-1 text-xs w-full"
          placeholder="Run filter"
          ref="filterElement"
        />
      </div>
    </div>
    <!-- Runs -->
    <div class="bg-gray-100">
      <div v-if="error" class="bg-red-200 p-1 text-xs">
        {{ error.message }}
      </div>
      <div class="overflow-hidden relative" style="height: 0.125rem">
        <div v-if="isFetching" class="progress-bar bg-purple-400"></div>
      </div>
      <div v-if="runsFiltered">
        <div
          v-for="run in runsFiltered"
          :key="run.rid"
          class="whitespace-nowrap px-1 border-b border-gray-300 cursor-pointer"
          @click.stop="selected = [run.rid]"
        >
          <div class="text-xs py-1">
            <input
              type="checkbox"
              :value="run.rid"
              v-model="selected"
              class="checkbox"
              @click.stop="triggerCheckbox(run.rid)"
            />
            <span v-if="multiExp" class="text-gray-400">
              {{ run.exp }} /
            </span>
            <span>{{ run.name }}</span>
          </div>
          <!-- <div class="text-xs text-gray-400 pl-4">
            <span>{{ formatSteps(run.max_step) }} steps / </span>
            <span :class="{ 'text-green-600': run.age < 300 }">
              {{ formatAge(run.age) }} ago
            </span>
          </div> -->
        </div>
      </div>
    </div>
  </div>
</template>
