"use client";
import { useEffect, useMemo, useState } from "react";
import { MASTER_YEARS, PARCOURS } from "@/lib/constants";

type Dict = Record<string, string>;
type Props = { dict: Dict; locale: "zh" | "fr" };

type IndexEntry = {
  name: string;
  code: string;
  groups: string[];
  source: string; // e.g. M1_DAC
};
type IndexByYear = Record<string, Record<string, IndexEntry>>;

export default function HomeClient({ dict, locale }: Props) {
  const t = (key: string, vars?: Record<string, string | number>) => {
    let val = dict[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) val = val.replaceAll(`{${k}}`, String(v));
    return val;
  };

  const [index, setIndex] = useState<IndexByYear | null>(null);
  const [year, setYear] = useState<string>("M1");
  const [parcours, setParcours] = useState<string>("DAC");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Record<string, Set<string>>>(() => ({}));
  const [genUrl, setGenUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/preprocessed/index.json`)
      .then(r => r.json())
      .then((data: IndexByYear) => setIndex(data))
      .catch(() => setIndex(null));
  }, []);

  useEffect(() => { setSelected({}); }, [year, parcours]);

  const courses = useMemo(() => {
    const yearIndex = index?.[year] ?? {};
    const entries: IndexEntry[] = Object.values(yearIndex) as any;
    const query = q.trim().toLowerCase();
    const searched = entries.filter(i => !query || i.name.toLowerCase().includes(query) || i.code.toLowerCase().includes(query));
    const enriched = searched.map(i => {
      const inParcours = i.source === `${year}_${parcours}`;
      return { key: `${i.code}|${i.source}`, name: i.name, code: i.code, groups: i.groups ?? [], source: i.source, inParcours };
    });
    enriched.sort((a, b) => {
      if (a.inParcours !== b.inParcours) return a.inParcours ? -1 : 1;
      const nameCmp = a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
      if (nameCmp !== 0) return nameCmp;
      return a.code.localeCompare(b.code, undefined, { numeric: true });
    });
    return enriched;
  }, [index, year, parcours, q]);

  const toggle = (key: string, group: string) => {
    setSelected(prev => {
      const cp = { ...prev };
      const current = cp[key];
      if (current && current.has(group)) delete cp[key];
      else cp[key] = new Set([group]);
      return cp;
    });
  };

  const selectedSummary = useMemo(() => {
    const entries = Object.entries(selected);
    if (entries.length === 0) return t("selectedNone");
    const parts: string[] = [];
    for (const [key, groups] of entries) {
      const [code, source] = key.split('|');
      const arr = Array.from(groups ?? []);
      if (arr.length === 0) parts.push(`${code}(${t("groupAll")})`);
      else parts.push(`${code}(${arr.join(',')})`);
      if (source) parts[parts.length-1] += ` [${source}]`;
    }
    const joiner = t("joiner");
    return t("selectedPrefix", { n: entries.length }) + parts.join(joiner);
  }, [selected, dict]);

  const buildLink = () => {
    const base64urlEncode = (input: string) => {
      if (typeof window !== 'undefined') {
        const bytes = new TextEncoder().encode(input);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      }
      // @ts-ignore
      return Buffer.from(input).toString('base64url');
    };
    const items: Array<{code: string; group?: string; source: string}> = [];
    const allMarkers = new Set([t('groupAll').toLowerCase(), 'all', 'tout']);
    for (const [key, groups] of Object.entries(selected)) {
      const [code, source] = key.split('|');
      if (!groups || groups.size === 0) continue;
      const g = Array.from(groups)[0];
      if (!g || allMarkers.has(String(g).toLowerCase())) items.push({ code, source });
      else items.push({ code, group: String(g), source });
    }
    const payload = { master_year: year, parcours, items, calendar_name: `${year} ${parcours}` };
    const raw = JSON.stringify(payload);
    const q = base64urlEncode(raw);
    return `/api/build-ics?q=${q}`;
  };

  const onGenerate = () => {
    const rel = buildLink();
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    const abs = origin ? origin + rel : rel;
    setGenUrl(abs);
    setCopied(false);
  };
  const webcalUrl = useMemo(() => (genUrl ? genUrl.replace(/^https?:\/\//, 'webcal://') : null), [genUrl]);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-semibold">{t("title")}</h1>
      <div className="flex gap-4 items-center flex-wrap">
        <label className="flex items-center gap-2">{t("grade")}
          <select className="border rounded px-2 py-1" value={year} onChange={(e)=>setYear(e.target.value)}>
            {MASTER_YEARS.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2">{t("parcours")}
          <select className="border rounded px-2 py-1" value={parcours} onChange={(e)=>setParcours(e.target.value)}>
            {PARCOURS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <input className="flex-1 border rounded px-3 py-2" placeholder={t("search")} value={q} onChange={(e)=>setQ(e.target.value)} />

        <div className="ml-auto flex gap-2">
          <a className={`px-2 py-1 text-sm rounded border ${locale==='zh' ? 'bg-gray-200 dark:bg-white/10' : ''}`} href={`/zh`}>{t("lang_zh")}</a>
          <a className={`px-2 py-1 text-sm rounded border ${locale==='fr' ? 'bg-gray-200 dark:bg-white/10' : ''}`} href={`/fr`}>{t("lang_fr")}</a>
        </div>
      </div>

      <div className="border rounded divide-y max-h-[420px] overflow-auto">
        {courses.map(c => (
          <div key={c.key} className="p-3 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{c.name}</div>
                <div className="text-xs text-gray-500">{c.code} · {c.source}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {(c.groups && c.groups.length > 0 ? c.groups : [t("groupAll")]).map((g) => {
                const group = String(g);
                const sel = selected[c.key]?.has(group) ?? false;
                return (
                  <button
                    key={group}
                    className={`px-2 py-1 text-sm rounded border transition-colors ${sel
                      ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-500 dark:border-blue-500'
                      : 'border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-white/10'}`}
                    onClick={()=>toggle(c.key, group)}
                  >
                    {group}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-300">
          {selectedSummary}
        </div>
        <button className="px-4 py-2 rounded bg-blue-600 text-white" onClick={onGenerate}>{t("genButton")}</button>
      </div>

      {genUrl && (
        <div className="space-y-3 border rounded p-3">
          <div className="flex items-center gap-2">
            <input className="flex-1 border rounded px-3 py-2 bg-transparent" value={genUrl} readOnly />
            <button
              className="px-3 py-2 text-sm rounded border hover:bg-gray-100 dark:hover:bg-white/10"
              onClick={async ()=>{ try { await navigator.clipboard.writeText(genUrl); setCopied(true); setTimeout(()=>setCopied(false), 1500);} catch {} }}
              title={copied ? t('copied') : t('copyLink')}
            >{copied ? t('copied') : t('copy')}</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {webcalUrl && (
              <a className="px-3 py-2 rounded border hover:bg-gray-100 dark:hover:bg-white/10" href={webcalUrl}>
                {t('importWebcal')}
              </a>
            )}
            <a className="px-3 py-2 rounded border hover:bg-gray-100 dark:hover:bg-white/10" href={genUrl} download={`su-${year}-${parcours}.ics`}>
              {t('downloadIcs')}
            </a>
          </div>
        </div>
      )}

      <details className="border rounded p-3">
        <summary className="cursor-pointer font-medium">{t('guide')}</summary>
        <ul className="list-disc ml-5 mt-2 text-sm space-y-1">
          <li>{t('guide_ios')}</li>
          <li>{t('guide_google')}</li>
          <li>{t('guide_outlook')}</li>
        </ul>
      </details>
    </div>
  );
}
