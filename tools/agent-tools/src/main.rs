use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

fn scripts_dir() -> PathBuf {
    // Resolve from binary location: walk up to find skills/scripts/.
    if let Ok(exe) = env::current_exe() {
        let mut dir = exe.as_path();
        while let Some(parent) = dir.parent() {
            let candidate = parent.join("skills/scripts");
            if candidate.is_dir() {
                return candidate;
            }
            dir = parent;
        }
    }

    // Fallback: ~/.claude/skills/scripts
    let home = env::var("HOME").expect("HOME not set");
    Path::new(&home).join(".claude/skills/scripts")
}

fn cmd_skill(args: &[String]) -> ! {
    if args.is_empty() {
        eprintln!("usage: agent-tools skill <module.entry> [args...]");
        eprintln!("  e.g. agent-tools skill do.do --step 1");
        std::process::exit(1);
    }

    let module = format!("skills.{}", &args[0]);
    let scripts = scripts_dir();

    let mut cmd = Command::new("python3");
    cmd.arg("-m").arg(&module);
    cmd.args(&args[1..]);
    cmd.current_dir(&scripts);

    let err = cmd.exec();
    eprintln!("agent-tools: exec python3 failed: {err}");
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
