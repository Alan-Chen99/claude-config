use anyhow::{Context, Result};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicI64, Ordering};
use tokio::fs::OpenOptions;
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use tokio::sync::watch;
use tokio::time::{sleep, Duration};

use crate::events;

/// Tee `reader` -> (capture file at `capture_path`) + (forward writer).
/// Updates `last_activity_unix_ms` on each non-empty read. Appends
/// `first_byte` + (later) `silence`/`silence_break` events to `events_dir`
/// (the task or child dir that owns events.jsonl).
///
/// Returns when the reader closes (EOF).
pub async fn tee<R, W>(
    stream_name: &'static str,
    mut reader: R,
    capture_path: PathBuf,
    mut forward: W,
    last_activity_unix_ms: Arc<AtomicI64>,
    events_dir: PathBuf,
) -> Result<()>
where
    R: AsyncRead + Unpin,
    W: AsyncWrite + Unpin,
{
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&capture_path)
        .await
        .with_context(|| format!("open capture {}", capture_path.display()))?;

    let mut buf = vec![0u8; 8192];
    let mut wrote_first_byte = false;
    loop {
        let n = reader.read(&mut buf).await?;
        if n == 0 {
            break;
        }
        let chunk = &buf[..n];
        file.write_all(chunk).await?;
        let _ = forward.write_all(chunk).await;
        last_activity_unix_ms.store(now_unix_ms(), Ordering::SeqCst);
        if !wrote_first_byte {
            wrote_first_byte = true;
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "first_byte", serde_json::json!({"stream": stream}));
            });
        }
    }
    file.flush().await.ok();
    let _ = forward.flush().await;
    Ok(())
}

/// Run a per-stream silence watcher. Polls every 1 s; if the gap between
/// `now` and `last_activity_unix_ms` exceeds `threshold_ms`, emits `silence`
/// once until the next byte (which emits `silence_break`).
pub async fn watch_silence(
    stream_name: &'static str,
    last_activity_unix_ms: Arc<AtomicI64>,
    threshold_ms: u64,
    events_dir: PathBuf,
    mut cancel: watch::Receiver<bool>,
) {
    let mut last_seen = last_activity_unix_ms.load(Ordering::SeqCst);
    let mut warned = false;
    loop {
        tokio::select! {
            _ = sleep(Duration::from_secs(1)) => {}
            changed = cancel.changed() => {
                if changed.is_err() || *cancel.borrow() { break; }
            }
        }
        let cur = last_activity_unix_ms.load(Ordering::SeqCst);
        let now = now_unix_ms();
        let gap = now - cur;
        if !warned && gap > threshold_ms as i64 {
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            let gap_ms = gap;
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "silence", serde_json::json!({"stream": stream, "since_ms": gap_ms}));
            });
            warned = true;
        } else if warned && cur > last_seen {
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            tokio::task::spawn_blocking(move || {
                let _ = events::append(&dir, "silence_break", serde_json::json!({"stream": stream}));
            });
            warned = false;
        }
        last_seen = cur;
    }
}

fn now_unix_ms() -> i64 {
    chrono::Utc::now().timestamp_millis()
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use tokio::io::AsyncWriteExt;

    #[tokio::test]
    async fn tee_writes_capture_file() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap.clone(),
            tokio::io::sink(),
            last.clone(),
            evts_dir,
        ));

        writer.write_all(b"hello\n").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        let captured = std::fs::read(&cap).unwrap();
        assert_eq!(captured, b"hello\n");
    }

    #[tokio::test]
    async fn tee_forwards_through_to_writer() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let (forward_w, mut forward_r) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap,
            forward_w,
            last,
            evts_dir,
        ));
        writer.write_all(b"forward me\n").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        let mut got = Vec::new();
        tokio::io::AsyncReadExt::read_to_end(&mut forward_r, &mut got).await.unwrap();
        assert_eq!(got, b"forward me\n");
    }

    #[tokio::test]
    async fn tee_records_first_byte_event() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let evts_dir = dir.path().to_path_buf();
        let (reader, mut writer) = tokio::io::duplex(1024);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap,
            tokio::io::sink(),
            last,
            evts_dir.clone(),
        ));
        writer.write_all(b"x").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;
        let evts = events::read_all(&evts_dir).unwrap();
        assert!(evts.iter().any(|e| e.kind == "first_byte"));
    }

    #[tokio::test]
    async fn silence_watcher_emits_event_after_threshold() {
        let dir = TempDir::new().unwrap();
        let evts_dir = dir.path().to_path_buf();
        let last = Arc::new(AtomicI64::new(now_unix_ms() - 5000));
        let (tx, rx) = watch::channel(false);

        let h = tokio::spawn(watch_silence("stdout", last.clone(), 1000, evts_dir.clone(), rx));

        tokio::time::sleep(Duration::from_millis(1500)).await;
        let _ = tx.send(true);
        h.await.unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;
        let evts = events::read_all(&evts_dir).unwrap();
        assert!(evts.iter().any(|e| e.kind == "silence"), "events: {:?}", evts);
    }
}
