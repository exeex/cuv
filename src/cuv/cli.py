import argparse
from cuv.toml_parser import load_project
from cuv.dep_resolver import resolve_dependencies
from cuv.ninja_writer import generate_build_file
from pathlib import Path
import subprocess
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", help="subcommands", required=True)

    sync_parser = sub.add_parser("sync", help="Resolve and sync project dependencies")
    build_parser = sub.add_parser("build", help="Build the project using ninja")

    # Add arguments to sync parser
    sync_parser.add_argument(
        "--config",
        help="Path to project configuration file",
        default="cproject.toml"
    )
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-sync dependencies"
    )

    # Add arguments to build parser
    build_parser.add_argument(
        "--config",
        help="Path to project configuration file",
        default="cproject.toml"
    )
    build_parser.add_argument(
        "--build-dir",
        help="Path to build directory",
        default="build"
    )
    build_parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directory before building"
    )

    args = parser.parse_args()

    if args.command == "sync":
        project = load_project(args.config)
        if args.force:
            print("Force re-syncing dependencies...")
        # resolve_external_dependencies(project)

    elif args.command == "build":
        project = load_project(args.config)
        build_dir = Path(args.build_dir)
        if args.clean:
            print(f"Cleaning build directory: {build_dir}")
            subprocess.run(["rm", "-rf", str(build_dir)])
        build_dir.mkdir(exist_ok=True)
        print(f"Generated build.ninja in {build_dir}")
        generate_build_file(project, str(build_dir), str(build_dir / "build.ninja"))
        subprocess.run(["ninja", "-C", str(build_dir)])
