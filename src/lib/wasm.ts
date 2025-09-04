import { TZID_DEFAULT } from "./constants";
import fs from "node:fs/promises";
import path from "node:path";
import type { Selection, Bundle } from "./types";

let wasmInstance: WebAssembly.Instance | null = null;
let loadPromise: Promise<WebAssembly.Instance> | null = null;

async function loadWasm(): Promise<WebAssembly.Instance> {
  if (wasmInstance) return wasmInstance;
  if (loadPromise) return loadPromise;
  loadPromise = (async () => {
    const wasmPath = path.join(process.cwd(), "public", "wasm", "ics_wasm.wasm");
    const buf = await fs.readFile(wasmPath);
    const ab = (buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as unknown) as ArrayBuffer;
    const module = await WebAssembly.compile(ab);
    const instance = await WebAssembly.instantiate(module, {});
    wasmInstance = instance as WebAssembly.Instance;
    return wasmInstance;
  })();
  try {
    return await loadPromise;
  } finally {
    loadPromise = null;
  }
}

export async function prewarmWasm() {
  try {
    await loadWasm();
  } catch {
    // best-effort: ignore prewarm errors; route will retry on demand
  }
}

export async function buildICS(events: Array<{start: string; end: string; summary: string; location?: string; uid?: string}>, name = "My Courses") {
  const inst = await loadWasm();
  const exports = (inst.exports as unknown) as {
    memory: WebAssembly.Memory;
    alloc: (len: number) => number;
    dealloc: (ptr: number, len: number) => void;
    build_ics: (ptr: number, len: number) => number;
    last_len: () => number;
  };
  const payload = JSON.stringify({ calendar_name: name, timezone: TZID_DEFAULT, events });
  const enc = new TextEncoder();
  const bytes = enc.encode(payload);
  const ptr = exports.alloc(bytes.length);
  const mem = new Uint8Array(exports.memory.buffer);
  mem.set(bytes, ptr);
  const outPtr = exports.build_ics(ptr, bytes.length);
  const len = exports.last_len();
  const view = new Uint8Array(exports.memory.buffer, outPtr, len);
  const dec = new TextDecoder();
  const ics = dec.decode(view);
  // free input and output
  exports.dealloc(ptr, bytes.length);
  exports.dealloc(outPtr, len);
  return ics;
}

export async function buildICSFromSelection(sel: Selection) {
  const inst = await loadWasm();
  const exports = (inst.exports as unknown) as {
    memory: WebAssembly.Memory;
    alloc: (len: number) => number;
    dealloc: (ptr: number, len: number) => void;
    build_ics_from_selection: (ptr: number, len: number) => number;
    last_len: () => number;
  };
  const normalizedItems = sel.items.map((i) => ({
    code: String(i.code).toUpperCase(),
    group: i.group !== undefined ? String(i.group) : undefined,
    source: i.source,
  }));
  const sources = Array.from(new Set(normalizedItems.map((i) => i.source)));
  const bundles: Record<string, Bundle> = {};
  await Promise.all(
    sources.map(async (s) => {
      const file = path.join(process.cwd(), "data", "preprocessed", `${s}.json`);
      try {
        const json = await fs.readFile(file, "utf8");
        bundles[s] = JSON.parse(json) as Bundle;
      } catch {
        // skip missing or bad bundle
      }
    })
  );
  const payload = JSON.stringify({
    calendar_name: sel.calendar_name ?? "My Courses",
    timezone: TZID_DEFAULT,
    master_year: sel.master_year,
    parcours: sel.parcours,
    items: normalizedItems,
    bundles,
  });
  const enc = new TextEncoder();
  const bytes = enc.encode(payload);
  const ptr = exports.alloc(bytes.length);
  const mem = new Uint8Array(exports.memory.buffer);
  mem.set(bytes, ptr);
  const outPtr = exports.build_ics_from_selection(ptr, bytes.length);
  const len = exports.last_len();
  const view = new Uint8Array(exports.memory.buffer, outPtr, len);
  const dec = new TextDecoder();
  const ics = dec.decode(view);
  exports.dealloc(ptr, bytes.length);
  exports.dealloc(outPtr, len);
  return ics;
}
