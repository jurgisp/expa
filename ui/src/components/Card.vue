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
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { state, experimentsJoin, runsJoin } from "@/state";
import { getPlot } from "@/api";
import { cmd } from "@/commands";
import { COLORS } from "@/utils";

import CardPlot from "./CardPlot.vue";

const props = defineProps<{
  metric: string;
  pinned: boolean;
  pinnedFirst?: boolean;
  pinnedLast?: boolean;
}>();

const initData = [{ facet: "", groups: [] as any[] }];
const data = ref(initData);

const enabled = computed(() => experimentsJoin.value.length > 0);

const {
  data: response,
  error,
  refetch,
  isFetching,
} = useQuery({
  queryKey: [
    "plot",
    props.metric,
    experimentsJoin,
    runsJoin,
    computed(() => state.value.report.groupBy),
    computed(() => state.value.report.facetBy),
    computed(() => state.value.report.bins),
    computed(() => state.value.report.xaxis),
    computed(() => state.value.report.xmin),
    computed(() => state.value.report.xmax),
    computed(() => state.value.report.stepAgg),
    computed(() => state.value.report.runAgg),
    computed(() => state.value.report.complete),
  ],
  queryFn: () =>
    getPlot(
      props.metric,
      experimentsJoin.value,
      runsJoin.value,
      state.value.report.groupBy,
      state.value.report.facetBy,
      state.value.report.bins,
      state.value.report.xaxis,
      state.value.report.xmin,
      state.value.report.xmax,
      state.value.report.stepAgg,
      state.value.report.runAgg,
      state.value.report.complete
    ),
  // Do not cache plot data.
  // If we do, we get update-refetch-update on run change, which is annoying.
  gcTime: 0,
  enabled: enabled,
});

watch([response, enabled], ([response, enabled]) => {
  if (!enabled) {
    data.value = initData;
  } else if (response) {
    if (response.data.length > 0) {
      data.value = response.data;
    } else {
      data.value = initData; // In case of empty data, show one empty plot
    }
  }
});

cmd.on("refresh", refetch);
onBeforeUnmount(() => cmd.off("refresh", refetch));
</script>

<template>
  <div class="bg-white relative text-gray-600 border">
    <div v-if="error" class="bg-red-200 p-1 text-xs">
      {{ error.message }}
    </div>
    <div class="overflow-hidden relative" style="height: 0.125rem">
      <div v-if="isFetching" class="progress-bar bg-purple-400"></div>
    </div>
    <div class="absolute right-0 top-1 text-right pr-2">
      <span
        title="Pin to report"
        v-if="!pinned"
        @click.stop="$emit('add')"
        class="btn-icon material-symbols-outlined"
      >
        add
      </span>
      <span
        title="Move up"
        v-if="pinned && !pinnedFirst"
        @click.stop="$emit('moveUp')"
        class="btn-icon material-symbols-outlined"
      >
        chevron_left
      </span>
      <span
        title="Move down"
        v-if="pinned && !pinnedLast"
        @click.stop="$emit('moveDown')"
        class="btn-icon material-symbols-outlined"
      >
        chevron_right
      </span>
      <span
        title="Remove from report"
        v-if="pinned"
        @click.stop="$emit('remove')"
        class="btn-icon material-symbols-outlined"
      >
        remove
      </span>
    </div>
    <div class="mt-1 flex flex-col items-center">
      <p class="w-64 text-center truncate font-bold" :title="metric">
        {{ metric }}
      </p>
    </div>
    <!-- Plots -->
    <div class="flex flex-wrap">
      <div v-for="facetData in data" :key="facetData.facet">
        <div class="flex flex-col items-center">
          <p class="w-64 text-center truncate" :title="facetData.facet">
            {{ facetData.facet }}
          </p>
          <CardPlot :key="facetData.facet" :data="facetData.groups" />
        </div>
      </div>
    </div>
    <!-- Legend -->
    <div v-if="state.report.legend && data && data.length > 0" class="px-1">
      <!-- TODO: legend -->
      <div v-for="group in data[0].groups" class="flex flex-row">
        <div
          :style="{
            backgroundColor: COLORS[group.group_index % COLORS.length],
          }"
          class="size-3 mr-1"
        ></div>
        <div>
          {{ group.group }}
        </div>
      </div>
    </div>
  </div>
</template>
