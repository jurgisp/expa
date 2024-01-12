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
import { computed, ref, watch } from "vue";
import { Line } from "vue-chartjs";
import { type ChartOptions } from "chart.js";

import { state } from "@/state";
import { formatSteps, COLORS } from "@/utils";

const props = defineProps<{ data: any }>();
const element = ref(null as HTMLElement | null);

const chartData = computed(() => {
  const data = props.data;
  const datasets = data.map((group) => ({
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

// TODO: plot improvements
// - Custom expandable legend
// - Tooltip/Mouseover?
// - Bubbles when zoomed in?

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
        min: state.value.report.xmin ?? undefined,
        max: state.value.report.xmax ?? undefined,
        // title: {
        //   display: state.value.report.xaxis != "step",
        //   text: {"step": "steps", "runtime": "seconds"}[state.value.report.xaxis]
        // },
      },
      y: {
        type: "linear",
        grace: "0%",
        min: state.value.report.ymin ?? undefined,
        max: state.value.report.ymax ?? undefined,
      },
    },
    interaction: {
      // aplies to both hover and tooltip
      mode: "nearest",
      axis: "x",
      intersect: false,
    },
    plugins: {
      title: {
        display: false,
      },
      legend: {
        display: false,
      },
      tooltip: {
        // enabled: false,
        animation: { duration: 0 },
        itemSort: (a, b) => b.parsed.y - a.parsed.y,
      },
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
    class="w-[320px] h-[240px] mx-1 mb-1"
    @dblclick="resetZoom"
    ref="element"
  >
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
