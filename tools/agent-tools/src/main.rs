use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

fn repo_root() -> PathBuf {
    // Walk up from binary location to find pyproject.toml (project root).
    if let Ok(exe) = env::current_exe() {
        let mut dir = exe.as_path();
        while let Some(parent) = dir.parent() {
            if parent.join("pyproject.toml").is_file() && parent.join("skills/scripts").is_dir() {
                return parent.to_path_buf();
            }
            dir = parent;
        }
    }

    // Fallback: ~/.claude
    let home = env::var("HOME").expect("HOME not set");
    Path::new(&home).join(".claude")
}

fn cmd_skill(args: &[String]) -> ! {
    if args.is_empty() {
        eprintln!("usage: agent-tools skill <module.entry> [args...]");
        eprintln!("  e.g. agent-tools skill do.do --step 1");
        std::process::exit(1);
    }

    let module = format!("skills.{}", &args[0]);
    let root = repo_root();

    let mut cmd = Command::new("uv");
    cmd.arg("run");
    cmd.arg("--project").arg(&root);
    cmd.arg("python3").arg("-m").arg(&module);
    cmd.args(&args[1..]);
    cmd.current_dir(root.join("skills/scripts"));

    let err = cmd.exec();
    eprintln!("agent-tools: exec uv failed: {err}");
    std::process::exit(1);
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();

    if args.is_empty() {
        eprintln!("usage: agent-tools <command> [args...]");
        eprintln!("commands: skill");
        std::process::exit(1);
    }

    match args[0].as_str() {
        "skill" => cmd_skill(&args[1..]),
        other => {
            eprintln!("agent-tools: unknown command '{other}'");
            eprintln!("commands: skill");
            std::process::exit(1);
        }
    }
}
