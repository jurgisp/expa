/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import mitt from "mitt";

import { bindKey, isInputFocused } from "./utils";

export const cmd = mitt();

function invoke(command: string) {
  console.log(command); // DEBUG
  cmd.emit(command);
}

function defineCommand(command: string, key: string) {
  bindKey(key, () => invoke(command));
}

// Special case for Esc - it either deselects input or fires command
bindKey(
  "Escape",
  () => {
    if (isInputFocused()) {
      // @ts-ignore
      document.activeElement.blur();
    } else {
      invoke("deselect");
    }
  },
  false
);

defineCommand("refresh", "Cmd+Enter");

defineCommand("nextReport", "Cmd+ArrowDown");
defineCommand("prevReport", "Cmd+ArrowUp");
defineCommand("moveReportDown", "Cmd+Shift+ArrowDown");
defineCommand("moveReportUp", "Cmd+Shift+ArrowUp");
defineCommand("saveReport", "Cmd+s");
defineCommand("deleteReport", "Cmd+d");

defineCommand("focusNextCard", "ArrowRight");
defineCommand("focusPrevCard", "ArrowLeft");
defineCommand("addRemoveCard", " ");
defineCommand("moveCardDown", "Shift+ArrowRight");
defineCommand("moveCardUp", "Shift+ArrowLeft");

defineCommand("focusMetricSearch", "/");
defineCommand("focusRunFilter", "Cmd+/");

defineCommand("report.settings.toggleLegend", "l");
defineCommand("report.settings.bins1", "1");
defineCommand("report.settings.bins2", "2");
defineCommand("report.settings.bins3", "3");
defineCommand("report.settings.bins4", "4");
defineCommand("report.settings.bins5", "5");

defineCommand("experiments.toggleRunning", "r");
