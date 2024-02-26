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

import { onKeyStroke } from "@vueuse/core";
import { watchDebounced as watchDebouncedOrig } from "@vueuse/core";

// https://github.com/chartjs/Chart.js/blob/master/src/plugins/plugin.colors.ts
export const COLORS = [
  "rgb(54, 162, 235)", // blue
  "rgb(255, 99, 132)", // red
  "rgb(75, 192, 192)", // green
  "rgb(255, 159, 64)", // orange
  "rgb(153, 102, 255)", // purple
  "rgb(255, 205, 86)", // yellow
  "rgb(201, 203, 207)", // grey
];

export function watchDebounced(source, callback, options = { debounce: 300 }) {
  watchDebouncedOrig(source, callback, options);
}

export function regexFilter(
  items: any[],
  pattern: string,
  prop: (any) => string
) {
  try {
    const regex = new RegExp(pattern);
    return items.filter((o) => regex.test(prop(o)));
  } catch (e) {
    // If not a valid regex, treat as substring search
    return items.filter((o) => prop(o).includes(pattern));
  }
}

export function formatAge(seconds: number) {
  if (seconds < 60) {
    return seconds + "s";
  } else if (seconds < 3600) {
    return Math.floor(seconds / 60) + "m";
  } else if (seconds < 86400) {
    return Math.floor(seconds / 3600) + "h";
  } else {
    return Math.floor(seconds / 86400) + "d";
  }
}

export function formatSteps(steps, precision: number = 3) {
  let suffix = "";
  if (steps >= 1000000000) {
    steps /= 1000000000;
    suffix = "B";
  } else if (steps >= 1000000) {
    steps /= 1000000;
    suffix = "M";
  } else if (steps >= 1000) {
    steps /= 1000;
    suffix = "K";
  }
  return roundToPrecision(steps, precision).toString() + suffix;
}

function roundToPrecision(value: number, precision: number) {
  return Number(value.toPrecision(precision));
}

export function parseIntInput(s: string): number | null {
  // Parse while handling shorthand "100k", "10M"
  s = s.trim();
  if (s === "") return null;
  let val = parseInt(s, 10);
  if (s.toLowerCase().endsWith("k")) {
    val = parseInt(s.slice(0, -1), 10) * 1000;
  } else if (s.toLowerCase().endsWith("m")) {
    val = parseInt(s.slice(0, -1), 10) * 1000000;
  } else if (s.toLowerCase().endsWith("b")) {
    val = parseInt(s.slice(0, -1), 10) * 1000000000;
  }
  return isNaN(val) ? null : val;
}

export function parseFloatInput(s: string): number | null {
  s = s.trim();
  if (s === "") return null;
  let val = parseFloat(s);
  return isNaN(val) ? null : val;
}

export function isDeepEqual(obj1, obj2) {
  return JSON.stringify(obj1) === JSON.stringify(obj2);
}

export function deepCopy(obj) {
  return JSON.parse(JSON.stringify(obj));
}

export function bindKey(key: string, fn: () => void, ignoreOnInput = true) {
  // Supports (modifier)+(key), unlike onKeyStroke
  key = key.replace("Ctrl+", "Cmd+"); // Treat Ctrl=Cmd
  const [rawKey] = key.split("+").slice(-1); // Without modifiers
  onKeyStroke([rawKey], (e) => {
    if (ignoreOnInput && isInputFocused()) {
      // Disable text-editing keyboard shortcuts on input focus
      if (
        !(e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) ||
        ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(rawKey)
      ) {
        return;
      }
    }
    const mods = [] as string[];
    if (e.metaKey || e.ctrlKey) {
      mods.push("Cmd");
    }
    if (e.altKey) {
      mods.push("Alt");
    }
    if (e.shiftKey) {
      mods.push("Shift");
    }
    mods.push(rawKey);
    const keyPressed = mods.join("+");
    if (keyPressed === key) {
      fn();
      e.preventDefault();
    }
  });
}

export function isInputFocused() {
  var activeElement = document.activeElement;
  return (
    activeElement &&
    (activeElement.tagName === "INPUT" ||
      activeElement.tagName === "TEXTAREA" ||
      activeElement.tagName === "SELECT")
  );
}
