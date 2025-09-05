use serde::Deserialize;
use std::collections::HashMap;

// Minimal ABI for WebAssembly without wasm-bindgen.
// Expose alloc/dealloc and a build function that takes JSON and returns a pointer to a UTF-8 string in memory.

#[no_mangle]
pub extern "C" fn alloc(len: usize) -> *mut u8 {
    let mut buf = Vec::<u8>::with_capacity(len);
    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);
    ptr
}

#[no_mangle]
pub extern "C" fn dealloc(ptr: *mut u8, len: usize) {
    unsafe { let _ = Vec::from_raw_parts(ptr, 0, len); }
}

static mut LAST_LEN: usize = 0;

#[no_mangle]
pub extern "C" fn last_len() -> usize {
    unsafe { LAST_LEN }
}

#[derive(Debug, Deserialize)]
struct EventIn {
    start: String,
    end: String,
    summary: String,
    location: Option<String>,
    uid: Option<String>,
    #[serde(default)]
    rrule: Option<String>,
    #[serde(default)]
    exdates: Option<Vec<String>>, // ISO strings
    #[serde(default)]
    recurrence_id: Option<String>, // ISO string
}

#[derive(Debug, Deserialize)]
struct BuildInput {
    calendar_name: Option<String>,
    timezone: Option<String>,
    events: Vec<EventIn>,
}

#[no_mangle]
pub extern "C" fn build_ics(ptr: *mut u8, len: usize) -> *mut u8 {
    // Safety: JS ensures ptr points to `len` bytes of input JSON
    let input = unsafe { std::slice::from_raw_parts(ptr, len) };
    let json = match std::str::from_utf8(input) { Ok(s) => s, Err(_) => "{}" };
    let data: BuildInput = serde_json::from_str(json).unwrap_or(BuildInput{ calendar_name: Some("My Calendar".into()), timezone: Some("Europe/Paris".into()), events: vec![] });
    let ics = build_calendar(&data);
    let bytes = ics.into_bytes();
    let out_ptr = alloc(bytes.len());
    unsafe { std::ptr::copy_nonoverlapping(bytes.as_ptr(), out_ptr, bytes.len()); }
    // convey length to host
    unsafe { LAST_LEN = bytes.len(); }
    std::mem::forget(bytes);
    out_ptr
}

fn esc(s: &str) -> String {
    s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
}

fn build_calendar(data: &BuildInput) -> String {
    let tz = data.timezone.as_deref().unwrap_or("Europe/Paris");
    let name = data.calendar_name.as_deref().unwrap_or("My Calendar");
    let estimated = 256 + data.events.len().saturating_mul(160);
    let mut out = String::with_capacity(estimated);
    out.push_str("BEGIN:VCALENDAR\r\n");
    out.push_str("VERSION:2.0\r\n");
    out.push_str("PRODID:-//UFR Info//Schedule Builder 0.1//EN\r\n");
    out.push_str("CALSCALE:GREGORIAN\r\n");
    out.push_str(&format!("X-WR-CALNAME:{}\r\n", esc(name)));
    out.push_str(&format!("X-WR-TIMEZONE:{}\r\n", tz));

    for ev in &data.events {
        let uid = ev.uid.clone().unwrap_or_else(|| make_uid(&ev.start, &ev.end, &ev.summary));
        out.push_str("BEGIN:VEVENT\r\n");
        // DTSTAMP is required by RFC 5545; use event start as a reasonable default
        out.push_str(&format!("DTSTAMP:{}\r\n", to_ics_dt(&ev.start)));
        out.push_str(&format!("UID:{}\r\n", esc(&uid)));
        out.push_str(&format!("DTSTART:{}\r\n", to_ics_dt(&ev.start)));
        out.push_str(&format!("DTEND:{}\r\n", to_ics_dt(&ev.end)));
        // RRULE/EXDATE for base events; RECURRENCE-ID for overrides
        if let Some(rid) = &ev.recurrence_id {
            out.push_str(&format!("RECURRENCE-ID:{}\r\n", to_ics_dt(rid)));
        } else {
            if let Some(rr) = &ev.rrule { out.push_str(&format!("RRULE:{}\r\n", rr.trim())); }
            if let Some(xs) = &ev.exdates {
                for x in xs { out.push_str(&format!("EXDATE:{}\r\n", to_ics_dt(x))); }
            }
        }
        out.push_str(&format!("SUMMARY:{}\r\n", esc(&ev.summary)));
        if let Some(loc) = &ev.location { out.push_str(&format!("LOCATION:{}\r\n", esc(loc))); }
        out.push_str("END:VEVENT\r\n");
    }
    out.push_str("END:VCALENDAR\r\n");
    out
}

fn to_ics_dt(iso: &str) -> String {
    // Normalize common ISO-8601 inputs to RFC5545 DATE-TIME (UTC) basic form: YYYYMMDDTHHMMSSZ
    // Examples input: 2025-09-01T08:00:00Z or 2025-09-01T08:00:00+01:00
    let s = iso.trim();
    let mut digits: String = s.chars().filter(|c| c.is_ascii_digit()).collect();
    if digits.len() < 14 {
        // Pad missing HHMMSS with zeros if only date or incomplete time was provided
        while digits.len() < 14 { digits.push('0'); }
    }
    // Insert 'T' between date and time components and enforce Z suffix
    format!("{}T{}Z", &digits[0..8], &digits[8..14])
}

fn make_uid(start: &str, end: &str, summary: &str) -> String {
    // Simple FNV-1a 64-bit hash
    let mut hash: u64 = 0xcbf29ce484222325;
    for b in start.as_bytes().iter().chain(end.as_bytes()).chain(summary.as_bytes()) {
        hash ^= *b as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{:016x}@ics", hash)
}

// ---- Selection-based building (moves filtering into Rust) ----

#[derive(Debug, Deserialize)]
struct SelectionItem {
    code: String,
    #[serde(default)]
    group: Option<String>,
    source: String,
}

#[derive(Debug, Deserialize)]
struct VariantIn {
    #[serde(default)]
    group: Option<String>,
    #[allow(dead_code)]
    #[serde(default)]
    r#type: Option<String>,
    events: Vec<EventIn>,
}

#[derive(Debug, Deserialize)]
struct CourseIn {
    name: String,
    code: String,
    #[serde(default)]
    special: bool,
    #[allow(dead_code)]
    groups: Vec<String>,
    variants: Vec<VariantIn>,
}

#[derive(Debug, Deserialize)]
struct BundleIn {
    #[allow(dead_code)]
    master_year: String,
    #[allow(dead_code)]
    parcours: String,
    courses: Vec<CourseIn>,
}

#[derive(Debug, Deserialize)]
struct BuildFromSelectionInput {
    calendar_name: Option<String>,
    timezone: Option<String>,
    master_year: Option<String>,
    parcours: Option<String>,
    items: Vec<SelectionItem>,
    bundles: HashMap<String, BundleIn>,
}

#[no_mangle]
pub extern "C" fn build_ics_from_selection(ptr: *mut u8, len: usize) -> *mut u8 {
    // Safety: JS ensures ptr points to `len` bytes of input JSON
    let input = unsafe { std::slice::from_raw_parts(ptr, len) };
    let json = match std::str::from_utf8(input) { Ok(s) => s, Err(_) => "{}" };
    let data: BuildFromSelectionInput = serde_json::from_str(json).unwrap_or(BuildFromSelectionInput {
        calendar_name: Some("My Calendar".into()),
        timezone: Some("Europe/Paris".into()),
        master_year: None,
        parcours: None,
        items: vec![],
        bundles: HashMap::new(),
    });

    let mut out_events: Vec<EventIn> = Vec::new();

    // Pick events by sources according to items
    for it in &data.items {
        if let Some(bundle) = data.bundles.get(&it.source) {
            // Find course by code (case-insensitive, ASCII)
            if let Some(course) = bundle
                .courses
                .iter()
                .find(|c| c.code.eq_ignore_ascii_case(&it.code))
            {
                for v in &course.variants {
                    // When a group is selected, include matching group variants,
                    // and also include variants with no group (shared across groups).
                    if let Some(ref g_it) = it.group {
                        match &v.group {
                            Some(g_v) if g_v == g_it => { /* ok */ }
                            None => { /* shared variant, include */ }
                            _ => { continue; }
                        }
                    }
                    for ev in &v.events {
                        out_events.push(EventIn {
                            start: ev.start.clone(),
                            end: ev.end.clone(),
                            summary: ev.summary.clone(),
                            location: ev.location.clone(),
                            uid: ev.uid.clone(),
                            rrule: ev.rrule.clone(),
                            exdates: ev.exdates.clone(),
                            recurrence_id: ev.recurrence_id.clone(),
                        });
                    }
                }
            }
        }
    }

    // Collect special events from selected bundles, filtered by selected parcours/master_year if provided
    for (_k, b) in &data.bundles {
        if let Some(ref sel_py) = data.master_year {
            if b.master_year != *sel_py { continue; }
        }
        if let Some(ref sel_parcours) = data.parcours {
            if b.parcours != *sel_parcours { continue; }
        }
        for c in &b.courses {
            if c.special {
                for v in &c.variants {
                    for ev in &v.events {
                        out_events.push(EventIn {
                            start: ev.start.clone(),
                            end: ev.end.clone(),
                            summary: c.name.clone(),
                            location: ev.location.clone(),
                            uid: ev.uid.clone(),
                            rrule: ev.rrule.clone(),
                            exdates: ev.exdates.clone(),
                            recurrence_id: ev.recurrence_id.clone(),
                        });
                    }
                }
            }
        }
    }

    let cal = BuildInput {
        calendar_name: data.calendar_name,
        timezone: data.timezone,
        events: out_events,
    };
    let ics = build_calendar(&cal);
    let bytes = ics.into_bytes();
    let out_ptr = alloc(bytes.len());
    unsafe { std::ptr::copy_nonoverlapping(bytes.as_ptr(), out_ptr, bytes.len()); }
    // convey length to host
    unsafe { LAST_LEN = bytes.len(); }
    std::mem::forget(bytes);
    out_ptr
}
