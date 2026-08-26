use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut command = Command::new(bin());
    command.env("CLAUDE_CONFIG_ROOT", worktree_root());
    command
}

fn make_task(home: &std::path::Path) -> PathBuf {
    let dir = home.join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

#[test]
fn errors_when_env_not_set() {
    let home = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run", "--", "echo", "hi"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(!out.status.success());
    assert!(String::from_utf8_lossy(&out.stderr).contains("AGENT_TOOLS_PARENT_DIR"));
}

#[test]
fn captures_child_stdout_and_forwards() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--",
            "bash",
            "-c",
            "echo hello; echo bad 1>&2; exit 0",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "bad\n");

    let children: Vec<_> = std::fs::read_dir(&parent_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].path();
    // Capture path is <parent>/<pid>/ — NO `children/` segment.
    assert_eq!(child_dir.parent().unwrap(), parent_dir.as_path());
    assert!(child_dir.join("meta.json").exists());
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stdout")).unwrap(),
        "hello\n"
    );
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stderr")).unwrap(),
        "bad\n"
    );
}

#[test]
fn lazily_creates_parent_dir_when_missing() {
    let home = tempfile::tempdir().unwrap();
    // Point AGENT_TOOLS_PARENT_DIR at a path that does NOT yet exist.
    let parent_dir = home.path().join(".claude/agent-tools/sid/tuid-fresh");
    assert!(
        !parent_dir.exists(),
        "precondition: parent dir must not exist"
    );
    let out = agent_tools()
        .args(["run", "--", "bash", "-c", "echo lazy"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), "lazy\n");
    assert!(
        parent_dir.exists(),
        "run should have lazily created the parent dir"
    );
    let children: Vec<_> = std::fs::read_dir(&parent_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .collect();
    assert_eq!(children.len(), 1);
    let child_dir = children[0].path();
    assert_eq!(child_dir.parent().unwrap(), parent_dir.as_path());
    assert_eq!(
        std::fs::read_to_string(child_dir.join("stdout")).unwrap(),
        "lazy\n"
    );
}

#[test]
fn forwards_stdin_to_child() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    use std::io::Write;
    use std::process::Stdio;
    let mut c = agent_tools()
        .args(["run", "--", "cat"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(b"streamed\n").unwrap();
    drop(c.stdin.take());
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success());
    assert_eq!(String::from_utf8_lossy(&out.stdout), "streamed\n");
}

#[test]
fn propagates_exit_code() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args(["run", "--", "bash", "-c", "exit 7"])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(7));
}

#[test]
fn records_child_started_and_child_exit_in_parent_events() {
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--desc",
            "compute things",
            "--",
            "bash",
            "-c",
            "echo ok",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(out.status.success());
    let evts = std::fs::read_to_string(parent_dir.join("events.jsonl")).unwrap();

    // The payloads are what a reader reconstructs the run from, so pin their
    // whole shape: a field silently dropped from one of them is a fact lost,
    // and matching on the kind string alone would not notice.
    let events: Vec<serde_json::Value> = evts
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).expect("each line is one event"))
        .collect();
    let data_of = |kind: &str| -> serde_json::Value {
        events
            .iter()
            .find(|e| e["kind"] == kind)
            .unwrap_or_else(|| panic!("no {kind} event: {evts}"))["data"]
            .clone()
    };
    let field_names = |v: &serde_json::Value| -> Vec<String> {
        let obj = v.as_object().expect("data is an object");
        let mut names: Vec<String> = obj.keys().cloned().collect();
        names.sort();
        names
    };

    let started = data_of("child_started");
    let exited = data_of("child_exit");

    assert_eq!(
        field_names(&started),
        ["child_pid", "command", "desc", "wrapper_pid"]
    );
    assert_eq!(field_names(&exited), ["child_pid", "exit_code", "wrapper_pid"]);

    assert_eq!(started["desc"], "compute things");
    assert_eq!(started["command"], serde_json::json!(["bash", "-c", "echo ok"]));
    assert_eq!(exited["exit_code"], 0);

    // The exit must be attributable to the process that started: both events
    // name the same child and the same wrapper, and neither pid is null.
    assert!(started["child_pid"].as_u64().is_some(), "events: {evts}");
    assert!(started["wrapper_pid"].as_u64().is_some(), "events: {evts}");
    assert_eq!(exited["child_pid"], started["child_pid"]);
    assert_eq!(exited["wrapper_pid"], started["wrapper_pid"]);
}

// Default: --desc and full argv are visible in /proc/self/cmdline
// (clarity for general debugging). PR_SET_NAME/`comm` is set to a
// truncated hint so `ps -o comm=` still identifies the wrapper.
#[test]
fn default_leaves_argv_visible_and_sets_comm() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--desc",
            "compute-things",
            "--",
            "bash",
            "-c",
            "cat /proc/$PPID/cmdline; echo; echo COMM=$(cat /proc/$PPID/comm)",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let stdout = String::from_utf8_lossy(&out.stdout);
    // Default keeps the descriptive argv intact.
    assert!(
        stdout.contains("compute-things"),
        "default should leave --desc visible in /proc/self/cmdline: {stdout}"
    );
    assert!(
        stdout.contains("--desc"),
        "default should leave '--desc' visible in /proc/self/cmdline: {stdout}"
    );
    // comm slot is set to a hint derived from desc (15-byte cap).
    assert!(
        stdout.contains("COMM=at:compute-thin"),
        "expected comm slot set from --desc hint: {stdout}"
    );
}

// Round-19 F88 regression guard for the opt-in path: with
// `--hide-cmdline`, `--desc` and the wrapped command line must NOT
// appear in /proc/self/cmdline while the wrapper runs. Used for
// probe / contamination-sensitive work.
#[test]
fn hide_cmdline_hides_desc_and_argv_from_proc_self_cmdline() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let home = tempfile::tempdir().unwrap();
    let parent_dir = make_task(home.path());
    let out = agent_tools()
        .args([
            "run",
            "--hide-cmdline",
            "--desc",
            "F88-SECRET-CANARY-STRING",
            "--",
            "bash",
            "-c",
            "cat /proc/$PPID/cmdline; echo; echo 'ARGS='; ps -o args= -p $PPID",
        ])
        .env("HOME", home.path())
        .env("AGENT_TOOLS_PARENT_DIR", &parent_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        !stdout.contains("F88-SECRET-CANARY-STRING"),
        "--desc leaked into /proc/self/cmdline under --hide-cmdline: {stdout}"
    );
    assert!(
        !stdout.contains("--desc"),
        "'--desc' argv token leaked into /proc/self/cmdline under --hide-cmdline: {stdout}"
    );
    // meta.json (the intended observability channel) still records the desc.
    let child_dirs: Vec<_> = std::fs::read_dir(&parent_dir)
        .unwrap()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().map(|t| t.is_dir()).unwrap_or(false))
        .collect();
    let meta = child_dirs
        .iter()
        .find_map(|d| std::fs::read_to_string(d.path().join("meta.json")).ok())
        .expect("expected a child meta.json");
    assert!(
        meta.contains("F88-SECRET-CANARY-STRING"),
        "desc must remain in meta.json (the intended observability channel): {meta}"
    );
}
