import { NextRequest } from "next/server";
export const runtime = "nodejs";

import { buildICSFromSelection, prewarmWasm } from "@/lib/wasm";
import type { Selection } from "@/lib/types";

// Prewarm WASM instance on module load (best-effort)
void prewarmWasm();

// Selection filtering and ICS building is moved into Rust via WASM.

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q');
  if (!q) return new Response('Missing q', { status: 400 });
  let sel: Selection;
  try {
    const json = Buffer.from(q, 'base64url').toString('utf8');
    sel = JSON.parse(json);
  } catch {
    return new Response('Bad q', { status: 400 });
  }
  const ics = await buildICSFromSelection(sel);
  return new Response(ics, { headers: { 'Content-Type': 'text/calendar; charset=utf-8' } });
}

export async function POST(req: NextRequest) {
  let sel: Selection;
  try {
    sel = await req.json();
  } catch {
    return new Response('Bad JSON', { status: 400 });
  }
  const ics = await buildICSFromSelection(sel);
  return new Response(ics, { headers: { 'Content-Type': 'text/calendar; charset=utf-8' } });
}
