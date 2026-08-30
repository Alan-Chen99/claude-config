use anyhow::Result;
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
    /// The post-close drain reached its bound and the read end was dropped.
    /// The capture is short of what the child went on to write, by design.
    pub drain_capped: bool,
    /// The capture reached its bound with no downstream ever in the picture,
    /// and the read end was dropped. Kept apart from `drain_capped` because the
    /// two send a reader to different places: one says a caller went away and
    /// the wrapper kept reading past it, the other that nothing was ever
    /// forwarded and the capture itself is what ran out of room. A backgrounded
    /// child reported as `drain capped` would have its reader hunting a
    /// downstream that never existed.
    pub capture_capped: bool,
    /// The capture could not be written, and capturing stopped there. Holds
    /// what the OS said. Set once, by whichever of the open, a chunk write or
    /// the flush reached it first — a capture that has already stopped cannot
    /// stop again, and one message per stream is the contract the tests pin.
    pub capture_error: Option<String>,
}

/// The tee's read size, and the boundary between the two capture-side regimes.
///
/// A child whose output exceeds this is read in more than one chunk, so a
/// forward write's error surfaces at the next write, inside the read loop. A
/// child whose whole output fits in one read has no next write, so its error can
/// appear nowhere but the flush at EOF. Which regime a test exercises is decided
/// by this number and nothing else: `core_test.rs`'s `ARRIVES_IN_ONE_CHUNK` and
/// `ONE_CHUNK_THEN_EXITS_5` are 2000 bytes precisely because 2000 is under it.
/// Changing it silently moves their tests into the other regime, where they pass
/// while guarding nothing — `read_buf_divides_the_two_regimes` below is what
/// makes that loud.
const READ_BUF: usize = 8192;

/// What stops a tee, and from which byte it counts.
///
/// Not a policy toggle: the two arms are the two shapes a run has, and each
/// names the only thing that can end a runaway producer in its own shape. A
/// forwarded run ends one because the caller goes away and the drain past that
/// point is bounded. A run with nowhere to forward to has no downstream that
/// can go away, so a bound counting from a refusal never arms — the count has
/// to start at the first byte or nothing ever stops it. `run --background` is
/// that second shape, and its wrapper outlives the session that started it, so
/// the case the bound exists for is exactly the case with nobody left watching.
#[derive(Debug, Clone, Copy)]
pub enum Bound {
    /// Bytes captured after the downstream stopped accepting writes. An
    /// ordinary run never approaches it: forwarding does not fail.
    AfterForwardCloses(u64),
    /// Bytes captured at all, counted from the first. There is no downstream to
    /// lose, so the whole run is what a bound has to cover.
    Captured(u64),
}

impl Bound {
    /// The bound's size, for the notice that says it was reached.
    fn bytes(self) -> u64 {
        match self {
            Bound::AfterForwardCloses(n) | Bound::Captured(n) => n,
        }
    }

    /// What the bound counts, so its notice names the thing that ran out rather
    /// than the mechanism both share.
    fn what(self) -> &'static str {
        match self {
            Bound::AfterForwardCloses(_) => "drain",
            Bound::Captured(_) => "capture",
        }
    }
}

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
/// A capture that cannot be written stops the capturing, and neither the
/// forwarding nor the child: the wrapper's disk is not the child's fault. A tee
/// that gave up here would leave the pipe undrained, and the child would die of
/// a `SIGPIPE` the wrapper inflicted and then be reported as `final(141)` — a
/// plausible and wrong story about a failure that was never its own. Stated on
/// stderr and returned for the same reason the forward close is, since `final(0)`
/// beside a capture that stopped growing an hour ago reads as a complete record.
///
/// Capturing on alone is how a runaway producer fills the disk, so it is
/// bounded, and `bound` says from which byte the count runs. Reaching it drops
/// the reader either way, which closes the read end of the child's pipe and
/// leaves the child facing the `SIGPIPE` bare would have given it. Every value
/// is a bound and every value means the same thing, `0` included — under
/// `Bound::AfterForwardCloses` it stops at the first chunk read after the one
/// that *detected* the close, which `TeeOutcome::bytes_since_close_detected`
/// places up to two reads past the close itself. Only this file's own tests
/// want a bound nothing can reach, and they pass `UNCAPPED` from their
/// module.
///
/// Returns when the reader closes (EOF), or when `bound` is reached.
pub async fn tee<R, W>(
    stream_name: &'static str,
    mut reader: R,
    capture_path: PathBuf,
    mut forward: W,
    bound: Bound,
    last_activity_unix_ms: Arc<AtomicI64>,
    events_dir: PathBuf,
) -> Result<TeeOutcome>
where
    R: AsyncRead + Unpin,
    W: AsyncWrite + Unpin,
{
    let mut outcome = TeeOutcome::default();

    // `None` is a capture that is not happening. An open that fails leaves the
    // rest of the tee running against it, because forwarding the child's bytes
    // and draining its pipe are worth more than the record of them.
    let mut file = match OpenOptions::new()
        .create(true)
        .append(true)
        .open(&capture_path)
        .await
    {
        Ok(f) => Some(f),
        Err(e) => {
            outcome.capture_error = Some(e.to_string());
            state(&format!(
                "agent-tools: capture to {} could not be opened ({e}); forwarding \
                 continues, nothing is captured\n",
                capture_path.display()
            ));
            None
        }
    };

    let mut buf = vec![0u8; READ_BUF];
    let mut wrote_first_byte = false;
    let mut captured = 0u64;
    loop {
        let n = reader.read(&mut buf).await?;
        if n == 0 {
            break;
        }
        let chunk = &buf[..n];
        capture_or_stop_capturing(&mut file, chunk, &capture_path, &mut outcome).await;

        // Snapshot before the write, because the write is what can change it:
        // the chunk that *detects* a close is counted by
        // `forward_or_stop_forwarding` and must not also be compared against
        // the bound on the same pass. That is the lag
        // `TeeOutcome::bytes_since_close_detected` describes, and
        // `the_chunk_that_detects_the_close_is_not_compared_against_the_bound`
        // is what holds it. Reading `outcome.forward_closed` after the write
        // instead would stop the drain one read early.
        let was_closed = outcome.forward_closed;
        // A stream that has already lost its downstream is not written to
        // again: `forward_or_stop_forwarding` states the close where it happens,
        // and one message per stream is the contract.
        if !was_closed {
            forward_or_stop_forwarding(
                &mut forward,
                chunk,
                stream_name,
                &capture_path,
                &mut outcome,
            )
            .await;
        }
        // Which bound is in force decides only when the tee stops, never where
        // the bytes go — so the arms below count, and nothing else.
        let over_bound = match bound {
            Bound::AfterForwardCloses(cap) => {
                if was_closed {
                    outcome.bytes_since_close_detected += n as u64;
                    outcome.bytes_since_close_detected >= cap
                } else {
                    false
                }
            }
            Bound::Captured(cap) => {
                captured += n as u64;
                captured >= cap
            }
        };
        if over_bound {
            // One flag per bound, so the note a reader ends up with names the
            // bound that actually stopped this capture.
            match bound {
                Bound::AfterForwardCloses(_) => outcome.drain_capped = true,
                Bound::Captured(_) => outcome.capture_capped = true,
            }
            let what = bound.what();
            let size = bound.bytes();
            state(&format!(
                "agent-tools: {stream_name} {what} bound of {size} bytes reached; \
                 dropping the read end so the child sees SIGPIPE as bare\n"
            ));
            break;
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
    // Both flushes below are second write sites for the one-chunk-late error
    // stated on `TeeOutcome::bytes_since_close_detected`, which `tokio::fs::File`
    // has too: `Blocking::poll_write` hands the chunk to a blocking task and
    // returns `Ok`, so the write's own error is reported at the next write or
    // here. The last chunk has no next write, and a child whose whole output
    // arrives in one 8192-byte read has no earlier chunk either, so for that
    // child this is the only place either failure ever appears. Discarded, a
    // capture that never happened comes back as a clean outcome.
    if let Some(f) = file.as_mut() {
        match f.flush().await {
            // Vacuous today and kept deliberately: `capture_or_stop_capturing`
            // sets `capture_error` and clears `file` together, so reaching here
            // at all means no error has been recorded. Its mirror on the
            // forward side is not vacuous — nothing ever takes `forward` — so
            // the two guards look symmetric and rest on different invariants.
            Err(e) if outcome.capture_error.is_none() => {
                outcome.capture_error = Some(e.to_string());
                state(&format!(
                    "agent-tools: capture to {} failed at the flush ({e}); the capture is \
                     short by whatever was still in flight\n",
                    capture_path.display()
                ));
            }
            // Already reported in the loop, or nothing to report.
            _ => {}
        }
    }
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

/// Write one chunk to the capture. Failing costs the capture and nothing else.
///
/// The child is not at fault for the wrapper's disk, so its pipe keeps being
/// drained and its bytes keep reaching the caller. `file` is taken to `None`, so
/// there is no second write to fail and no second message: a stream states this
/// once, naming where the record stops.
async fn capture_or_stop_capturing(
    file: &mut Option<tokio::fs::File>,
    chunk: &[u8],
    capture_path: &std::path::Path,
    outcome: &mut TeeOutcome,
) {
    let Some(f) = file.as_mut() else {
        return;
    };
    let Err(e) = f.write_all(chunk).await else {
        return;
    };
    outcome.capture_error = Some(e.to_string());
    state(&format!(
        "agent-tools: capture to {} failed ({e}); forwarding continues, the capture \
         is incomplete from here\n",
        capture_path.display()
    ));
    *file = None;
}

/// Write one chunk to the downstream. Failing costs the forwarding and nothing
/// else.
///
/// A caller going away is expected and capturing on is the point, so the loop
/// keeps reading — under the drain bound the caller applies, which is why the
/// trigger chunk is counted here and compared against only on the next one.
async fn forward_or_stop_forwarding<W>(
    forward: &mut W,
    chunk: &[u8],
    stream_name: &str,
    capture_path: &std::path::Path,
    outcome: &mut TeeOutcome,
) where
    W: AsyncWrite + Unpin,
{
    if let Err(e) = forward.write_all(chunk).await {
        outcome.forward_closed = true;
        outcome.bytes_since_close_detected += chunk.len() as u64;
        state_forward_closed(stream_name, &e, capture_path);
    }
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

    /// A bound no capture can reach, for the tests here that are about
    /// something else. Not a sentinel: `tee` compares against it like any other
    /// value, so there is no special case to leave untested. `0` is equally
    /// valid and means "stop at the first chunk after the one that detected the
    /// close" — which `TeeOutcome::bytes_since_close_detected` places up to two
    /// reads past the close itself.
    const UNCAPPED: Bound = Bound::AfterForwardCloses(u64::MAX);

    /// A downstream that is already gone: every write is `EPIPE`, with none of
    /// `tokio::io::stdout`'s buffering, so the failure lands on the write that
    /// caused it rather than a chunk later.
    struct AlwaysBrokenPipe;

    impl tokio::io::AsyncWrite for AlwaysBrokenPipe {
        fn poll_write(
            self: std::pin::Pin<&mut Self>,
            _: &mut std::task::Context<'_>,
            _: &[u8],
        ) -> std::task::Poll<std::io::Result<usize>> {
            std::task::Poll::Ready(Err(std::io::Error::from(std::io::ErrorKind::BrokenPipe)))
        }
        fn poll_flush(
            self: std::pin::Pin<&mut Self>,
            _: &mut std::task::Context<'_>,
        ) -> std::task::Poll<std::io::Result<()>> {
            std::task::Poll::Ready(Ok(()))
        }
        fn poll_shutdown(
            self: std::pin::Pin<&mut Self>,
            _: &mut std::task::Context<'_>,
        ) -> std::task::Poll<std::io::Result<()>> {
            std::task::Poll::Ready(Ok(()))
        }
    }

    /// `core_test.rs` is an integration test against a binary-only crate, so it
    /// cannot name `READ_BUF` and cannot fail when it moves. Pinning the value
    /// from this side is the only thing standing between a resized buffer and a
    /// flush-regime test that quietly stops testing the flush. There are two of
    /// those, one per side of the tee, and one `READ_BUF` decides both.
    #[test]
    fn read_buf_divides_the_two_regimes() {
        assert_eq!(
            READ_BUF, 8192,
            "core_test.rs's `a_close_seen_only_at_the_flush_is_stated_too` and \
             `a_capture_that_fails_only_at_the_flush_is_stated_too` each need a \
             child whose whole output arrives in one read, and their producers \
             `ARRIVES_IN_ONE_CHUNK` and `ONE_CHUNK_THEN_EXITS_5` are 2000 bytes \
             only because 2000 is under 8192. Move READ_BUF below that and the \
             error surfaces in the read loop instead: both tests still pass, \
             guarding nothing. Resize both producers in the same commit."
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

    /// The chunk that detects the close is counted, not compared.
    ///
    /// So the lowest bound stops one read past the close rather than at it. The
    /// difference is a single read of capture, which no integration test can
    /// see: the bytes that reached the consumer before it quit vary by more than
    /// that. Here the forward fails on its first write and the reader hands over
    /// whole `READ_BUF` chunks, so the count is exact.
    /// `core_test.rs`'s `the_lowest_bound_stops_the_drain_at_the_first_read_past_the_close`
    /// asserts the same behaviour from outside and passes either way.
    #[tokio::test]
    async fn the_chunk_that_detects_the_close_is_not_compared_against_the_bound() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("stdout");
        let (reader, mut writer) = tokio::io::duplex(4 * READ_BUF);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "stdout",
            reader,
            cap.clone(),
            AlwaysBrokenPipe,
            Bound::AfterForwardCloses(0),
            last,
            dir.path().to_path_buf(),
        ));
        writer.write_all(&[b'x'; 4 * READ_BUF]).await.ok();
        drop(writer);
        h.await.unwrap().unwrap();

        assert_eq!(
            std::fs::metadata(&cap).unwrap().len(),
            2 * READ_BUF as u64,
            "one read to detect the close and one to compare on; comparing on the \
             detecting chunk would stop at one"
        );
    }

    /// The bound that arms with no downstream in the picture. Nothing here can
    /// ever set `forward_closed` — `sink()` accepts every write, exactly as
    /// `Destination::Nowhere` hands the tee — so a bound counting from a close
    /// would never fire and the capture would grow to whatever the child wrote.
    #[tokio::test]
    async fn a_capture_with_nowhere_to_forward_still_stops_at_its_bound() {
        let dir = TempDir::new().unwrap();
        let cap = dir.path().join("output");
        let (reader, mut writer) = tokio::io::duplex(8 * READ_BUF);
        let last = Arc::new(AtomicI64::new(now_unix_ms()));

        let h = tokio::spawn(tee(
            "output",
            reader,
            cap.clone(),
            tokio::io::sink(),
            Bound::Captured(2 * READ_BUF as u64),
            last,
            dir.path().to_path_buf(),
        ));
        writer.write_all(&[b'y'; 6 * READ_BUF]).await.ok();
        drop(writer);
        let outcome = h.await.unwrap().unwrap();

        assert_eq!(
            std::fs::metadata(&cap).unwrap().len(),
            2 * READ_BUF as u64,
            "the capture must stop at its bound, not at what the child wrote"
        );
        assert!(
            outcome.capture_capped,
            "a capture stopped short must say so: {outcome:?}"
        );
        assert!(
            !outcome.drain_capped,
            "nothing drained past a close here; there was no close: {outcome:?}"
        );
        assert!(!outcome.forward_closed, "a sink never refuses a write");
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
        let evts = events::read_all(&evts_dir).unwrap().events;
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
        let evts = events::read_all(&evts_dir).unwrap().events;
        assert!(
            evts.iter().any(|e| e.kind == "silence"),
            "events: {:?}",
            evts
        );
    }
}
