use std::collections::HashMap;
use std::fs;
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::Command;

const LANGFUSE_ENV: [(&str, &str); 3] = [
    ("OPENCODE_LANGFUSE_SECRET_KEY", "LANGFUSE_SECRET_KEY"),
    ("OPENCODE_LANGFUSE_PUBLIC_KEY", "LANGFUSE_PUBLIC_KEY"),
    ("OPENCODE_LANGFUSE_BASE_URL", "LANGFUSE_BASEURL"),
];

const GIT_AUTHOR_NAME: &str = "opencode";
const GIT_AUTHOR_EMAIL: &str = "opencode@users.noreply.github.com";

pub fn run(root: &Path, args: &[String]) -> ! {
    let mut cmd = Command::new("opencode");

    for (target, value) in langfuse_env(&root.join(".env"), |key| std::env::var(key).ok()) {
        cmd.env(target, value);
    }

    cmd.env("GIT_AUTHOR_NAME", GIT_AUTHOR_NAME);
    cmd.env("GIT_AUTHOR_EMAIL", GIT_AUTHOR_EMAIL);
    cmd.env("GIT_COMMITTER_NAME", GIT_AUTHOR_NAME);
    cmd.env("GIT_COMMITTER_EMAIL", GIT_AUTHOR_EMAIL);

    cmd.args(args);
    let err = cmd.exec();
    eprintln!("agent-tools opencode: exec opencode failed: {err}");
    std::process::exit(1);
}

/// The plugin variables opencode should see, under the prefixed names that
/// carry them.
///
/// The repo `.env` is authoritative: `src/claude_config/config.py` loads the
/// same file with `override=True`, and the `OPENCODE_` prefix exists so repo
/// config stays distinguishable from whatever the shell already holds. The
/// process environment is the fallback for a checkout with no `.env` — the
/// file is gitignored, so a worktree has none.
fn langfuse_env(
    env_path: &Path,
    from_process: impl Fn(&str) -> Option<String>,
) -> Vec<(&'static str, String)> {
    let env_file = parse_env_file(env_path);

    LANGFUSE_ENV
        .iter()
        .filter_map(|(source, target)| {
            let value = env_file
                .get(*source)
                .cloned()
                .or_else(|| from_process(source))?;
            Some((*target, value))
        })
        .collect()
}

fn parse_env_file(path: &Path) -> HashMap<String, String> {
    let Ok(contents) = fs::read_to_string(path) else {
        return HashMap::new();
    };

    contents
        .lines()
        .filter_map(parse_env_line)
        .collect::<HashMap<_, _>>()
}

fn parse_env_line(line: &str) -> Option<(String, String)> {
    let line = line.trim();
    if line.is_empty() || line.starts_with('#') {
        return None;
    }

    let (key, value) = line.split_once('=')?;
    let key = key.trim();
    if key.is_empty() {
        return None;
    }

    Some((key.to_string(), unquote(value.trim()).to_string()))
}

fn unquote(value: &str) -> &str {
    if value.len() >= 2 {
        let bytes = value.as_bytes();
        if (bytes[0] == b'"' && bytes[value.len() - 1] == b'"')
            || (bytes[0] == b'\'' && bytes[value.len() - 1] == b'\'')
        {
            return &value[1..value.len() - 1];
        }
    }

    value
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn mapped(
        env_path: &Path,
        from_process: impl Fn(&str) -> Option<String>,
    ) -> HashMap<&'static str, String> {
        langfuse_env(env_path, from_process).into_iter().collect()
    }

    fn nothing(_: &str) -> Option<String> {
        None
    }

    #[test]
    fn an_env_file_value_wins_over_the_process_environment() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join(".env");
        fs::write(&path, "OPENCODE_LANGFUSE_SECRET_KEY=from file\n").unwrap();

        let m = mapped(&path, |_| Some("from process".to_string()));

        assert_eq!(
            m.get("LANGFUSE_SECRET_KEY").map(String::as_str),
            Some("from file")
        );
    }

    #[test]
    fn the_process_environment_supplies_a_key_the_env_file_omits() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join(".env");
        fs::write(&path, "OPENCODE_LANGFUSE_SECRET_KEY=from file\n").unwrap();

        let m = mapped(&path, |key| {
            (key == "OPENCODE_LANGFUSE_PUBLIC_KEY").then(|| "from process".to_string())
        });

        assert_eq!(
            m.get("LANGFUSE_PUBLIC_KEY").map(String::as_str),
            Some("from process")
        );
    }

    #[test]
    fn a_missing_env_file_leaves_every_key_to_the_process_environment() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("absent.env");

        let m = mapped(&path, |_| Some("from process".to_string()));

        assert_eq!(
            m.get("LANGFUSE_SECRET_KEY").map(String::as_str),
            Some("from process")
        );
        assert_eq!(
            m.get("LANGFUSE_PUBLIC_KEY").map(String::as_str),
            Some("from process")
        );
        assert_eq!(
            m.get("LANGFUSE_BASEURL").map(String::as_str),
            Some("from process")
        );
    }

    #[test]
    fn a_quoted_env_file_value_is_carried_without_its_quotes() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join(".env");
        fs::write(
            &path,
            "OPENCODE_LANGFUSE_BASE_URL=\"https://langfuse.example\"\n",
        )
        .unwrap();

        let m = mapped(&path, nothing);

        assert_eq!(
            m.get("LANGFUSE_BASEURL").map(String::as_str),
            Some("https://langfuse.example")
        );
    }

    #[test]
    fn a_key_absent_from_both_sources_is_not_carried() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join(".env");
        fs::write(&path, "OPENCODE_LANGFUSE_SECRET_KEY=from file\n").unwrap();

        let m = mapped(&path, nothing);

        assert_eq!(m.get("LANGFUSE_PUBLIC_KEY"), None);
        assert_eq!(m.get("LANGFUSE_BASEURL"), None);
    }
}
