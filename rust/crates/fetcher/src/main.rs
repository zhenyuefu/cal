use std::{collections::HashMap, env, fs, path::PathBuf, time::Duration};

use anyhow::{Context, Result};
use backoff::{future::retry, ExponentialBackoff};
use reqwest::{header, StatusCode};
use serde::{Deserialize, Serialize};

const PARCOURS: &[&str] = &["ANDROIDE","DAC","STL","IMA","BIM","SAR","SESI","SFPN"];
const MASTER_YEARS: &[&str] = &["M1","M2"];
const BASE: &str = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/{parcours}/{master_year}_{parcours}/";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct EtagMap(HashMap<String, String>);

#[tokio::main]
async fn main() -> Result<()> {
    let data_dir = PathBuf::from("data");
    let download_dir = data_dir.join("download");
    fs::create_dir_all(&download_dir)?;
    let etag_path = data_dir.join("etag-map.json");
    let mut etags: EtagMap = if etag_path.exists() {
        let s = fs::read_to_string(&etag_path).context("read etag-map.json")?;
        serde_json::from_str(&s).unwrap_or_default()
    } else {
        EtagMap::default()
    };

    let username = env::var("CAL_USERNAME").unwrap_or_default();
    let password = env::var("CAL_PASSWORD").unwrap_or_default();
    if username.is_empty() || password.is_empty() {
        eprintln!("Warning: CAL_USERNAME/CAL_PASSWORD not set; requests may fail.");
    }

    let client = reqwest::Client::builder()
        .user_agent("cal-fetcher/0.1")
        .connect_timeout(Duration::from_secs(15))
        .timeout(Duration::from_secs(60))
        .build()?;

    for &year in MASTER_YEARS {
        for &p in PARCOURS {
            let url = BASE.replace("{parcours}", p).replace("{master_year}", year);
            match fetch_one(&client, &url, &mut etags, &username, &password).await {
                Ok(Some((bytes, etag))) => {
                    let file = download_dir.join(format!("{}_{}.ics", year, p));
                    fs::write(&file, &bytes).with_context(|| format!("write {}", file.display()))?;
                    println!("saved {} ({} bytes) etag={}", file.display(), bytes.len(), etag.unwrap_or_default());
                }
                Ok(None) => {
                    println!("no change for {} {}", year, p);
                }
                Err(e) => {
                    eprintln!("error fetching {} {}: {e:#}", year, p);
                }
            }
        }
    }

    fs::write(&etag_path, serde_json::to_vec_pretty(&etags)?).context("write etag-map.json")?;
    Ok(())
}

async fn fetch_one(
    client: &reqwest::Client,
    url: &str,
    etags: &mut EtagMap,
    username: &str,
    password: &str,
) -> Result<Option<(bytes::Bytes, Option<String>)>> {
    let mut req = client.get(url);
    if !username.is_empty() {
        req = req.basic_auth(username, Some(password));
    }
    if let Some(et) = etags.0.get(url) {
        req = req.header(header::IF_NONE_MATCH, et.as_str());
    }

    let policy = ExponentialBackoff {
        max_elapsed_time: Some(Duration::from_secs(60)),
        max_interval: Duration::from_secs(8),
        ..ExponentialBackoff::default()
    };

    let res = retry(policy, || async {
        let resp = req.try_clone().unwrap().send().await.map_err(|e| backoff::Error::transient(anyhow::anyhow!(e)))?;
        match resp.status() {
            StatusCode::OK | StatusCode::NOT_MODIFIED => Ok(resp),
            StatusCode::NOT_FOUND | StatusCode::UNAUTHORIZED | StatusCode::FORBIDDEN => {
                Err(backoff::Error::permanent(anyhow::anyhow!(
                    "{status} for {url}",
                    status = resp.status(),
                    url = url
                )))
            }
            StatusCode::TOO_MANY_REQUESTS | StatusCode::BAD_GATEWAY | StatusCode::SERVICE_UNAVAILABLE | StatusCode::GATEWAY_TIMEOUT => {
                Err(backoff::Error::transient(anyhow::anyhow!("{status} transient", status = resp.status())))
            }
            s if s.is_server_error() => Err(backoff::Error::transient(anyhow::anyhow!("server {s}"))),
            s => Err(backoff::Error::permanent(anyhow::anyhow!("unexpected status {s}"))),
        }
    }).await;

    match res {
        Ok(resp) => {
            if resp.status() == StatusCode::NOT_MODIFIED {
                return Ok(None);
            }
            let etag = resp
                .headers()
                .get(header::ETAG)
                .and_then(|v| v.to_str().ok())
                .map(|s| s.to_string());
            let bytes = resp.bytes().await?;
            if let Some(ref et) = etag {
                etags.0.insert(url.to_string(), et.clone());
            } else {
                // Fallback: weak etag by content hash
                let fallback = format!("W/\"{}\"", blake3::hash(&bytes).to_hex());
                etags.0.insert(url.to_string(), fallback);
            }
            Ok(Some((bytes, etag)))
        }
        Err(e) => {
            eprintln!("{url} failed permanently: {e:#}");
            Ok(None)
        }
    }
}
