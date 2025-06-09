import argparse
from cuv.toml_parser import load_project
from cuv.dep_resolver import resolve_dependencies
from cuv.cmake_writer import generate_cmake

def main():
    print("hello world")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync")
    sub.add_parser("build")

    args = parser.parse_args()

    if args.command == "sync":
        project = load_project("cproject.toml")
        resolve_dependencies(project)

    elif args.command == "build":
        project = load_project("cproject.toml")
        generate_cmake(project)
