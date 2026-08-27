use anyhow::{Context, Result};
use std::path::PathBuf;
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Arc;
use tokio::fs::OpenOptions;
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use tokio::sync::watch;
use tokio::time::{sleep, Duration};

use crate::events;

/// What a tee observed. Every field explains a difference from the bare command.
#[derive(Debug, Default, Clone)]
pub struct TeeOutcome {
    /// The downstream stopped accepting writes; forwarding stopped here.
    pub forward_closed: bool,
    /// An anchor for a drain bound, not a count of bytes the downstream missed:
    /// detection lags the close itself by up to two of the 8192-byte reads
    /// below. A forwarded write's error surfaces one chunk late —
    /// `Blocking::poll_write` hands the chunk to a blocking task and returns
    /// `Ok` without waiting, so the *next* write is what reports it — and the
    /// write that failed was already past the close. The trigger chunk is
    /// counted whole, which is exact rather than approximate: `poll_write`
    /// fails it from its Busy arm having accepted none of it, so there is no
    /// prefix to subtract. The chunk that may have been delivered in part is
    /// the preceding one, still in flight when the downstream closed, and it is
    /// never counted here at all.
    pub bytes_since_close_detected: u64,
    /// The drain reached `drain_cap_bytes` and the read end was dropped. The
    /// capture is short of what the child went on to write, by design.
    pub drain_capped: bool,
}

/// The tee's read size, and the boundary between the two capture-side regimes.
///
/// A child whose output exceeds this is read in more than one chunk, so a
/// forward write's error surfaces at the next write, inside the read loop. A
/// child whose whole output fits in one read has no next write, so its error can
/// appear nowhere but the flush at EOF. Which regime a test exercises is decided
/// by this number and nothing else: `core_test.rs`'s `ARRIVES_IN_ONE_CHUNK` is
/// 2000 bytes precisely because 2000 is under it. Changing it silently moves
/// that test into the other regime, where it passes while guarding nothing —
/// `read_buf_divides_the_two_regimes` below is what makes that loud.
const READ_BUF: usize = 8192;

/// Tee `reader` -> (capture file at `capture_path`) + (forward writer).
/// Updates `last_activity_unix_ms` on each non-empty read. Appends
/// `first_byte` + (later) `silence`/`silence_break` events to `events_dir`
/// (the task or child dir that owns events.jsonl).
///
/// A downstream that stops accepting writes stops the forwarding, not the
/// child and not the capture: a caller going away is expected and capturing on
/// is the point. It is still a difference from bare, so it is stated on stderr
/// and returned rather than inferred from a short stream.
///
/// Draining on alone is how a runaway producer fills the disk, so it is bounded:
/// `drain_cap_bytes` past the close the reader is dropped, which closes the read
/// end of the child's pipe and leaves the child facing the `SIGPIPE` bare would
/// have given it. The bound applies only once forwarding has failed, so an
/// ordinary run never approaches it. Every value is a bound and every value
/// means the same thing, `0` included — it stops at the first chunk read after
/// the one that *detected* the close, which
/// `TeeOutcome::bytes_since_close_detected` places up to two reads past the
/// close itself. A caller with no downstream to lose passes `UNCAPPED`.
///
/// Returns when the reader closes (EOF), or when the drain reaches its bound.
pub async fn tee<R, W>(
    stream_name: &'static str,
    mut reader: R,
    capture_path: PathBuf,
    mut forward: W,
    drain_cap_bytes: u64,
    last_activity_unix_ms: Arc<AtomicI64>,
    events_dir: PathBuf,
) -> Result<TeeOutcome>
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

    let mut buf = vec![0u8; READ_BUF];
    let mut wrote_first_byte = false;
    let mut outcome = TeeOutcome::default();
    loop {
        let n = reader.read(&mut buf).await?;
        if n == 0 {
            break;
        }
        let chunk = &buf[..n];
        file.write_all(chunk).await?;

        if outcome.forward_closed {
            outcome.bytes_since_close_detected += n as u64;
            if outcome.bytes_since_close_detected >= drain_cap_bytes {
                outcome.drain_capped = true;
                state(&format!(
                    "agent-tools: {stream_name} drain bound of {drain_cap_bytes} bytes \
                     reached; dropping the read end so the child sees SIGPIPE as bare\n"
                ));
                break;
            }
        } else if let Err(e) = forward.write_all(chunk).await {
            outcome.forward_closed = true;
            outcome.bytes_since_close_detected += n as u64;
            state_forward_closed(stream_name, &e, &capture_path);
        }
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
    // The second write site for the one-chunk-late error stated on
    // `TeeOutcome::bytes_since_close_detected`. The last chunk has no next
    // write, so its error can appear nowhere but here; and a child whose whole
    // output arrives in one 8192-byte read has no earlier chunk either, so here
    // is the only place `EPIPE` ever appears. Discarded, the caller's stream is
    // silently short by whatever was still in flight and the outcome says
    // forwarding was fine.
    match forward.flush().await {
        Err(e) if !outcome.forward_closed => {
            outcome.forward_closed = true;
            state_forward_closed(stream_name, &e, &capture_path);
        }
        // Already reported in the loop, or nothing to report.
        _ => {}
    }
    Ok(outcome)
}

/// Say something once on the caller's stderr, from inside a tee.
///
/// Not `eprintln!`: that panics when the write fails, and the stream that just
/// closed can be this one — `cmd 2>&1 | head -3` puts both of the caller's
/// descriptors on the pipe `head` drops, which is exactly the shape the merge
/// rule admits. A panic there would kill the tee, stopping the capture the
/// message is about, and the outcome would come back saying nothing happened.
///
/// Formatted by the caller and written once, so a notice cannot be spliced by
/// the other stream's tee mid-line: one `write` under `PIPE_BUF` is atomic,
/// while `write_fmt` emits a syscall per fragment. Callers pass the trailing
/// newline; nothing here adds one, because a second write would break that.
fn state(msg: &str) {
    use std::io::Write as _;
    let _ = std::io::stderr().write_all(msg.as_bytes());
}

/// Say that forwarding stopped and capturing did not.
fn state_forward_closed(stream_name: &str, err: &std::io::Error, capture_path: &std::path::Path) {
    state(&format!(
        "agent-tools: {stream_name} downstream closed ({err}); still capturing to {}\n",
        capture_path.display()
    ));
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
                let _ = events::append(
                    &dir,
                    "silence",
                    serde_json::json!({"stream": stream, "since_ms": gap_ms}),
                );
            });
            warned = true;
        } else if warned && cur > last_seen {
            let dir = events_dir.clone();
            let stream = stream_name.to_string();
            tokio::task::spawn_blocking(move || {
                let _ =
                    events::append(&dir, "silence_break", serde_json::json!({"stream": stream}));
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

    /// A bound no capture can reach, for callers with no downstream to lose.
    /// Not a sentinel: `tee` compares against it like any other value, so there
    /// is no special case to leave untested. `0` is equally valid and means
    /// "stop at the first chunk after the one that detected the close" — which
    /// `TeeOutcome::bytes_since_close_detected` places up to two reads past the
    /// close itself.
    const UNCAPPED: u64 = u64::MAX;

    /// `core_test.rs` is an integration test against a binary-only crate, so it
    /// cannot name `READ_BUF` and cannot fail when it moves. Pinning the value
    /// from this side is the only thing standing between a resized buffer and a
    /// flush-regime test that quietly stops testing the flush.
    #[test]
    fn read_buf_divides_the_two_regimes() {
        assert_eq!(
            READ_BUF, 8192,
            "core_test.rs's `a_close_seen_only_at_the_flush_is_stated_too` needs a \
             child whose whole output arrives in one read, and its \
             `ARRIVES_IN_ONE_CHUNK` producer is 2000 bytes only because 2000 is \
             under 8192. Move READ_BUF below that and the error surfaces in the \
             read loop instead: the test still passes, guarding nothing. Resize \
             `ARRIVES_IN_ONE_CHUNK` in the same commit."
        );
    }

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
            UNCAPPED,
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
            "stdout", reader, cap, forward_w, UNCAPPED, last, evts_dir,
        ));
        writer.write_all(b"forward me\n").await.unwrap();
        drop(writer);
        h.await.unwrap().unwrap();

        let mut got = Vec::new();
        tokio::io::AsyncReadExt::read_to_end(&mut forward_r, &mut got)
            .await
            .unwrap();
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
            UNCAPPED,
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

        let h = tokio::spawn(watch_silence(
            "stdout",
            last.clone(),
            1000,
            evts_dir.clone(),
            rx,
        ));

        tokio::time::sleep(Duration::from_millis(1500)).await;
        let _ = tx.send(true);
        h.await.unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;
        let evts = events::read_all(&evts_dir).unwrap();
        assert!(
            evts.iter().any(|e| e.kind == "silence"),
            "events: {:?}",
            evts
        );
    }
}
