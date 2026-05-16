use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "agent-tools")]
struct Cli {
    #[command(subcommand)]
    command: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Run a skill script: agent-tools skill <module.entry> [args...]
    Skill {
        /// Python module path (e.g. do.do, alan_coding_style.coding_style)
        module: String,
        /// Arguments forwarded to the skill script
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Pretty-print a Claude Code JSONL session log
    CcPretty {
        /// Arguments forwarded to cc-pretty.py
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
}

fn repo_root() -> PathBuf {
    if let Ok(exe) = env::current_exe() {
        let mut dir = exe.as_path();
        while let Some(parent) = dir.parent() {
            if parent.join("pyproject.toml").is_file() && parent.join("skills/scripts").is_dir() {
                return parent.to_path_buf();
            }
            dir = parent;
        }
    }
    let home = env::var("HOME").expect("HOME not set");
    Path::new(&home).join(".claude")
}

fn uv_run(root: &Path, working_dir: &Path, python_args: &[&str], extra_args: &[String]) -> ! {
    let mut cmd = Command::new("uv");
    cmd.arg("run").arg("--project").arg(root);
    for a in python_args {
        cmd.arg(a);
    }
    cmd.args(extra_args);
    cmd.current_dir(working_dir);
    let err = cmd.exec();
    eprintln!("agent-tools: exec uv failed: {err}");
    std::process::exit(1);
}

fn main() {
    let cli = Cli::parse();
    let root = repo_root();

    match cli.command {
        Cmd::Skill { module, args } => {
            let full_module = format!("skills.{module}");
            uv_run(
                &root,
                &root.join("skills/scripts"),
                &["python3", "-m", &full_module],
                &args,
            );
        }
        Cmd::CcPretty { args } => {
            let script = root.join("scripts/cc-pretty.py");
            let script_str = script.to_str().expect("non-UTF8 path");
            let scripts_dir = root.join("scripts");
            let mut cmd = Command::new("uv");
            cmd.arg("run").arg("--project").arg(&root);
            cmd.arg("python3").arg(script_str);
            cmd.args(&args);
            // cc-pretty.py imports cc_pretty_parse from same directory
            cmd.env("PYTHONPATH", &scripts_dir);
            cmd.current_dir(&root);
            let err = cmd.exec();
            eprintln!("agent-tools: exec uv failed: {err}");
            std::process::exit(1);
        }
    }
}
