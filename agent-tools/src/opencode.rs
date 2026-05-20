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

pub fn run(root: &Path, args: &[String]) -> ! {
    let env_file = parse_env_file(&root.join(".env"));
    let mut cmd = Command::new("opencode");

    for (source, target) in LANGFUSE_ENV {
        if let Some(value) = env_file.get(source) {
            cmd.env(target, value);
        } else if let Ok(value) = std::env::var(source) {
            cmd.env(target, value);
        }
    }

    cmd.args(args);
    let err = cmd.exec();
    eprintln!("agent-tools opencode: exec opencode failed: {err}");
    std::process::exit(1);
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
