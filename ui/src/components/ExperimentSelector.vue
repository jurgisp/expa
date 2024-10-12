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
import RadioSelect from "./elements/RadioSelect.vue";

// Filter box
const filterInput = ref("");
const filter = ref("");
watchDebounced(filterInput, (value) => (filter.value = value));
const filterElement = ref(null as HTMLInputElement | null);

// Running checkbox
const runningMaxAge = 300;
const running = ref(false);
const age = computed(() => (running.value ? runningMaxAge : 0));

// Complete stats checkbox
const statsComplete = ref(false);

// Steps filter
const steps = ref(0);

// Experiment selection
const selected = computed({
  get: () => state.experiments,
  set: (value) => (state.experiments = value),
});

// Data
const { data, error, isFetching, refetch } = useQuery({
  queryKey: ["experiments", computed(() => state.project), filter, age, steps],
  queryFn: () =>
    getExperiments(state.project, filter.value, age.value, steps.value),
});
watch(data, (data) => {
  if (data) {
    // Deselect those that are not in the new list.
    const currentSelected = new Set([...selected.value]);
    const newExperiments = data.data.experiments.map((r) => r.xid.toString());
    const newSelected = newExperiments
      .filter((r1) => currentSelected.has(r1))
      .sort();
    if (selected.value.join("|") != newSelected.join("|")) {
      selected.value = newSelected;
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

cmd.on("refresh", refetch);
cmd.on("experiments.toggleRunning", () => {
  running.value = !running.value;
});
</script>

<template>
  <div class="bg-slate-200 text-sm flex flex-col">
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
      <div class="flex flex-wrap gap-2">
        <Checkbox label="Running" v-model="running" />
        <!-- <Checkbox label="Complete stats" v-model="statsComplete" /> -->
        <span>Steps:</span>
        <RadioSelect
          id="stepsRadio"
          :options="[
            [0, '0'],
            [1, '1'],
            [10000, '10k'],
            [100000, '100k'],
          ]"
          v-model="steps"
        />
      </div>
    </div>
    <!-- Experiments -->
    <div class="bg-gray-100 overflow-auto">
      <div v-if="error" class="bg-red-200 p-1 text-xs">
        {{ error.message }}
      </div>
      <div class="overflow-hidden relative" style="height: 0.125rem">
        <div v-if="isFetching" class="progress-bar bg-purple-400"></div>
      </div>
      <div v-if="data">
        <div
          v-for="exp in data.data.experiments"
          :key="exp.xid"
          class="whitespace-nowrap px-1 border-b border-gray-300 cursor-pointer"
          @click.stop="selected = [exp.xid.toString()]"
        >
          <div>
            <input
              type="checkbox"
              :value="exp.xid.toString()"
              v-model="selected"
              class="checkbox"
              @click.stop="triggerCheckbox(exp.xid.toString())"
            />
            <span>{{ exp.name }}</span>
          </div>
          <div class="text-xs text-gray-600 pl-4">
            {{ exp.note }}
          </div>
          <div class="text-xs text-gray-400 pl-4">
            <span> {{ exp.run_count }} runs / </span>
            <span v-if="!statsComplete">
              <span>{{ formatSteps(exp.max_step) }} steps / </span>
              <span :class="{ 'text-green-600': exp.age < 300 }">
                {{ formatAge(exp.age) }} ago
              </span>
            </span>
            <span v-else>
              <span>{{ formatSteps(exp.max_step_complete) }} steps / </span>
              <span :class="{ 'text-green-600': exp.age_complete < 300 }">
                {{ formatAge(exp.age_complete) }} ago
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
