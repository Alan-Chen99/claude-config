//! Which checkout a binary is allowed to act for.
//!
//! `agent-tools` refuses to run when its compiled root is not the root the
//! active Claude Code config points at, unless `CLAUDE_CONFIG_ROOT` asserts the
//! mismatch is intended. The config in question is the one Claude Code is
//! actually reading: `CLAUDE_CONFIG_DIR` relocates every config read, so a
//! session launched against one checkout must be served by that checkout's
//! binary and no other.
//!
//! `ps --session-id` is the probe throughout. It resolves the root and then
//! needs nothing else from the environment — a bare `ps` would fail for the
//! unrelated reason that `AGENT_TOOLS_PARENT_DIR` is absent outside a Claude
//! Code Bash call, which would make a passing test indistinguishable from one
//! that never reached the root check.

use std::fs;
use std::os::unix::fs::symlink;
use std::path::{Path, PathBuf};
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// The checkout this test binary was compiled from — the only root it may act for.
fn compiled_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ has a parent")
        .to_path_buf()
}

/// A config directory whose `skills` link names `root`, the shape
/// `installed_default_root` reads.
fn config_dir_naming(parent: &Path, name: &str, root: &Path) -> PathBuf {
    let dir = parent.join(name);
    fs::create_dir_all(&dir).unwrap();
    symlink(root.join("skills"), dir.join("skills")).unwrap();
    dir
}

/// A checkout that is not this one. Only the directory has to exist: the root is
/// read from the link target's parent, so the `skills` entry itself need not.
fn other_root(parent: &Path) -> PathBuf {
    let root = parent.join("some-other-checkout");
    fs::create_dir_all(&root).unwrap();
    root
}

fn probe(home: &Path, config_dir: Option<&Path>) -> std::process::Output {
    let mut cmd = Command::new(bin());
    cmd.args(["ps", "--session-id", "root-check"])
        .env("HOME", home)
        .env_remove("CLAUDE_CONFIG_ROOT")
        .env_remove("CLAUDE_CONFIG_DIR");
    if let Some(dir) = config_dir {
        cmd.env("CLAUDE_CONFIG_DIR", dir);
    }
    cmd.output().unwrap()
}

/// The case the assertion exists for: a session is configured against one
/// checkout and a binary belonging to a different one is invoked inside it.
/// Resolving the root from `$HOME/.claude` instead lets that binary serve the
/// session without a word, which is the silent wrong-checkout result.
#[test]
fn a_binary_from_another_checkout_is_refused_inside_a_relocated_config() {
    let tmp = tempfile::tempdir().unwrap();
    // $HOME agrees with this binary, so only CLAUDE_CONFIG_DIR can refuse it.
    let home = tmp.path().join("home");
    config_dir_naming(&home, ".claude", &compiled_root());
    let elsewhere = other_root(tmp.path());
    let cfg = config_dir_naming(tmp.path(), "session-config", &elsewhere);

    let out = probe(&home, Some(&cfg));
    let stderr = String::from_utf8_lossy(&out.stderr);

    assert_eq!(
        out.status.code(),
        Some(2),
        "expected refusal, got status {:?}\nstdout: {}\nstderr: {stderr}",
        out.status.code(),
        String::from_utf8_lossy(&out.stdout)
    );
    assert!(
        stderr.contains(&elsewhere.canonicalize().unwrap().display().to_string()),
        "refusal names the root the session is configured for: {stderr}"
    );
}

/// The mirror image: the binary matching the session's config is admitted even
/// though `$HOME/.claude` names a different checkout entirely. Together with the
/// test above this pins the relocated config as the authority rather than one of
/// two sources that happen to agree.
#[test]
fn the_binary_matching_a_relocated_config_is_admitted() {
    let tmp = tempfile::tempdir().unwrap();
    let home = tmp.path().join("home");
    config_dir_naming(&home, ".claude", &other_root(tmp.path()));
    let cfg = config_dir_naming(tmp.path(), "session-config", &compiled_root());

    let out = probe(&home, Some(&cfg));
    assert!(
        out.status.success(),
        "expected admission, got status {:?}\nstderr: {}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
}

/// With no relocation the config directory is `$HOME/.claude`, unchanged.
#[test]
fn home_still_names_the_config_when_nothing_relocates_it() {
    let tmp = tempfile::tempdir().unwrap();
    let home = tmp.path().join("home");
    config_dir_naming(&home, ".claude", &compiled_root());
    assert!(probe(&home, None).status.success());

    let tmp2 = tempfile::tempdir().unwrap();
    let home2 = tmp2.path().join("home");
    config_dir_naming(&home2, ".claude", &other_root(tmp2.path()));
    assert_eq!(probe(&home2, None).status.code(), Some(2));
}

/// An empty value is not a relocation, so the fallback still applies rather than
/// the root being read from a directory named by the empty string.
#[test]
fn an_empty_relocation_falls_back_to_home() {
    let tmp = tempfile::tempdir().unwrap();
    let home = tmp.path().join("home");
    config_dir_naming(&home, ".claude", &compiled_root());

    let out = Command::new(bin())
        .args(["ps", "--session-id", "root-check"])
        .env("HOME", &home)
        .env_remove("CLAUDE_CONFIG_ROOT")
        .env("CLAUDE_CONFIG_DIR", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "empty CLAUDE_CONFIG_DIR falls back to $HOME/.claude: {}",
        String::from_utf8_lossy(&out.stderr)
    );
}

/// `CLAUDE_CONFIG_ROOT` asserts against the binary, so it still overrides a
/// relocated config that disagrees — and still refuses a value that is not this
/// checkout.
#[test]
fn the_explicit_assertion_outranks_a_relocated_config() {
    let tmp = tempfile::tempdir().unwrap();
    let home = tmp.path().join("home");
    config_dir_naming(&home, ".claude", &other_root(tmp.path()));
    let cfg = config_dir_naming(tmp.path(), "session-config", &other_root(tmp.path()));

    let admitted = Command::new(bin())
        .args(["ps", "--session-id", "root-check"])
        .env("HOME", &home)
        .env("CLAUDE_CONFIG_DIR", &cfg)
        .env("CLAUDE_CONFIG_ROOT", compiled_root())
        .output()
        .unwrap();
    assert!(
        admitted.status.success(),
        "explicit assertion admits its own checkout: {}",
        String::from_utf8_lossy(&admitted.stderr)
    );

    let refused = Command::new(bin())
        .args(["ps", "--session-id", "root-check"])
        .env("HOME", &home)
        .env("CLAUDE_CONFIG_DIR", &cfg)
        .env("CLAUDE_CONFIG_ROOT", other_root(tmp.path()))
        .output()
        .unwrap();
    assert_eq!(refused.status.code(), Some(2));
}

/// One directory reachable under two names is one root. Path strings cannot say
/// so; the check is on directory identity.
#[test]
fn one_directory_under_two_names_is_one_root() {
    let tmp = tempfile::tempdir().unwrap();
    let home = tmp.path().join("home");
    // A symlinked path to this checkout spells the root differently while
    // naming the same directory.
    let alias = tmp.path().join("alias");
    symlink(compiled_root(), &alias).unwrap();
    config_dir_naming(&home, ".claude", &compiled_root());

    let out = Command::new(bin())
        .args(["ps", "--session-id", "root-check"])
        .env("HOME", &home)
        .env_remove("CLAUDE_CONFIG_DIR")
        .env("CLAUDE_CONFIG_ROOT", &alias)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "a second name for this checkout is accepted: {}",
        String::from_utf8_lossy(&out.stderr)
    );
}
