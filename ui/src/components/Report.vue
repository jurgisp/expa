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

import { state } from "@/state";
import { cmd } from "@/commands";

import MetricsFilter from "./MetricsFilter.vue";
import ReportSettings from "./ReportSettings.vue";
import Card from "./Card.vue";

const pinnedCards = computed(() => state.value.report.cards);
const unpinnedCards = computed(() => {
  const pinned = new Set(pinnedCards.value.map((card) => card.metric));
  return state.value.metrics.filter((metric) => !pinned.has(metric.metric));
});
const focusedMetric = ref(null as string | null);

function getPinnedIndex(metric: string | null): number | null {
  const ix = pinnedCards.value.findIndex((c) => c.metric === metric);
  return ix == -1 ? null : ix;
}

function getUnpinnedIndex(metric: string | null): number | null {
  const ix = unpinnedCards.value.findIndex((c) => c.metric === metric);
  return ix == -1 ? null : ix;
}

function addRemoveCard(metric: string | null) {
  let ix = getUnpinnedIndex(metric);
  if (ix !== null) {
    // Unpinned - add
    state.value.report.cards.push(unpinnedCards.value[ix]);
    return;
  }
  ix = getPinnedIndex(metric);
  if (ix !== null) {
    // Pinned - remove
    state.value.report.cards.splice(ix, 1);
    return;
  }
}

function moveCardUp(metric: string | null) {
  const ix = getPinnedIndex(metric);
  if (ix === null || ix === 0) return;
  const [card] = state.value.report.cards.splice(ix, 1);
  state.value.report.cards.splice(ix - 1, 0, card);
}

function moveCardDown(metric: string | null) {
  const ix = getPinnedIndex(metric);
  if (ix === null || ix === pinnedCards.value.length - 1) return;
  const [card] = state.value.report.cards.splice(ix, 1);
  state.value.report.cards.splice(ix + 1, 0, card);
}

function focusNextCard() {
  const ix1 = getPinnedIndex(focusedMetric.value);
  const ix2 = getUnpinnedIndex(focusedMetric.value);
  if (ix1 === null && ix2 === null) {
    // If none focused, focus first pinned or unpinned
    if (pinnedCards.value.length > 0) {
      focusedMetric.value = pinnedCards.value[0].metric;
    } else if (unpinnedCards.value.length > 0) {
      focusedMetric.value = unpinnedCards.value[0].metric;
    }
  } else if (ix1 !== null) {
    // If pinned focused, focus next pinned or first unpinned
    if (ix1 < pinnedCards.value.length - 1) {
      focusedMetric.value = pinnedCards.value[ix1 + 1].metric;
    } else if (unpinnedCards.value.length > 0) {
      focusedMetric.value = unpinnedCards.value[0].metric;
    }
  } else if (ix2 !== null) {
    // If unpinned focused, focus next unpinned
    if (ix2 < unpinnedCards.value.length - 1) {
      focusedMetric.value = unpinnedCards.value[ix2 + 1].metric;
    }
  }
}

function focusPrevCard() {
  const ix1 = getPinnedIndex(focusedMetric.value);
  const ix2 = getUnpinnedIndex(focusedMetric.value);
  if (ix1 === null && ix2 === null) {
    // If none focused, focus last pinned or unpinned
    if (pinnedCards.value.length > 0) {
      focusedMetric.value =
        pinnedCards.value[pinnedCards.value.length - 1].metric;
    } else if (unpinnedCards.value.length > 0) {
      focusedMetric.value =
        unpinnedCards.value[unpinnedCards.value.length - 1].metric;
    }
  } else if (ix2 !== null) {
    // If unpinned focused, focus prev unpinned or last pinned
    if (ix2 > 0) {
      focusedMetric.value = unpinnedCards.value[ix2 - 1].metric;
    } else if (pinnedCards.value.length > 0) {
      focusedMetric.value =
        pinnedCards.value[pinnedCards.value.length - 1].metric;
    }
  } else if (ix1 !== null) {
    // If pinned focused, focus prev pinned
    if (ix1 > 0) {
      focusedMetric.value = pinnedCards.value[ix1 - 1].metric;
    }
  }
}

function unfocusCard() {
  focusedMetric.value = null;
}

watch(
  // On report change
  computed(() => state.value.reportIndex),
  () => unfocusCard()
);

cmd.on("moveCardDown", () => moveCardDown(focusedMetric.value));
cmd.on("moveCardUp", () => moveCardUp(focusedMetric.value));
cmd.on("addRemoveCard", () => addRemoveCard(focusedMetric.value));
cmd.on("focusNextCard", focusNextCard);
cmd.on("focusPrevCard", focusPrevCard);
cmd.on("deselect", unfocusCard);
</script>

<template>
  <div class="h-full w-full flex flex-col">
    <div class="p-1 bg-slate-200 border-b border-slate-400">
      <MetricsFilter />
    </div>
    <div class="bg-slate-200 border-b border-slate-400">
      <ReportSettings />
    </div>
    <div class="flex-grow overflow-scroll bg-gray-100">
      <!-- Pinned cards -->
      <div
        class="flex flex-wrap gap-1 p-1"
        v-if="pinnedCards.length > 0"
      >
        <!-- <div v-if="pinnedCards.length == 0" class="text-gray-400">
          No pinned metrics
        </div> -->
        <div
          v-for="(card, ix) in pinnedCards"
          :key="card.metric"
          :class="{ 'ring-2': card.metric === focusedMetric }"
        >
          <Card
            :key="card.metric"
            :metric="card.metric"
            :pinned="true"
            :pinnedFirst="ix == 0"
            :pinnedLast="ix == pinnedCards.length - 1"
            @move-up="moveCardUp(card.metric)"
            @move-down="moveCardDown(card.metric)"
            @remove="addRemoveCard(card.metric)"
            @click.stop="focusedMetric = card.metric"
          />
        </div>
      </div>
      <!-- Divider -->
      <div
        v-if="pinnedCards.length > 0 && unpinnedCards.length > 0"
        class="p-1 bg-slate-200 border-y border-slate-400"
      >
        <span class="text-gray-400">
          Search results
        </span>
      </div>
      <!-- Unpinned metrics -->
      <div class="flex flex-wrap gap-1 p-1">
        <div
          v-for="(card, ix) in unpinnedCards"
          :key="card.metric"
          :class="{ 'ring-2': card.metric === focusedMetric }"
        >
          <Card
            :key="card.metric"
            :metric="card.metric"
            :pinned="false"
            @add="addRemoveCard(card.metric)"
            @click.stop="focusedMetric = card.metric"
          />
        </div>
      </div>
    </div>
  </div>
</template>
