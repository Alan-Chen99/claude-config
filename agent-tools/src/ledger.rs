use anyhow::{Context, Result};
use nix::fcntl::{Flock, FlockArg};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

/// Per-scope map of child identity -> last reported status key.
///
/// Child identity is the capture directory's path relative to the scope:
/// `<tool_use_id>/<wrapper_pid>`. The exclusive flock is held for the lifetime
/// of the value, so a scan-and-report cycle is atomic against parallel hooks.
pub struct Ledger {
    path: PathBuf,
    map: BTreeMap<String, String>,
    _lock: Flock<fs::File>,
}

impl Ledger {
    pub fn open(scope: &Path) -> Result<Self> {
        fs::create_dir_all(scope).ok();
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
        let map = fs::read(&path)
            .ok()
            .and_then(|b| serde_json::from_slice(&b).ok())
            .unwrap_or_default();
        Ok(Ledger { path, map, _lock: lock })
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

    pub fn commit(&self) -> Result<()> {
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
    fn a_key_that_was_never_recorded_stays_pending() {
        // A caller that drops a line for size must not have it counted as told,
        // or that child's change is lost from the push channel permanently.
        let scope = TempDir::new().unwrap();
        {
            let l = Ledger::open(scope.path()).unwrap();
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
