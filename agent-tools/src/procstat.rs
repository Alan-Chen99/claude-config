use anyhow::{Context, Result};
use std::fs;

/// Parse `/proc/<pid>/stat` into (state, starttime_ticks).
///
/// Field 2 is `comm` wrapped in parentheses and may contain spaces and
/// parentheses, so parsing anchors on the last `)`. In the remainder, index 0
/// is field 3 (state) and index 19 is field 22 (starttime, clock ticks since
/// boot). Verified against /proc/uptime: a freshly started process reports
/// uptime x CLK_TCK.
pub fn parse_stat(line: &str) -> Result<(u8, u64)> {
    let (_, tail) = line.rsplit_once(')').context("no ')' in stat line")?;
    let mut it = tail.split_whitespace();
    let state = it.next().context("stat: no state field")?;
    let starttime = it
        .nth(18)
        .context("stat: line too short for starttime")?
        .parse::<u64>()
        .context("stat: starttime not an integer")?;
    // split_whitespace never yields an empty token, so the first byte exists.
    Ok((state.as_bytes()[0], starttime))
}

pub fn start_ticks(pid: u32) -> Result<u64> {
    let raw = fs::read_to_string(format!("/proc/{pid}/stat"))
        .with_context(|| format!("read /proc/{pid}/stat"))?;
    Ok(parse_stat(&raw)?.1)
}

/// True iff `pid` exists, was started at `expected_ticks`, and is not a zombie.
///
/// The start-ticks comparison rejects a recycled pid. A zombie wrapper has
/// already released its pipe fds, so it must not count as alive.
pub fn is_alive(pid: u32, expected_ticks: u64) -> bool {
    let Ok(raw) = fs::read_to_string(format!("/proc/{pid}/stat")) else {
        return false;
    };
    match parse_stat(&raw) {
        Ok((state, ticks)) => ticks == expected_ticks && state != b'Z',
        Err(_) => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_own_start_ticks_and_matches_liveness() {
        let me = std::process::id();
        let ticks = start_ticks(me).expect("own start ticks readable");
        assert!(ticks > 0);
        assert!(is_alive(me, ticks), "self must be alive with its own ticks");
    }

    #[test]
    fn wrong_start_ticks_reads_as_dead() {
        let me = std::process::id();
        let ticks = start_ticks(me).unwrap();
        assert!(
            !is_alive(me, ticks + 1),
            "a recycled pid with different start ticks must read as dead"
        );
    }

    #[test]
    fn comm_containing_spaces_and_parens_parses() {
        // Field 2 is `(comm)` and may itself contain ') ' sequences; parsing
        // must anchor on the LAST ')'.
        let line = "1234 (weird ) name) S 1 1234 1234 0 -1 4194560 100 0 0 0 \
                    1 2 3 4 20 0 1 0 987654 1000 100 0 0 0 0 0 0 0 0 0 0 0 0 0 0";
        assert_eq!(parse_stat(line).unwrap(), (b'S', 987654));
    }

    #[test]
    fn dead_pid_reads_as_dead() {
        // pid 0 never has a /proc entry.
        assert!(!is_alive(0, 1));
    }

    #[test]
    fn a_zombie_is_not_alive() {
        // An exited-but-unreaped child keeps its pid and its start ticks, so
        // ticks alone cannot distinguish it from a live process. It has
        // already released its pipe fds, so it must not count as alive.
        let mut child = std::process::Command::new("true").spawn().unwrap();
        let pid = child.id();
        let ticks = start_ticks(pid).unwrap();
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
        loop {
            let raw = std::fs::read_to_string(format!("/proc/{pid}/stat")).unwrap();
            if parse_stat(&raw).unwrap().0 == b'Z' {
                break;
            }
            assert!(std::time::Instant::now() < deadline, "child never became a zombie");
            std::thread::sleep(std::time::Duration::from_millis(10));
        }
        assert!(!is_alive(pid, ticks), "a zombie must not count as alive");
        child.wait().unwrap();
    }
}
