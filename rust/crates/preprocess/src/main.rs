use std::{collections::{BTreeMap, BTreeSet}, fs, path::{Path, PathBuf}, io::BufReader};

use anyhow::{Context, Result};
use chrono::{Datelike, NaiveDateTime, TimeZone, Utc, DateTime};
use chrono_tz::Europe::Paris;
use ical::parser::ical::component::IcalEvent;
use ical::IcalParser;
use regex::Regex;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

const PARCOURS: &[&str] = &["ANDROIDE","DAC","STL","IMA","BIM","SAR","SESI","SFPN"];
const MASTER_YEARS: &[&str] = &["M1","M2"];

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Event {
    uid: String,
    summary: String,
    location: Option<String>,
    start: String,
    end: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    rrule: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    exdates: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    recurrence_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CourseVariant {
    group: Option<String>,
    r#type: Option<String>,
    events: Vec<Event>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Course {
    name: String,
    code: String,
    special: bool,
    groups: BTreeSet<String>,
    variants: Vec<CourseVariant>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Bundle {
    master_year: String,
    parcours: String,
    courses: Vec<Course>,
    updated_at: String,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
struct IndexEntry {
    name: String,
    code: String,
    // groups for this course within this single source
    groups: BTreeSet<String>,
    // single source like M1_DAC
    source: String,
}

fn main() -> Result<()> {
    let download_dir = PathBuf::from("data/download");
    let out_dir = PathBuf::from("data/preprocessed");
    fs::create_dir_all(&out_dir)?;

    // index by year: { "M1": { code|source -> IndexEntry }, "M2": { ... } }
    let mut index_by_year: BTreeMap<String, BTreeMap<String, IndexEntry>> = BTreeMap::new();

    for &year in MASTER_YEARS {
        for &p in PARCOURS {
            let ics_path = download_dir.join(format!("{}_{}.ics", year, p));
            if !ics_path.exists() { continue; }
            let bundle = process_one(&ics_path, year, p)?;
            // write bundle
            let out_path = out_dir.join(format!("{}_{}.json", year, p));
            fs::write(&out_path, serde_json::to_vec_pretty(&bundle)?)
                .with_context(|| format!("write {}", out_path.display()))?;

            // update index_by_year: do not merge across sources; key by code|source; skip specials
            let map = index_by_year.entry(year.to_string()).or_default();
            for c in &bundle.courses {
                if c.special { continue; }
                let src = format!("{}_{}", year, p);
                let key = format!("{}|{}", c.code, src);
                let entry = map.entry(key.clone()).or_insert_with(|| IndexEntry {
                    name: c.name.clone(),
                    code: c.code.clone(),
                    groups: BTreeSet::new(),
                    source: src.clone(),
                });
                // keep the first non-generic name
                if entry.name.eq_ignore_ascii_case("Cours") && !c.name.eq_ignore_ascii_case("Cours") {
                    entry.name = c.name.clone();
                }
                entry.groups.extend(c.groups.clone());
            }
        }
    }

    // write index only to public for direct client fetch (single source of truth)
    let public_dir = PathBuf::from("public/preprocessed");
    fs::create_dir_all(&public_dir)?;
    let public_index = public_dir.join("index.json");
    fs::write(&public_index, serde_json::to_vec_pretty(&index_by_year)?)?;

    let count: usize = index_by_year.values().map(|m| m.len()).sum();
    println!("preprocess done; wrote {} entries", count);
    Ok(())
}

fn academic_year_start_utc() -> chrono::DateTime<Utc> {
    let now = Utc::now().with_timezone(&Paris);
    let year = if now.month() >= 9 { now.year() } else { now.year() - 1 };
    let dt = Paris.with_ymd_and_hms(year, 9, 1, 0, 0, 0).unwrap();
    dt.with_timezone(&Utc)
}

fn process_one(path: &Path, year: &str, parcours: &str) -> Result<Bundle> {
    let file = fs::File::open(path).with_context(|| format!("open {}", path.display()))?;
    let mut parser = IcalParser::new(BufReader::new(file));
    let mut events: Vec<IcalEvent> = Vec::new();
    if let Some(calendar) = parser.next() {
        let cal = calendar?;
        events.extend(cal.events);
    }

    let start_cut = academic_year_start_utc();
    let end_cut = academic_year_end_utc();
    // Group by code only; keep candidate names per event to pick a canonical name later
    let mut grouped: BTreeMap<String, Vec<(Option<String>, Option<String>, Event, String)>> = BTreeMap::new();

    for ev in &events {
        let summary = get_prop(ev, "SUMMARY").unwrap_or_else(|| "(sans titre)".into());
        let location = get_prop(ev, "LOCATION");
        let uid = get_prop(ev, "UID").unwrap_or_else(|| Uuid::new_v4().to_string());

        // datetime
        let (start_raw, end_raw) = match (get_prop(ev, "DTSTART"), get_prop(ev, "DTEND")) {
            (Some(s), Some(e)) => (s, e),
            _ => continue,
        };
        let start_iso = parse_ics_datetime_to_utc_iso(&start_raw);
        let end_iso = parse_ics_datetime_to_utc_iso(&end_raw);
        let start_dt = DateTime::parse_from_rfc3339(&start_iso).unwrap().with_timezone(&Utc);

        // Recurrence info
        let rrule = get_prop(ev, "RRULE");
        let mut exdates: BTreeSet<String> = BTreeSet::new();
        for ex in get_props(ev, "EXDATE") {
            for part in ex.split(',') {
                let iso = parse_ics_datetime_to_utc_iso(part.trim());
                exdates.insert(iso);
            }
        }
        let recurrence_id = get_prop(ev, "RECURRENCE-ID").map(|s| parse_ics_datetime_to_utc_iso(&s));

        // Filter window: singles and overrides by start; recurring base by intersection with UNTIL if available
        let include = if recurrence_id.is_some() {
            start_dt >= start_cut && start_dt <= end_cut
        } else if rrule.is_some() {
            if let Some(rule) = rrule.as_ref().map(|s| parse_rrule(s)) {
                if let Some(until_iso) = rule.until_iso.as_ref() {
                    if let Ok(until_dt) = DateTime::parse_from_rfc3339(until_iso) {
                        let until_dt = until_dt.with_timezone(&Utc);
                        // intersect [start, until] with [start_cut, end_cut]
                        !(until_dt < start_cut)
                    } else { true }
                } else { true }
            } else { true }
        } else {
            start_dt >= start_cut && start_dt <= end_cut
        };
        if !include { continue; }

        // extract name, code, type, group from summary with improved rules
        let Parsed { name, code, typ, group: grp } = parse_summary(&summary);

        let event = Event {
            uid,
            summary: summary.clone(),
            location,
            start: start_iso,
            end: end_iso,
            rrule,
            exdates: exdates.into_iter().collect(),
            recurrence_id,
        };
        grouped.entry(code.clone()).or_default().push((grp.clone(), typ.clone(), event, name.clone()));
    }

    let mut courses: Vec<Course> = Vec::new();
    for (code, rows) in grouped {
        // group by (group,type)
        let mut by_variant: BTreeMap<(Option<String>, Option<String>), Vec<Event>> = BTreeMap::new();
        // collect explicit groups to decide defaulting rule
        let mut explicit_groups: BTreeSet<String> = BTreeSet::new();
        for (grp, _typ, _ev, _name) in &rows {
            if let Some(g) = grp.clone() { explicit_groups.insert(g); }
        }
        for (grp, typ, ev, _name) in rows.clone() {
            by_variant.entry((grp, typ)).or_default().push(ev);
        }
        let groups: BTreeSet<String> = by_variant.keys().filter_map(|(g, _)| g.clone()).collect();
        let variants = by_variant.into_iter().map(|((grp, typ), events)| CourseVariant { group: grp, r#type: typ, events }).collect();
        // Specials: everything not normal code and not OIP/Anglais is encoded earlier as code="special"
        let special = code == "special";
        // pick canonical name: most frequent non-"Cours" if available otherwise first
        let mut name_counts: BTreeMap<String, usize> = BTreeMap::new();
        for (_grp, _typ, _ev, nm) in rows {
            *name_counts.entry(nm).or_insert(0) += 1;
        }
        let mut best_name: Option<(String, usize)> = None;
        for (nm, cnt) in name_counts {
            let is_generic = nm.eq_ignore_ascii_case("Cours");
            let score = if is_generic { cnt } else { cnt * 10 };
            if let Some((_bn, bs)) = &best_name {
                if score > *bs { best_name = Some((nm, score)); }
            } else {
                best_name = Some((nm, score));
            }
        }
        let name = best_name.map(|(n, _)| n).unwrap_or_else(|| code.clone());
        courses.push(Course { name, code, special, groups, variants });
    }

    courses.sort_by(|a,b| a.name.cmp(&b.name));
    let bundle = Bundle { master_year: year.into(), parcours: parcours.into(), courses, updated_at: Utc::now().to_rfc3339() };
    Ok(bundle)
}

fn get_prop(ev: &IcalEvent, name: &str) -> Option<String> {
    ev.properties.iter().find(|p| p.name.eq_ignore_ascii_case(name)).and_then(|p| p.value.clone())
}

fn get_props(ev: &IcalEvent, name: &str) -> Vec<String> {
    ev.properties
        .iter()
        .filter(|p| p.name.eq_ignore_ascii_case(name))
        .filter_map(|p| p.value.clone())
        .collect()
}

fn parse_ics_datetime_to_utc_iso(s: &str) -> String {
    // Handles forms: 20240901T130000Z or 20240901T130000 or 20240901
    if let Ok(dt) = chrono::DateTime::parse_from_rfc3339(s) {
        return dt.with_timezone(&Utc).to_rfc3339();
    }
    // Try basic form with Z
    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(s.trim_end_matches('Z'), "%Y%m%dT%H%M%S") {
        let dt = Paris.from_local_datetime(&dt).unwrap();
        return dt.with_timezone(&Utc).to_rfc3339();
    }
    if let Ok(d) = chrono::NaiveDate::parse_from_str(s, "%Y%m%d") {
        let ndt = NaiveDateTime::new(d, chrono::NaiveTime::from_hms_opt(0,0,0).unwrap());
        let dt = Paris.from_local_datetime(&ndt).unwrap();
        return dt.with_timezone(&Utc).to_rfc3339();
    }
    // fallback now
    Utc::now().to_rfc3339()
}

#[derive(Debug, Clone)]
struct Parsed {
    name: String,
    code: String,
    typ: Option<String>,
    group: Option<String>,
}

fn parse_summary(summary: &str) -> Parsed {
    // Tokenize on non-alphanumeric separators but keep original casing for name
    let tokens: Vec<String> = Regex::new(r"[^A-Za-z0-9]+").unwrap()
        .split(summary)
        .filter(|t| !t.is_empty())
        .map(|s| s.to_string())
        .collect();

    let upper = summary.to_uppercase();

    // 1) Detect normal course numeric code and reduce to last 3 digits
    //    - [4/5]INxxx → xxx
    //    - INxxx → xxx
    //    - UM5INxxx / MU5INxxx → xxx
    //    - UM5255 → 255 (fallback: take last 3 digits from first segment before '-')
    let code_digits_in = Regex::new(r"(?i)\b[45]?IN(\d{3})\b").unwrap()
        .captures(summary)
        .and_then(|c| c.get(1))
        .map(|m| m.as_str().to_string());

    let code_digits_um = Regex::new(r"(?i)\b(?:UM|MU)\s*([45]?\d{3,4})\b").unwrap()
        .captures(summary)
        .and_then(|c| c.get(1))
        .map(|m| {
            let s = m.as_str();
            if s.len() >= 3 { s[s.len()-3..].to_string() } else { s.to_string() }
        });

    let first_seg = summary.split('-').next().unwrap_or(summary);
    let code_digits_firstseg = Regex::new(r"(\d{3,4})").unwrap()
        .captures_iter(first_seg)
        .last()
        .map(|c| c.get(1).unwrap().as_str().to_string())
        .map(|s| if s.len()>=3 { s[s.len()-3..].to_string() } else { s });

    // 2) Detect OIP family
    let is_oip = upper.contains("OIP");
    // 3) Detect Anglais family (standalone course only; exclude "(en anglais)")
    let has_en_anglais = Regex::new(r"(?i)\(\s*en\s+anglais\s*\)").unwrap().is_match(summary);
    let is_ang = !has_en_anglais && upper.contains("ANGLAIS");

    // Type + group detection
    let mut ty: Option<String> = None;
    let mut grp: Option<String> = None;

    // a) combined like TME3, TD1, TP2, CM1, CS2
    let re_comb = Regex::new(r"(?i)\b(CM|TD|TP|TME|CS|EXAM|EXAMEN|DS|CT|CC)\s*:?\s*(TD|TP)?\s*([0-9]{1,2})?\b").unwrap();
    for cap in re_comb.captures_iter(&upper) {
        // prefer explicit TD/TP/CM/TME over CS
        let t1 = cap.get(1).map(|m| m.as_str().to_uppercase());
        let t2 = cap.get(2).map(|m| m.as_str().to_uppercase());
        let g = cap.get(3).map(|m| m.as_str().to_string());
        ty = match (t1.as_deref(), t2.as_deref()) {
            (_, Some("TD")) => Some("TD".into()),
            (_, Some("TP")) => Some("TP".into()),
            (Some("TME"), _) => Some("TME".into()),
            (Some("CM"), _) => Some("CM".into()),
            (Some("TD"), _) => Some("TD".into()),
            (Some("TP"), _) => Some("TP".into()),
            (Some("CS"), _) => Some("CS".into()),
            (Some("EXAM"), _) | (Some("EXAMEN"), _) => Some("EXAM".into()),
            (Some("DS"), _) => Some("DS".into()),
            (Some("CT"), _) => Some("CT".into()),
            (Some("CC"), _) => Some("CC".into()),
            _ => ty,
        };
        // Only treat trailing digits as group when teaching types (TD/TP/CM/TME/CS)
        if grp.is_none() {
            if matches!(ty.as_deref(), Some("TD"|"TP"|"CM"|"TME"|"CS")) {
                grp = g;
            }
        }
    }

    // b) group markers like Gr2, Groupe 2, G2
    let re_grp = Regex::new(r"(?i)\b(?:GR|GRP|GROUPE|GROUP|G)\s*[-_ ]?(\d{1,2})\b").unwrap();
    if grp.is_none() {
        grp = re_grp.captures(&upper).and_then(|c| c.get(1)).map(|m| m.as_str().to_string());
    }

    // c) Cours keyword => CS type
    if ty.is_none() && upper.contains("COURS") {
        ty = Some("CS".into());
    }

    // d) ER/ER1/ER2 → EXAM (not a group)
    if ty.is_none() {
        let re_er = Regex::new(r"(?i)\bER\s*\d*\b").unwrap();
        if re_er.is_match(&upper) { ty = Some("EXAM".into()); }
    }

    // e) Session 2, Session 1, etc. → EXAM
    if ty.is_none() {
        let re_sess = Regex::new(r"(?i)\bSESSION\s*\d+\b").unwrap();
        if re_sess.is_match(&upper) { ty = Some("EXAM".into()); }
    }

    // f) type suffix appended e.g. AnglaisCS
    if ty.is_none() {
        if let Some(tok) = tokens.iter().find(|t| Regex::new(r"(?i)(CM|TD|TP|TME|CS|EXAM|DS|CT|CC)$").unwrap().is_match(t)) {
            let m = Regex::new(r"(?i)(CM|TD|TP|TME|CS|EXAM|DS|CT|CC)$").unwrap().captures(tok).unwrap();
            ty = m.get(1).map(|m| m.as_str().to_uppercase());
        }
    }

    // g) Fallback: any occurrence of EXAMEN/EXAM anywhere → EXAM
    if ty.is_none() {
        if upper.contains("EXAMEN") || upper.contains("EXAM") {
            ty = Some("EXAM".into());
        }
    }

    // Code + Name resolution
    // Try to capture hyphen-based name: token after the first hyphen (e.g. "... - SDED - Cours" → SDED)
    let hyphen_name = Regex::new(r"(?i)^[^-]+-\s*([^-\s]+)")
        .unwrap()
        .captures(summary)
        .and_then(|c| c.get(1))
        .map(|m| m.as_str().to_string())
        .filter(|tok| {
            let u = tok.to_uppercase();
            let is_type = Regex::new(r"^(CM|TD|TP|TME|CS|EXAM|DS|CT|CC|COURS)$").unwrap().is_match(&u);
            !is_type
        });

    let (code, mut name) = if is_oip {
        ("OIP".into(), "OIP".into())
    } else if is_ang {
        let name_tok = tokens.iter().find(|t| t.to_uppercase().starts_with("ANGLAIS")).cloned().unwrap_or_else(|| "Anglais".into());
        ("Anglais".into(), name_tok)
    } else if let Some(d) = code_digits_in.or(code_digits_um).or(code_digits_firstseg) {
        // normal course: prefer hyphen-name, else the next good token (letters+digits, starts with letter, >=3) not being type/COURS
        let mut name_candidate: Option<String> = hyphen_name;
        if name_candidate.is_none() {
            let re_letter_digit_name = Regex::new(r"^[A-Z][A-Z0-9]{2,}$").unwrap();
            let re_code_um = Regex::new(r"^(UM|MU)[A-Z]*\d+$").unwrap();
            for (i, t) in tokens.iter().enumerate() {
                let tu = t.to_uppercase();
                let has_digit = Regex::new(r"\d").unwrap().is_match(&tu);
                // skip the very first token if it contains digits (often the code like UM4MA062)
                if i == 0 && has_digit { continue; }
                // skip tokens that include the detected numeric code digits (e.g., 062, 653)
                if has_digit && tu.contains(&d) { continue; }
                // skip obvious code-looking tokens like UM...062
                if re_code_um.is_match(&tu) { continue; }
                // skip tokens containing IN (e.g. UM5IN653)
                if tu.contains("IN") { continue; }
                if ["UM", "MU", "M", "U"].contains(&tu.as_str()) { continue; }
                if tu == "COURS" { continue; }
                if Regex::new(r"^(CM|TD|TP|TME|CS|EXAM|DS|CT|CC)$").unwrap().is_match(&tu) { continue; }
                if Regex::new(r"^(GR|GRP|GROUPE|GROUP|G)[0-9]*$").unwrap().is_match(&tu) { continue; }
                if re_letter_digit_name.is_match(&tu) { name_candidate = Some(t.clone()); break; }
            }
        }
        // As a last resort, take the segment after the first hyphen and strip trailing punctuation
        let final_name = name_candidate.unwrap_or_else(|| {
            summary.split('-').nth(1).map(|s| s.split_whitespace().next().unwrap_or(s).to_string()).unwrap_or_else(|| summary.to_string())
        });
        (d, final_name)
    } else {
        // Special activity (not OIP/Anglais; no standard numeric code) — use code "special"
        ("special".into(), summary.to_string())
    };

    // If this is a normal code course and marked "(en anglais)", set special group label
    let mut grp = grp;
    if has_en_anglais && code != "Anglais" && code != "special" {
        grp = Some("anglais".into());
        // ensure name doesn't include the trailing marker
        if name.to_uppercase().contains("ANGLAIS") {
            name = name.split_whitespace().next().unwrap_or(&name).to_string();
        }
    }

    Parsed { name, code, typ: ty, group: grp }
}

#[derive(Debug, Default, Clone)]
struct RRule {
    freq: Option<String>,
    interval: u32,
    until_iso: Option<String>,
    count: Option<u32>,
    byday: Vec<chrono::Weekday>,
}

fn parse_rrule(s: &str) -> RRule {
    let mut rule = RRule { freq: None, interval: 1, until_iso: None, count: None, byday: Vec::new() };
    for part in s.split(';') {
        let mut it = part.splitn(2, '=');
        let key = it.next().unwrap_or("").to_uppercase();
        let val = it.next().unwrap_or("");
        match key.as_str() {
            "FREQ" => rule.freq = Some(val.to_uppercase()),
            "INTERVAL" => {
                if let Ok(n) = val.parse::<u32>() { rule.interval = n.max(1); }
            }
            "UNTIL" => {
                rule.until_iso = Some(parse_ics_datetime_to_utc_iso(val));
            }
            "COUNT" => {
                if let Ok(n) = val.parse::<u32>() { rule.count = Some(n); }
            }
            "BYDAY" => {
                let mut days: Vec<chrono::Weekday> = Vec::new();
                for d in val.split(',') {
                    let wd = match d.trim().to_uppercase().as_str() {
                        "MO" => Some(chrono::Weekday::Mon),
                        "TU" => Some(chrono::Weekday::Tue),
                        "WE" => Some(chrono::Weekday::Wed),
                        "TH" => Some(chrono::Weekday::Thu),
                        "FR" => Some(chrono::Weekday::Fri),
                        "SA" => Some(chrono::Weekday::Sat),
                        "SU" => Some(chrono::Weekday::Sun),
                        _ => None,
                    };
                    if let Some(wd) = wd { days.push(wd); }
                }
                // stable ordering Monday..Sunday
                days.sort_by_key(|d| d.num_days_from_monday());
                rule.byday = days;
            }
            _ => {}
        }
    }
    rule
}

fn academic_year_end_utc() -> chrono::DateTime<Utc> {
    let now = Utc::now().with_timezone(&Paris);
    let year = if now.month() >= 9 { now.year() + 1 } else { now.year() };
    let dt = Paris.with_ymd_and_hms(year, 8, 31, 23, 59, 59).unwrap();
    dt.with_timezone(&Utc)
}

// note: RRULE expansion removed from preprocess; ICS builder will emit RRULE
