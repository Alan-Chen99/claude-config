use anyhow::{bail, Context, Result};
use nix::fcntl::{Flock, FlockArg};
use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};

/// Scopes with a live `Ledger` in this process.
///
/// `flock` keys off the open file description, not the process, so a second
/// `open` on a scope this process already holds blocks forever waiting on its
/// own lock — with no diagnostic, and nothing able to release it. The set turns
/// that hang into an error.
fn open_scopes() -> &'static Mutex<HashSet<PathBuf>> {
    static SCOPES: OnceLock<Mutex<HashSet<PathBuf>>> = OnceLock::new();
    SCOPES.get_or_init(|| Mutex::new(HashSet::new()))
}

/// The stored map, plus the reason it could not be read.
///
/// A missing file is ordinary: nothing has been reported in this scope yet.
/// Anything else means the record of what the agent was already told is gone.
/// The agent has to hear about that, because the consequence is every child
/// being reported to it a second time.
fn load(path: &Path) -> (BTreeMap<String, String>, Option<String>) {
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return (BTreeMap::new(), None),
        Err(e) => {
            return (
                BTreeMap::new(),
                Some(format!("{} could not be read ({e})", path.display())),
            )
        }
    };
    match serde_json::from_slice(&bytes) {
        Ok(m) => (m, None),
        Err(e) => (
            BTreeMap::new(),
            Some(format!("{} is unreadable ({e})", path.display())),
        ),
    }
}

/// Per-scope map of child identity -> last reported status key.
///
/// Child identity is the capture directory's path relative to the scope:
/// `<tool_use_id>/<wrapper_pid>`. The exclusive flock is held for the lifetime
/// of the value, so a scan-and-report cycle is atomic against parallel hooks.
#[derive(Debug)]
pub struct Ledger {
    scope: PathBuf,
    path: PathBuf,
    map: BTreeMap<String, String>,
    /// Set when the stored ledger could not be read. Everything in this scope
    /// will look new, so the report says why rather than letting the agent see
    /// unexplained repeats.
    pub reset_reason: Option<String>,
    _lock: Flock<fs::File>,
}

impl Drop for Ledger {
    fn drop(&mut self) {
        open_scopes().lock().unwrap().remove(&self.scope);
    }
}

impl Ledger {
    pub fn open(scope: &Path) -> Result<Self> {
        fs::create_dir_all(scope)
            .with_context(|| format!("create scope dir {}", scope.display()))?;
        let scope = fs::canonicalize(scope)
            .with_context(|| format!("canonicalize {}", scope.display()))?;
        if !open_scopes().lock().unwrap().insert(scope.clone()) {
            bail!(
                "a Ledger for {} is already open in this process; a second one would \
                 block forever waiting on this process's own flock",
                scope.display()
            );
        }
        match Self::acquire(scope.clone()) {
            Ok(l) => Ok(l),
            Err(e) => {
                open_scopes().lock().unwrap().remove(&scope);
                Err(e)
            }
        }
    }

    fn acquire(scope: PathBuf) -> Result<Self> {
        let lock_path = scope.join(".reported.lock");
        let file = fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(&lock_path)
            .with_context(|| format!("open lock {}", lock_path.display()))?;
        let lock = Flock::lock(file, FlockArg::LockExclusive)
            .map_err(|(_, e)| anyhow::anyhow!("flock {}: {e}", lock_path.display()))?;
        let path = scope.join(".reported.json");
        let (map, reset_reason) = load(&path);
        Ok(Ledger { scope, path, map, reset_reason, _lock: lock })
    }

    /// True when `key` differs from the last key reported for `id`.
    ///
    /// A pure query. Nothing is recorded until `record` is called, so a line the
    /// caller ends up dropping stays pending rather than being marked as told.
    pub fn changed(&self, id: &str, key: &str) -> bool {
        self.map.get(id).map(|prev| prev != key).unwrap_or(true)
    }

    /// Record `key` as the last key reported for `id`. Call this only for lines
    /// that actually reach the agent.
    pub fn record(&mut self, id: &str, key: &str) {
        self.map.insert(id.to_string(), key.to_string());
    }

    /// Takes `&mut self` so two threads sharing one open `Ledger` cannot race
    /// the fixed temp filename. The flock excludes other processes; it does
    /// nothing to serialize callers already holding this file description.
    pub fn commit(&mut self) -> Result<()> {
        let tmp = self.path.with_extension("json.tmp");
        fs::write(&tmp, serde_json::to_vec_pretty(&self.map)?)
            .with_context(|| format!("write {}", tmp.display()))?;
        fs::rename(&tmp, &self.path)
            .with_context(|| format!("rename into {}", self.path.display()))?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn first_sight_of_a_key_is_a_change() {
        let scope = TempDir::new().unwrap();
        let mut l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "producing"));
        l.record("toolu_a/12", "producing");
        l.commit().unwrap();
    }

    #[test]
    fn same_key_twice_is_not_a_change() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "producing");
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(!l.changed("toolu_a/12", "producing"));
    }

    #[test]
    fn a_new_key_for_a_known_child_is_a_change() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "exited(0)");
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "final(0)"));
    }

    #[test]
    fn children_are_tracked_independently() {
        let scope = TempDir::new().unwrap();
        let mut l = Ledger::open(scope.path()).unwrap();
        assert!(l.changed("toolu_a/12", "producing"));
        l.record("toolu_a/12", "producing");
        assert!(l.changed("toolu_b/99", "producing"));
    }

    #[test]
    fn a_second_open_in_this_process_fails_fast_instead_of_hanging() {
        let scope = TempDir::new().unwrap();
        let _first = Ledger::open(scope.path()).unwrap();
        let err = Ledger::open(scope.path()).unwrap_err().to_string();
        assert!(err.contains("already open in this process"), "err: {err}");
    }

    #[test]
    fn a_corrupt_ledger_announces_itself_rather_than_resetting_quietly() {
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            l.record("toolu_a/12", "producing");
            l.commit().unwrap();
        }
        std::fs::write(scope.path().join(".reported.json"), b"{not json").unwrap();
        let l = Ledger::open(scope.path()).unwrap();
        assert!(l.reset_reason.is_some(), "a corrupt ledger must say so");
        assert!(
            l.changed("toolu_a/12", "producing"),
            "the record really is gone, so the child reports again"
        );
    }

    #[test]
    fn a_key_that_was_never_recorded_stays_pending() {
        // A caller that drops a line for size must not have it counted as told,
        // or that child's change is lost from the push channel permanently.
        let scope = TempDir::new().unwrap();
        {
            let mut l = Ledger::open(scope.path()).unwrap();
            assert!(l.changed("toolu_a/12", "producing"));
            l.commit().unwrap();
        }
        let l = Ledger::open(scope.path()).unwrap();
        assert!(
            l.changed("toolu_a/12", "producing"),
            "an unreported key must not count as told"
        );
    }
}
