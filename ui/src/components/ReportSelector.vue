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
import { computed, nextTick, ref } from "vue";

import { state, reports } from "@/state";
import { cmd } from "@/commands";
import { isDeepEqual, deepCopy } from "@/utils";

const renaming = ref(false);
const deleting = ref(false);

const reportModified = computed(
  () => !isDeepEqual(state.report, reports.value[state.reportIndex])
);

function selectReport(ix: number) {
  if (ix < 0 || ix >= reports.value.length) {
    return;
  }
  cancelDelete();
  // Discarding unsaved changes
  state.reportIndex = ix;
  state.report = deepCopy(reports.value[ix]);
}

async function saveReport() {
  if (state.reportIndex == 0) {
    // If saving "new" -> add
    await saveNewReport(generateNewName());
  } else {
    // If saving previously saved -> overwrite
    reports.value[state.reportIndex] = deepCopy(state.report);
  }
}

async function saveNewReport(name?: string) {
  if (name) {
    state.report.name = name;
  }
  reports.value.splice(state.reportIndex + 1, 0, deepCopy(state.report));
  state.reportIndex = state.reportIndex + 1;
  await nextTick();
  startRename();
}

function deleteReport() {
  if (state.reportIndex == 0) {
    console.error("Can not delete first report");
    return;
  }
  reports.value.splice(state.reportIndex, 1);
  selectReport(state.reportIndex - 1);
}

function generateNewName() {
  const prefix = "Saved ";
  const names = new Set(reports.value.map((r) => r.name));
  let suffix = 1;
  while (names.has(prefix + suffix)) {
    suffix += 1;
  }
  return prefix + suffix;
}

function startRename() {
  if (state.reportIndex == 0) return;
  renaming.value = true;
}
function finishRename() {
  if (state.reportIndex == 0) return;
  renaming.value = false;
  // Name is auto-saved
  reports.value[state.reportIndex].name = state.report.name;
}

function startDelete() {
  if (state.reportIndex == 0) return;
  deleting.value = true;
}
function cancelDelete() {
  deleting.value = false;
}
function confirmDelete() {
  if (state.reportIndex == 0) return;
  deleting.value = false;
  deleteReport();
}

function moveReportDown() {
  const ix = state.reportIndex;
  if (ix == 0 || ix == reports.value.length - 1) return;
  const [report] = reports.value.splice(ix, 1);
  reports.value.splice(ix + 1, 0, report);
  state.reportIndex += 1;
}
function moveReportUp() {
  const ix = state.reportIndex;
  if (ix == 0 || ix == 1) return;
  const [report] = reports.value.splice(ix, 1);
  reports.value.splice(ix - 1, 0, report);
  state.reportIndex -= 1;
}

cmd.on("nextReport", () => selectReport(state.reportIndex + 1));
cmd.on("prevReport", () => selectReport(state.reportIndex - 1));
cmd.on("saveReport", saveReport);
cmd.on("saveNewReport", saveNewReport);
cmd.on("deleteReport", () =>
  deleting.value ? confirmDelete() : startDelete()
);
cmd.on("moveReportDown", moveReportDown);
cmd.on("moveReportUp", moveReportUp);
</script>

<template>
  <div class="overflow-auto bg-slate-200 text-sm text-gray-600">
    <div>
      <div v-for="(rep, ix) in reports">
        <!-- Selected report -->
        <div
          v-if="ix == state.reportIndex"
          class="p-1 w-full border-b border-slate-400 bg-white flex"
        >
          <div class="grow whitespace-nowrap overflow-auto">
            <span v-if="!renaming" @click.stop="startRename()">
              {{ state.report.name }}
            </span>
            <input
              v-else
              type="text"
              :ref="(el) => { if (el) { (el as HTMLInputElement).focus(); } }"
              v-model="state.report.name"
              @blur="finishRename"
              @keydown.enter="finishRename"
              class="text-xs text-black px-1 py-0 w-full"
            />
          </div>
          <!-- Controls -->
          <div v-if="!renaming" class="grow-0 whitespace-nowrap">
            <span
              v-if="reportModified && !deleting"
              title="Save"
              @click.stop="saveReport()"
              class="btn-icon-sm material-symbols-outlined"
            >
              save
            </span>
            <span
              v-if="ix != 0 && !deleting"
              title="Duplicate"
              @click.stop="saveNewReport()"
              class="btn-icon-sm material-symbols-outlined"
            >
              content_copy
            </span>
            <!-- <span
              v-if="ix != 0 && !deleting"
              title="Rename"
              @click.stop="startRename"
              class="btn-icon-sm material-symbols-outlined"
            >
              edit
            </span> -->
            <span
              v-if="ix != 0 && !deleting"
              title="Delete"
              @click.stop="startDelete"
              class="btn-icon-sm material-symbols-outlined"
            >
              delete
            </span>
            <span
              v-if="ix != 0 && deleting"
              title="Cancel delete"
              @click.stop="cancelDelete"
              class="btn-icon-sm material-symbols-outlined"
            >
              cancel
            </span>
            <span
              v-if="ix != 0 && deleting"
              title="Confirm delete"
              @click.stop="confirmDelete"
              class="btn-icon-sm material-symbols-outlined"
            >
              delete
            </span>
          </div>
        </div>
        <!-- Not selected report -->
        <div
          v-else
          @click.stop="selectReport(ix)"
          class="whitespace-nowrap p-1 border-b border-slate-400 cursor-pointer hover:bg-white"
        >
          {{ rep.name }}
        </div>
      </div>
    </div>
  </div>
</template>
