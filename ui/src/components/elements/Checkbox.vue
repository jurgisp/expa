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
const props = defineProps<{ value?: string; label: string }>();
const model = defineModel();
</script>

<template>
  <span>
    <label class="cursor-pointer">
      <input
        type="checkbox"
        :value="value"
        v-model="model"
        class="checkbox"
      />
      <span class="cursor-pointer">{{ label }}</span>
    </label>
  </span>
</template>
