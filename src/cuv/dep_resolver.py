import os
import subprocess

def resolve_dependencies(project):
    deps = project.get("dependencies", {})
    os.makedirs(".cuv/deps", exist_ok=True)
    for name, info in deps.items():
        if "git" in info:
            repo_url = info["git"]
            rev = info.get("rev", "main")
            target_dir = f".cuv/deps/{name}"
            if not os.path.exists(target_dir):
                print(f"Cloning {name}...")
                subprocess.run(["git", "clone", repo_url, target_dir])
            subprocess.run(["git", "-C", target_dir, "checkout", rev])
