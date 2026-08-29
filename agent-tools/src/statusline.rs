use chrono::{DateTime, Utc};

use crate::psrecord::{Capture, Record};
use crate::status;

/// Names shown before the rest become a count.
const NAMES: usize = 3;
/// Longest name shown. The cap is fixed rather than computed: terminal width is
/// absent from the statusline payload, and `tput cols` does not supply it — it
/// returns 80 against the pipe the command's stdout is, which is worse than
/// failing, because a plausible wrong width would size the line confidently and
/// wrongly.
const NAME_MAX: usize = 14;

/// The whole line, from the captures `ps` collected.
pub fn render(captures: &[Capture], now: DateTime<Utc>) -> String {
    let records: Vec<Record> = captures
        .iter()
        .map(|c| Record::build(&c.capture_dir, c.agent_id.clone(), &c.tool_use_id, now))
        .collect();
    render_records(&records, now)
}

/// The line, from records. Separate from `render` so the formatting rules can be
/// driven without a filesystem.
pub fn render_records(records: &[Record], now: DateTime<Utc>) -> String {
    let mut live: Vec<&Record> = records.iter().filter(|r| !r.terminal).collect();
    if live.is_empty() {
        // Nothing running means no row at all. A bar that always carries an
        // empty slot teaches a reader to stop looking at it.
        return String::new();
    }

    // Oldest first. This line carries no timer and freezes the instant the
    // agent goes idle — exactly when a person is reading it — so the three
    // slots that survive must go to the jobs most likely to still need
    // watching, not the ones easiest to remember unaided. A job spawned
    // seconds ago is still fresh in the person's own memory and needs no
    // reminder it is alive; a job that has been running for ten minutes is
    // the one this bar exists to reassure them about, and letting a newer,
    // short-lived job bump it into "(+N)" would defeat that.
    live.sort_by_key(|r| r.started_at);

    let remaining = live.len().saturating_sub(NAMES);
    let shown: Vec<String> = live.iter().take(NAMES).map(|r| format_one(r)).collect();
    let tail = if remaining > 0 {
        format!("  (+{remaining})")
    } else {
        String::new()
    };
    format!("▶ @{} {}{}", fmt_local_hm(now), shown.join(" · "), tail)
}

/// One shown job: `~` for a quiet child, the name capped to `NAME_MAX`, and its
/// running time. `key` decides only the marker and never reaches the line as
/// text; `name` is the one field `status::name` already routed through
/// `meta::escape_control` on its way into the record, and nothing else this
/// function prints originates anywhere but that field and its own arithmetic —
/// so nothing here needs a second escape.
fn format_one(r: &Record) -> String {
    let prefix = if r.key.starts_with("quiet") { "~" } else { "" };
    let name = status::cap_to(&r.name, NAME_MAX);
    // Every non-terminal record `Record::build` produces carries `elapsed_s`
    // (see its own field doc); `unwrap_or` is a display fallback for a shape
    // that cannot arise there, not a masked error, and it keeps a
    // hand-assembled `Record` from panicking this renderer.
    let elapsed = r.elapsed_s.unwrap_or(0.0);
    format!("{prefix}{name} {}", status::fmt_duration(elapsed))
}

/// The bar's only timestamp: hour and minute, not seconds. The line does not
/// re-render on a timer, so by the time anyone reads it some seconds have
/// already passed — showing seconds would promise a precision a frozen line
/// cannot honor.
fn fmt_local_hm(now: DateTime<Utc>) -> String {
    now.with_timezone(&chrono::Local)
        .format("%H:%M")
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Duration;

    /// A `Record` built directly rather than through `Record::build`, so the
    /// formatting rules above can be driven without a filesystem or a real
    /// wrapper. `started_at` is derived from `elapsed` so records built with
    /// different elapsed values sort against each other exactly as same-aged
    /// real captures would.
    fn rec(name: &str, key: &str, elapsed: f64) -> Record {
        let now = now_fixed();
        Record {
            name: name.to_string(),
            key: key.to_string(),
            origin: "tool",
            agent: None,
            tool_use_id: Some("toolu_test".to_string()),
            wrapper_pid: Some(1),
            child_pid: Some(2),
            started_at: Some(
                (now - Duration::milliseconds((elapsed * 1000.0) as i64))
                    .with_timezone(&chrono::Local),
            ),
            elapsed_s: Some(elapsed),
            ran_s: None,
            last_byte_at: None,
            last_byte_s: None,
            bytes: 0,
            capture: Vec::new(),
            notes: Vec::new(),
            stat_errors: Vec::new(),
            orphaned: None,
            terminal: false,
        }
    }

    #[test]
    fn nothing_running_prints_nothing() {
        assert_eq!(render_records(&[], now_fixed()), "");
    }

    #[test]
    fn a_line_stamps_itself_because_the_bar_does_not_tick() {
        let line = render_records(&[rec("build", "producing", 191.0)], now_fixed());
        assert!(line.starts_with("▶ @"), "{line}");
        assert!(line.contains("build 3m11s"), "{line}");
    }

    #[test]
    fn a_quiet_child_is_marked() {
        let line = render_records(&[rec("deploy", "quiet(30s)", 724.0)], now_fixed());
        assert!(line.contains("~deploy 12m04s"), "{line}");
    }

    #[test]
    fn beyond_three_the_rest_are_counted() {
        let rs: Vec<_> = ["a", "b", "c", "d", "e"]
            .iter()
            .map(|n| rec(n, "producing", 61.0))
            .collect();
        let line = render_records(&rs, now_fixed());
        assert!(line.contains("(+2)"), "{line}");
        assert!(
            !line.contains(" e "),
            "the fourth and fifth are not named: {line}"
        );
    }

    #[test]
    fn a_long_name_is_cut_rather_than_pushing_everything_else_off() {
        let line = render_records(
            &[rec(
                "an-extremely-long-description-of-a-task",
                "producing",
                61.0,
            )],
            now_fixed(),
        );
        assert!(line.contains('…'), "{line}");
        // `.len()` counts UTF-8 bytes, and this line carries multi-byte
        // characters (`▶`, `…`) — a byte count does not say how much of the
        // bar one name takes up. `.chars().count()` is the measure that
        // actually says what "must not own the bar" means.
        assert!(
            line.chars().count() < 60,
            "one name must not own the bar: {line}"
        );
    }

    #[test]
    fn the_oldest_job_leads_because_a_frozen_line_must_not_lose_it() {
        // Oldest first: the longest-running job is the one a person is most
        // likely to be worried about and the one this bar exists to reassure
        // them about. A job spawned seconds ago needs no such reminder, and
        // must not be allowed to bump an already-running job out to "(+N)".
        let old = rec("migrate", "producing", 600.0);
        let mid = rec("build", "producing", 300.0);
        let new = rec("probe", "producing", 5.0);
        let line = render_records(&[new, mid, old], now_fixed());
        let pos_migrate = line.find("migrate").expect("migrate is shown");
        let pos_build = line.find("build").expect("build is shown");
        let pos_probe = line.find("probe").expect("probe is shown");
        assert!(
            pos_migrate < pos_build && pos_build < pos_probe,
            "the oldest job must lead: {line}"
        );
    }

    #[test]
    fn a_raw_key_cannot_split_the_bar_or_run_escape_codes() {
        // `key` is a JSON sink upstream (see `Record::key`'s own doc) and
        // arrives raw — unlike `name`, nothing before this renderer has
        // escaped it. A `spawn-failed` status carries the wrapper's own
        // `io::Error` text verbatim, which nothing constrains; simulate one
        // holding a newline and an ANSI escape.
        let mut r = rec("deploy", "producing", 5.0);
        r.key = "spawn-failed(boom\n\x1b[31mHACKED\x1b[0m)".to_string();
        let line = render_records(&[r], now_fixed());
        assert!(
            !line.contains('\n'),
            "a newline must not split the bar: {line:?}"
        );
        assert!(
            !line.contains('\u{1b}'),
            "an escape code must not run in the terminal: {line:?}"
        );
    }

    fn now_fixed() -> chrono::DateTime<chrono::Utc> {
        chrono::DateTime::parse_from_rfc3339("2026-08-29T14:05:23Z")
            .unwrap()
            .with_timezone(&chrono::Utc)
    }
}
