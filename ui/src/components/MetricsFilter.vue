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
import { ref, computed, watchEffect, watch } from "vue";
import { useQuery } from "@tanstack/vue-query";
import { state, stateComp } from "@/state";
import { getMetrics } from "@/api";
import { cmd } from "@/commands";
import { watchDebounced } from "@/utils";

const defaultLimit = 25;
const initFilter = ".*";

const filterInput = ref(initFilter);
const filter = ref(initFilter);
const limit = ref(defaultLimit);

const filterElement = ref(null as HTMLInputElement | null);

watchDebounced(filterInput, (newFilter) => {
  filter.value = newFilter;
  limit.value = defaultLimit;
});

function resetFilter() {
  const v = state.reportIndex == 0 ? initFilter : "";
  filter.value = v;
  filterInput.value = v;
}

const enabled = computed(
  () => state.experiments.length > 0 && filter.value.length > 1
);

const {
  data: response,
  error,
  isPending,
  refetch,
} = useQuery({
  queryKey: [
    "metrics",
    computed(() => state.project),
    computed(() => stateComp.xids),
    filter,
    limit,
  ],
  queryFn: () =>
    getMetrics(state.project, stateComp.xids, filter.value, limit.value),
  enabled: enabled,
});

watchEffect(() => {
  if (!enabled.value) {
    state.metrics = [];
  } else if (response.value) {
    state.metrics = response.value.data.metrics;
  }
});

watch(
  // On report change
  computed(() => state.reportIndex),
  () => resetFilter()
);

cmd.on("refresh", refetch);
cmd.on("focusMetricSearch", () => filterElement.value?.focus());
</script>

<template>
  <div>
    <input
      type="search"
      v-model="filterInput"
      class="p-1 text-xs w-full"
      placeholder="Metric search"
      ref="filterElement"
    />
  </div>
  <div class="text-gray-400">
    <span v-if="!enabled">
      Select experiment and enter query (.* for all).
    </span>
    <span v-else-if="isPending"> Loading... </span>
    <span v-else-if="error" class="text-red-500">
      Error loading metrics: {{ error.message }}
    </span>
    <span v-else-if="response">
      Found {{ response.data.total }} metrics.
      <span v-if="response.data.truncated">
        Showing first {{ response.data.metrics.length }}.
        <button
          @click.stop="limit *= 2"
          class="text-blue-400 cursor-pointer hover:text-blue-500"
        >
          Load more
        </button>
      </span>
    </span>
    <span v-else class="text-red-500"> DEBUG: should not happen </span>
  </div>
</template>
