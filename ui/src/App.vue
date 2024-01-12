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
import { cmd } from "@/commands";
import Report from "./components/Report.vue";
import ReportSelector from "./components/ReportSelector.vue";
import ExperimentSelector from "./components/ExperimentSelector.vue";
import RunSelector from "./components/RunSelector.vue";
</script>

<template>
  <div class="h-screen w-screen flex flex-col">
    <div
      id="header"
      class="flex-none bg-purple-500 text-white drop-shadow p-2 flex"
    >
      <div class="grow">
        <span class="text-lg">e𝐗pa</span>
      </div>
      <div class="grow-0">
        <span
          title="Refresh (⌘+Enter)"
          @click.stop="cmd.emit('refresh')"
          class="cursor-pointer material-symbols-outlined align-[-8px]"
        >
          refresh
        </span>
      </div>
    </div>
    <!-- TODO: dynamically resize sidebars, some leads:
    https://codereview.stackexchange.com/questions/232651/resizable-containers-with-vuejs
    https://github.com/justcaliturner/vue-resizer -->
    <div id="body" class="grow flex text-xs overflow-clip">
      <div class="flex-none w-40 overflow-clip">
        <ReportSelector />
      </div>
      <div class="grow border-x border-slate-400 overflow-clip">
        <Report />
      </div>
      <div class="flex-none w-[350px] overflow-clip">
        <div class="h-1/2 border-b border-slate-400">
          <ExperimentSelector />
        </div>
        <div class="h-1/2">
          <RunSelector />
        </div>
      </div>
    </div>
  </div>
</template>
