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
///
/// The worst case this cap and `NAMES` together buy is 90 characters: three
/// quiet children, each named past the cap, each running long enough that
/// `fmt_duration` reaches two digits of hours — `▶ @14:05 ` is 9, `~<14
/// chars>… <Nh00m>` is 23 per child, two ` · ` separators are 6, `  (+N)` is
/// 6 (see `the_width_budget_holds_at_the_worst_case`). A third digit of hours
/// grows it further; `fmt_duration` has no cap to match this one against.
/// Claude Code renders this line as `<Text wrap="truncate">`, which cuts from
/// the *right*, so a narrow pane loses `(+N)` first — the one thing telling a
/// reader jobs are hidden — and the bar under-reports silently rather than
/// failing loudly. The same narrowness makes this cap's unit matter: it
/// counts *characters*, and a terminal spends *columns*. `tests/run_test.rs:338`
/// already exercises a CJK `--desc`; 14 wide characters cost 28 columns, not
/// 14, which pushes the real worst case toward 132.
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

    // Oldest first — the opposite of `ps --format json`/`text`, deliberately.
    // JSON's `live` array ranks every running child; order there is only
    // reading order, and every child is in the array somewhere. This bar
    // instead *selects*: everything past the third slot is dropped to a bare
    // count, not just reordered. "Which do I list first" and "which three do
    // I keep" are different questions, and a surface with a hard cap has to
    // answer the second one — that is what settles the direction, not just
    // the churn argument below. See `agent-tools/CLAUDE.md`, "What `ps` adds,
    // and what it admits", for the ordering this deliberately does not share.
    //
    // This line also carries no timer and freezes the instant the agent goes
    // idle — exactly when a person is reading it — so the three slots that
    // survive must go to the jobs most likely to still need watching, not the
    // ones easiest to remember unaided. A job spawned seconds ago is still
    // fresh in the person's own memory and needs no reminder it is alive; a
    // job that has been running for ten minutes is the one this bar exists to
    // reassure them about, and letting a newer, short-lived job bump it into
    // "(+N)" would defeat that.
    //
    // The two reinforce each other under `NAME_MAX`'s narrow-pane truncation:
    // Claude Code cuts this line from the right, so the leftmost slot is the
    // one that survives a narrow pane. Oldest-first puts the job most worth
    // keeping visible exactly there.
    live.sort_by_key(|r| r.started_at);

    let remaining = live.len().saturating_sub(NAMES);
    let shown: Vec<String> = live.iter().take(NAMES).map(|r| format_one(r)).collect();
    let tail = if remaining > 0 {
        format!("  (+{remaining})")
    } else {
        String::new()
    };
    format!(
        "▶ @{} {}{}",
        status::fmt_local_hm(now),
        shown.join(" · "),
        tail
    )
}

/// One shown job: `~` for a quiet child, the name capped to `NAME_MAX`, and its
/// running time. Nothing here reads `key` — `status.is_quiet()` decides the
/// marker off the typed enum instead of a second string check that could
/// drift from `Display` — and `name` is the one field `status::name` already
/// routed through `meta::escape_control` on its way into the record, so
/// nothing this function prints needs a second escape.
///
/// Deliberately silent about `stat_errors`: a capture whose file cannot be
/// stat'd reports zero bytes, so `derive`'s quiet anchor falls back to
/// `started_at`, and a child that is actually producing can render `~name`
/// here after 30s — the exact misreading `stat_errors` exists to forbid on
/// the other two surfaces (JSON's field, text's `[stat failed: ...]`
/// bracket). This surface does not carry it: there is no room for a fourth
/// signal in three fixed-width slots, a stat failure other than "not created
/// yet" is rare, and `agent-tools ps` is one command away for the reader who
/// needs to know why.
fn format_one(r: &Record) -> String {
    let prefix = if r.status.is_quiet() { "~" } else { "" };
    let name = status::cap_to(&r.name, NAME_MAX);
    // `Record::build` always populates `elapsed_s` for a non-terminal record
    // (see its own field doc); a hand-assembled `Record` need not. `"?"`
    // rather than a fallback number: a plausible wrong duration would read as
    // a real one, the same failure `NAME_MAX`'s own doc rejects for sizing
    // the line off a guessed `tput cols` width.
    let elapsed = match r.elapsed_s {
        Some(s) => status::fmt_duration(s),
        None => "?".to_string(),
    };
    format!("{prefix}{name} {elapsed}")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::status::StatusKey;
    use chrono::Duration;

    /// A `Record` built directly rather than through `Record::build`, so the
    /// formatting rules above can be driven without a filesystem or a real
    /// wrapper. `started_at` is derived from `elapsed` so records built with
    /// different elapsed values sort against each other exactly as same-aged
    /// real captures would. `key` is derived from `status` rather than taken
    /// as an independent parameter, so a fixture cannot set the two fields to
    /// disagree the way a hand-edited `meta.json` could.
    fn rec(name: &str, status: StatusKey, elapsed: f64) -> Record {
        let now = now_fixed();
        Record {
            name: name.to_string(),
            key: status.to_string(),
            status,
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
            // Always live, regardless of what a real `derive()` would say
            // about `status`: this fixture drives the formatting rules in
            // isolation, including combinations `derive()` itself could
            // never produce — see
            // `a_raw_key_cannot_split_the_bar_or_run_escape_codes`, which
            // needs a live record carrying a terminal-shaped key.
            terminal: false,
        }
    }

    #[test]
    fn nothing_running_prints_nothing() {
        assert_eq!(render_records(&[], now_fixed()), "");
    }

    #[test]
    fn a_line_stamps_itself_because_the_bar_does_not_tick() {
        let line = render_records(&[rec("build", StatusKey::Producing, 191.0)], now_fixed());
        assert!(line.starts_with("▶ @"), "{line}");
        assert!(line.contains("build 3m11s"), "{line}");
    }

    #[test]
    fn the_stamp_is_hour_and_minute_with_no_seconds() {
        let line = render_records(&[rec("build", StatusKey::Producing, 5.0)], now_fixed());
        let after_at = line
            .strip_prefix("▶ @")
            .unwrap_or_else(|| panic!("no stamp: {line}"));
        let end = after_at
            .find(' ')
            .unwrap_or_else(|| panic!("no space after the stamp: {line}"));
        let stamp = &after_at[..end];
        // `%H:%M` is five bytes: two digits, a colon, two digits. `%H:%M:%S`
        // is eight, with a second colon — the byte-class check below rejects
        // a same-length mistake the length check alone would miss. Neither
        // hardcodes a value, so this holds regardless of the host's zone.
        assert_eq!(
            stamp.len(),
            5,
            "the stamp must be HH:MM: {stamp:?} in {line}"
        );
        let b = stamp.as_bytes();
        assert!(
            b[0].is_ascii_digit()
                && b[1].is_ascii_digit()
                && b[2] == b':'
                && b[3].is_ascii_digit()
                && b[4].is_ascii_digit(),
            "the stamp must be HH:MM: {stamp:?} in {line}"
        );
    }

    #[test]
    fn a_quiet_child_is_marked() {
        let line = render_records(
            &[rec("deploy", StatusKey::Quiet("30s"), 724.0)],
            now_fixed(),
        );
        assert!(line.contains("~deploy 12m04s"), "{line}");
    }

    #[test]
    fn beyond_three_the_rest_are_counted() {
        let rs: Vec<_> = ["a", "b", "c", "d", "e"]
            .iter()
            .map(|n| rec(n, StatusKey::Producing, 61.0))
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
                StatusKey::Producing,
                61.0,
            )],
            now_fixed(),
        );
        // Pins the cut at exactly `NAME_MAX` (14): the 14 kept characters,
        // the ellipsis, and the space before the duration, together. A bare
        // length ceiling (or `contains('…')` alone) passes identically
        // whether the cap is 14 or 38; this does not.
        assert!(
            line.contains("an-extremely-l… "),
            "the name must be cut at exactly 14 characters: {line}"
        );
    }

    #[test]
    fn the_width_budget_holds_at_the_worst_case() {
        // Three shown slots, each a quiet child named past the cap and
        // running ten hours — the shape `NAME_MAX`'s own doc computes to 90
        // characters. Two more live children push the tail to "(+2)". This
        // is the test that actually pins `NAMES` and `NAME_MAX` together:
        // raising either enlarges every shown slot, or adds a fourth one,
        // and both grow the line past 90 — a tighter single-name length bound
        // cannot catch either, since neither mutation touches a one-record line.
        let rs: Vec<_> = ["a", "b", "c", "d", "e"]
            .iter()
            .map(|n| {
                rec(
                    &format!("{n}-{}", "x".repeat(20)),
                    StatusKey::Quiet("2h"),
                    36_000.0,
                )
            })
            .collect();
        let line = render_records(&rs, now_fixed());
        assert!(
            line.chars().count() <= 90,
            "{} chars: {line}",
            line.chars().count()
        );
    }

    #[test]
    fn the_oldest_job_leads_because_a_frozen_line_must_not_lose_it() {
        // Oldest first: the longest-running job is the one a person is most
        // likely to be worried about and the one this bar exists to reassure
        // them about. A job spawned seconds ago needs no such reminder, and
        // must not be allowed to bump an already-running job out to "(+N)".
        let old = rec("migrate", StatusKey::Producing, 600.0);
        let mid = rec("build", StatusKey::Producing, 300.0);
        let new = rec("probe", StatusKey::Producing, 5.0);
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
    fn a_record_with_no_elapsed_shows_a_question_mark_not_a_confident_zero() {
        let mut r = rec("build", StatusKey::Producing, 5.0);
        r.elapsed_s = None;
        let line = render_records(&[r], now_fixed());
        assert!(
            line.contains("build ?"),
            "an unknown duration must read as unknown, not as 0s: {line}"
        );
    }

    #[test]
    fn a_raw_key_cannot_split_the_bar_or_run_escape_codes() {
        // `key` is a JSON sink upstream (see `Record::key`'s own doc) and
        // arrives raw — unlike `name`, nothing before this renderer has
        // escaped it. A `spawn-failed` status carries the wrapper's own
        // `io::Error` text verbatim, which nothing constrains; simulate one
        // holding a newline and an ANSI escape. `status` stays `Producing` so
        // this stays a live, shown record — a real `SpawnFailed` is always
        // terminal and would simply never reach this renderer.
        let mut r = rec("deploy", StatusKey::Producing, 5.0);
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
