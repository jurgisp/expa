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
const props = defineProps<{ id: string; options: [number, string][] }>();
const model = defineModel();
</script>
<template>
  <span>
    <span v-for="opt in options">
      <label class="cursor-pointer">
        <input
          type="radio"
          class="size-3 text-purple-500 hover:ring-1 hover:ring-offset-1 focus:ring-1 focus:ring-offset-1"
          :name="id"
          :value="opt[0]"
          v-model="model"
        />
        <span class="mx-1">
          {{ opt[1] }}
        </span>
      </label>
    </span>
  </span>
</template>
