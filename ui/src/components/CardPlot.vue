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
import { computed, ref } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart,
  type ActiveElement,
  type ChartEvent,
  type ChartOptions,
} from "chart.js";

import { stateComp } from "@/state";
import { formatSteps, COLORS } from "@/utils";
import type { PlotResponseFacet } from "@/api";

type Point = { x: number; y: number; on: boolean };

const props = defineProps<{ data: PlotResponseFacet }>();
const emit = defineEmits(["showTooltip", "hideTooltip"]);
const element = ref(null as HTMLElement | null);

const chartOptions = computed(() => {
  const opt: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 500, // DEBUG: should not actually resize
    // @ts-ignore
    animations: false,
    scales: {
      x: {
        type: "linear",
        ticks: {
          maxRotation: 0,
          callback: (x) => formatSteps(x),
        },
        min: stateComp.report.xmin ?? undefined,
        max: stateComp.report.xmax ?? undefined,
      },
      y: {
        type: "linear",
        grace: "0%",
        min: stateComp.report.ymin ?? undefined,
        max: stateComp.report.ymax ?? undefined,
      },
    },
    interaction: {
      // aplies to both hover and tooltip
      mode: "nearest",
      axis: "x",
      intersect: false,
    },
    onHover: onHover,
    plugins: {
      // @ts-ignore
      crosshair: {
        line: { color: "#DDD", width: 0.5 },
        sync: { enabled: false },
        zoom: { enabled: true, zoomButtonClass: "reset-zoom" },
      },
    },
  };
  return opt;
});

const chartData = computed(() => {
  const datasets = props.data.groups.map((group) => ({
    label: group.group,
    data: group.step.map((x, i) => ({ x: x, y: group.value[i] })),
    borderColor: COLORS[group.group_index % COLORS.length],
    pointHoverBackgroundColor: COLORS[group.group_index % COLORS.length],
    pointHoverRadius: 3,
    borderWidth: 1.5,
    pointRadius: 0,
  }));
  return { datasets };
});

const hoverPoints = ref({} as { [key: string]: Point });
const tooltipVisible = ref(false);
const tooltipData = computed(() => {
  const hovers = hoverPoints.value;
  const groups = chartData.value.datasets.map((ds) => ({
    label: ds.label,
    color: ds.borderColor,
    hoverX: hovers[ds.label]?.x,
    hoverY: hovers[ds.label]?.y,
    highlight: hovers[ds.label]?.on || false,
  }));
  return groups.sort(
    (a, b) => (b.hoverY || -Infinity) - (a.hoverY || -Infinity)
  );
});

function onHover(ev: ChartEvent, elements: ActiveElement[], chart: Chart) {
  const points = {} as { [key: string]: Point };
  const mouseYFrom = chart.scales["y"].getValueForPixel((ev.y || 0) + 3) || 0;
  const mouseYTo = chart.scales["y"].getValueForPixel((ev.y || 0) - 3) || 0;
  for (const el of elements) {
    const ds = chartData.value.datasets[el.datasetIndex];
    const p = { x: ds.data[el.index].x, y: ds.data[el.index].y || 0 };
    const on = mouseYFrom <= p.y && p.y <= mouseYTo;
    points[ds.label] = { x: p.x, y: p.y, on: on };
  }
  hoverPoints.value = points;
}

function showTooltip() {
  tooltipVisible.value = true;
  emit("showTooltip");
}

function hideTooltip() {
  tooltipVisible.value = false;
  hoverPoints.value = {};
  emit("hideTooltip");
}

function resetZoom(e: MouseEvent) {
  // Bit hacky: simulate click on the hidden "Reset zoom" button
  const btns = element.value?.getElementsByClassName("reset-zoom");
  if (btns && btns.length > 0) {
    (btns[0] as HTMLButtonElement).click();
  }
  e.preventDefault();
}
</script>

<template>
  <div
    class="w-[320px] h-[240px] mx-1 mb-1 relative"
    ref="element"
    @dblclick="resetZoom"
    @mouseover="showTooltip"
    @mouseout="hideTooltip"
  >
    <!-- @vue-ignore -->
    <Line :data="chartData" :options="chartOptions" />
    <!-- Tooltip -->
    <div
      class="absolute left-0 top-100 w-[330px] translate-x-[-5px] z-10 shadow-md"
      v-show="tooltipVisible"
    >
      <div class="bg-white text-gray-600 border p-1 pb-0 flex flex-col">
        <div
          v-for="group in tooltipData"
          :class="{ flex: true, 'gap-1': true, 'font-bold': group.highlight }"
        >
          <div
            :style="{ backgroundColor: group.color }"
            class="size-3 mr-1"
          ></div>
          <div class="flex-grow">
            {{ group.label }}
            <span class="text-gray-400">
              {{ group.hoverX ? "[" + formatSteps(group.hoverX) + "]" : "" }}
            </span>
          </div>
          <div class="text-right">
            {{ group.hoverY?.toPrecision(4) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
