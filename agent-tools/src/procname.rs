//! Two knobs on the wrapper's identity as seen by peer processes.
//!
//! `set_comm(hint)` — default. Sets the kernel `comm` slot
//! (`prctl(PR_SET_NAME)`, `/proc/*/comm`, `ps -o comm=`) to a helpful
//! 15-byte fragment derived from the caller's `--desc` or the wrapped
//! command. Argv (`/proc/*/cmdline`, `ps aux`, `ps -o args=`) is left
//! untouched — clarity is more useful than privacy for general debugging.
//!
//! `hide_cmdline(title)` — opt-in via `--hide-cmdline`. Zeros the argv
//! memory region and writes `title` at its start, so peer processes
//! reading `ps aux` or `/proc/*/cmdline` cannot recover the `--desc`
//! string or the full command line from the wrapper; the wrapped child is
//! its own process, whose argv still shows the command. Also sets `comm`
//! to match.
//!
//! Round-19 F88 named the leak the hide path addresses: `agent-tools
//! run --desc "E-k3-v8: Kimi K3 + v8 + H17"` argv was visible via
//! `/proc/*/cmdline`, and a test-agent quoted it back verbatim. That
//! matters for probe/contamination-sensitive work. It does not matter
//! for normal use, so the hide is opt-in.
//!
//! Mechanism (hide path): `/proc/self/stat` fields 48 (`arg_start`)
//! and 49 (`arg_end`) record the exact virtual-memory range the kernel
//! serves as `/proc/self/cmdline`. That range lives in the caller's
//! own address space, so a byte-level rewrite is a plain in-process
//! store. No `prctl(PR_SET_MM, ...)` or CAP_SYS_RESOURCE required.
//! `PR_SET_NAME` is a separate 16-byte "comm" slot and does not
//! affect cmdline; setting it is bonus consistency.

use std::fs;

/// The longest prefix of `name` that the kernel's 15-byte `comm` slot
/// (`TASK_COMM_LEN - 1`) holds whole. prctl cuts at 15 bytes without regard
/// for character boundaries, and a half character is invalid UTF-8 to every
/// strict reader of `/proc/<pid>/comm` and `/proc/<pid>/stat`.
fn comm_for(name: &str) -> &str {
    &name[..name.floor_char_boundary(15)]
}

/// Set the kernel `comm` slot (`ps -o comm=`) to a truncated form of
/// `hint`. Cheap identifier for debugging; does NOT hide the argv.
///
/// Result is prefixed with `at:` (short for `agent-tools`) so
/// `ps -o comm=` distinguishes the wrapper from an inline invocation
/// while still leaving 12 bytes for the hint.
pub fn set_comm(hint: &str) {
    if !cfg!(target_os = "linux") {
        return;
    }
    let c_short = match std::ffi::CString::new(comm_for(&format!("at:{hint}"))) {
        Ok(v) => v,
        Err(_) => return,
    };
    // SAFETY: prctl(PR_SET_NAME, ptr, 0, 0, 0) reads up to 16 bytes from
    // ptr including the trailing NUL; we hold `c_short` alive across the
    // call.
    unsafe {
        libc::prctl(libc::PR_SET_NAME, c_short.as_ptr(), 0, 0, 0);
    }
}

/// Zero out the argv memory region and write `title` at its start.
///
/// Silently no-ops on non-Linux platforms or if the memory range
/// cannot be resolved from `/proc/self/stat`. Intended for
/// contamination hardening; the caller must not rely on the effect
/// having taken place.
pub fn hide_cmdline(title: &str) {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (start, size) = match argv_range() {
        Some(range) => range,
        None => return,
    };
    if size == 0 {
        return;
    }
    // SAFETY: `start` and `start + size` bound a virtual-memory range
    // the kernel itself hands to /proc/self/cmdline; it belongs to the
    // current process and is writable (argv is placed on the initial
    // stack). We are the sole owner of these bytes at this point in
    // execution — clap has already parsed argv into owned Strings.
    unsafe {
        let ptr = start as *mut u8;
        std::ptr::write_bytes(ptr, 0, size);
        let bytes = title.as_bytes();
        let n = bytes.len().min(size.saturating_sub(1));
        std::ptr::copy_nonoverlapping(bytes.as_ptr(), ptr, n);
    }
    // Match comm to the visible title, so `ps -o comm=` agrees with
    // `ps -o args=`.
    let c_short = std::ffi::CString::new(comm_for(title)).unwrap_or_default();
    unsafe {
        libc::prctl(libc::PR_SET_NAME, c_short.as_ptr(), 0, 0, 0);
    }
}

/// Return `(arg_start, arg_end - arg_start)` from /proc/self/stat, or None
/// if the file layout is unexpected. See proc(5): the fields are 1-indexed
/// including `pid` (field 1) and `comm` (field 2, wrapped in parentheses,
/// may itself contain whitespace and parens). `arg_start` is field 48,
/// `arg_end` is field 49. Splitting on the last `')'` skips comm safely.
fn argv_range() -> Option<(usize, usize)> {
    let stat = fs::read_to_string("/proc/self/stat").ok()?;
    let close = stat.rfind(')')?;
    let rest = &stat[close + 1..];
    let fields: Vec<&str> = rest.split_whitespace().collect();
    // After ')' the first field is `state` (field 3). `arg_start` is field
    // 48 → 0-indexed position 45 in `fields`. `arg_end` is at 46.
    if fields.len() < 47 {
        return None;
    }
    let arg_start: u64 = fields[45].parse().ok()?;
    let arg_end: u64 = fields[46].parse().ok()?;
    if arg_end < arg_start {
        return None;
    }
    Some((arg_start as usize, (arg_end - arg_start) as usize))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The kernel truncates `comm` at 15 bytes. A name whose character
    /// straddles that boundary must be cut before the character, not through
    /// it, and no earlier. Both callers' prefixes are ASCII, so the padding
    /// walks every multi-byte tail across every offset of the limit.
    #[test]
    fn comm_never_straddles_the_kernel_limit() {
        for prefix in ["at:", "agent-tools: "] {
            for n in 0..20 {
                for tail in ["鍵盘 driver", "✅ tail", "école", "😀 x"] {
                    let name = format!("{prefix}{}{tail}", "x".repeat(n));
                    let s = comm_for(&name);
                    assert!(
                        s.len() <= 15,
                        "comm_for({name:?}) = {s:?} is {} bytes, kernel keeps 15",
                        s.len()
                    );
                    let next = name[s.len()..].chars().next();
                    assert!(
                        next.is_none_or(|c| s.len() + c.len_utf8() > 15),
                        "comm_for({name:?}) = {s:?} stops before {next:?}, which fits"
                    );
                }
            }
        }
    }
}
