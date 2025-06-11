"""
Ninja build file generator for C/C++ projects.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, TextIO, Union
from cuv.toml_parser import ProjectConfig
from cuv.gen_compile_commands import CompileCommandsWriter
from cuv.dep_resolver import resolve_dependencies
from dataclasses import dataclass
from enum import Enum, auto
import subprocess


@dataclass
class BuildFlags:
    """Data class for build flags."""

    cxx: str
    ar: str
    cxxflags: str
    ldflags: str


@dataclass
class NinjaTask:
    """Data class for ninja task."""

    output: str
    input: List[str]
    deps: List[str]
    rule: str


@dataclass
class NinjaRule:
    """Data class for ninja rule."""

    name: str
    command: str
    description: str


class SourceType(Enum):
    CppSource = auto()
    CppModule = auto()
    StaticLibrary = auto()
    Executable = auto()
    Unknown = auto()


class NinjaWriter:
    def __init__(self, project_config: ProjectConfig, build_dir: Union[str, Path]):
        """
        Initialize NinjaWriter with project configuration and build directory.

        Args:
            project_config: Project configuration object
            build_dir: Absolute path to build directory
        """
        self.config = project_config
        self.project_root = Path(project_config.project_root)
        self.build_dir = Path(build_dir)
        self.objects_dir = self.build_dir / "objects"
        self.targets_dir = self.build_dir / "targets"
        self.module_cache_dir = self.build_dir / "module_cache"

    def write_build_vars(self, f: TextIO):
        """Write build variables."""

        flags = BuildFlags(
            cxx=self.config.cxx_compiler,
            ar=self.config.ar,
            cxxflags="-std=c++20 -Wall -O2",
            ldflags="",
        )
        
        module_cache_dir = self.module_cache_dir.relative_to(self.build_dir)
        f.write("# === build variables ===\n")
        f.write(f"cxx = {flags.cxx}\n")
        f.write(f"ar = {flags.ar}\n")
        f.write(f"module_cache_dir = {module_cache_dir}\n")
        f.write(
            f"cxxflags = {flags.cxxflags} -fprebuilt-module-path=$module_cache_dir\n"
        )
        if len(flags.ldflags) > 0:
            f.write(f"ldflags = {flags.ldflags}\n")
        f.write("\n")

    def get_source_type(self, source_file: Path) -> SourceType:
        """Determine source file type."""
        if source_file.suffix in [".cpp", ".cc"]:
            return SourceType.CppSource
        elif source_file.suffix in [".ixx", ".cppm"]:
            return SourceType.CppModule
        return SourceType.Unknown

    def write_rules(self, f):
        """Write compile rules for different source types."""

        f.write("# ====build rules====\n\n")
        rules = [
            NinjaRule(
                name="cxx_compile",
                command="$cxx $cxxflags -c $in -o $out -fprebuilt-module-path=$module_cache_dir",
                description="Compiling source $in",
            ),
            NinjaRule(
                name="cxx_module_compile",
                command="$cxx $cxxflags --precompile -o $out -c $in",
                description="Compiling module interface $in",
            ),
            NinjaRule(
                name="cxx_static_library",
                command="$ar rcs $out $in",
                description="Linking $out",
            ),
            NinjaRule(
                name="cxx_link",
                command="$cxx $in -o $out $ldflags",
                description="Linking $out",
            ),
        ]
        for rule in rules:
            f.write(
                f"rule {rule.name}\n  command = {rule.command}\n  description = {rule.description}\n"
            )
            f.write("\n")

    def gen_task_deps_list(self):

        objects_dir = self.objects_dir.relative_to(self.build_dir)
        targets_dir = self.targets_dir.relative_to(self.build_dir)
        module_cache_dir = self.module_cache_dir.relative_to(self.build_dir)
        writer = CompileCommandsWriter(
            self.config,
            self.build_dir,
            objects_dir,
            targets_dir,
            module_cache_dir,
        )

        os.makedirs(self.build_dir, exist_ok=True)

        # Write main build file
        with open(self.build_dir / "compile_commands.json", "w") as f:
            json.dump(writer.gen_build_commands(), f, indent=2)

        cmd = "clang-scan-deps-19 -compilation-database compile_commands.json -format=p1689 -o deps.json"
        subprocess.run(cmd.split(" "), cwd=self.build_dir)

        with open(self.build_dir / "deps.json", "r") as f:
            json_deps = json.load(f)
        task_list = resolve_dependencies(json_deps)

        return task_list

    def write_target_builds(self, f: TextIO):
        """Write build statements for object files."""

        objects_dir = self.objects_dir.relative_to(self.build_dir)
        targets_dir = self.targets_dir.relative_to(self.build_dir)
        module_cache_dir = self.module_cache_dir.relative_to(self.build_dir)
        # register ninja tasks (without deps and topo sort)
        ninja_task_dict: Dict[str, NinjaTask] = {}
        ninja_target_list: List[str] = []
        for target_name, target in self.config.targets.items():
            sources = target.get("sources", [])
            target_obj_files = []

            for source_pattern in sources:
                for src_file in Path(self.project_root).glob(source_pattern):
                    src_type = self.get_source_type(src_file)
                    match src_type:
                        case SourceType.CppModule:
                            tar_file = str(
                                module_cache_dir / (src_file.stem + ".pcm")
                            )
                            ninja_task_dict[tar_file] = NinjaTask(
                                output=tar_file, input=[str(src_file)], rule="cxx_module_compile", deps=[]
                            )
                        case SourceType.CppSource:
                            tar_file = str(objects_dir / (src_file.stem + ".o"))
                            ninja_task_dict[tar_file] = NinjaTask(
                                output=tar_file, input=[str(src_file)], rule="cxx_compile", deps=[]
                            )
                            target_obj_files.append(tar_file)

            if target.get("type") == "library":
                tar_file = str(targets_dir / f"lib{target_name}.a")
                ninja_target_list.append(NinjaTask(
                    output=tar_file, input=target_obj_files, rule="cxx_static_library", deps=[]
                ))

            elif target.get("type") == "executable":
                tar_file = str(targets_dir / target_name)
                ninja_target_list.append(NinjaTask(
                    output=tar_file, input=target_obj_files, rule="cxx_link", deps=[]
                ))

        # get task_list from deps.json (with topo sort)
        task_list = self.gen_task_deps_list()

        f.write("# ====build tasks====\n\n")
        for task_name, task_deps in task_list:
            ninja_task = ninja_task_dict[task_name]
            ninja_task.deps = task_deps

            ninja_cmd = f"build {ninja_task.output}: {ninja_task.rule}"
            if len(ninja_task.input) > 0:
                ninja_cmd += " ".join(ninja_task.input)
            if len(ninja_task.deps) > 0:
                ninja_cmd += " | " + " ".join(ninja_task.deps)
            ninja_cmd += "\n"

            f.write(ninja_cmd)

        f.write("# ====build targets====\n\n")
        for target in ninja_target_list:
            ninja_cmd = f"build {target.output}: {target.rule}"
            if len(target.input) > 0:
                ninja_cmd += " " + " ".join(target.input)
            if len(target.deps) > 0:
                ninja_cmd += " | " + " ".join(target.deps)
            ninja_cmd += "\n"

            f.write(ninja_cmd)
        f.write("\n")

    def write_footer(self, f: TextIO):
        """Write ninja build file footer."""
        targets_dir = self.targets_dir.relative_to(self.build_dir)
        f.write("\n# Default target\n")
        for target_name, target in self.config.targets.items():
            if target.get("type") == "library":
                lib_file = str(targets_dir / f"lib{target_name}.a")
                f.write(f"default {lib_file}\n")
            elif target.get("type") == "executable":
                exe_file = str(targets_dir / target_name)
                f.write(f"default {exe_file}\n")


def generate_build_file(
    project_config: ProjectConfig, build_dir: str, output_path: str
):
    """Generate ninja build file from project config."""
    writer = NinjaWriter(project_config, build_dir)

    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(writer.objects_dir, exist_ok=True)
    os.makedirs(writer.module_cache_dir, exist_ok=True)
    os.makedirs(writer.targets_dir, exist_ok=True)

    # Write main build file
    with open(output_path, "w") as f:
        f.write("ninja_required_version = 1.10\n\n")
        # Write build variables
        writer.write_build_vars(f)

        # Write rules
        writer.write_rules(f)

        # Write build statements
        writer.write_target_builds(f)
        writer.write_footer(f)


if __name__ == "__main__":
    # Load project config
    from toml_parser import load_project

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(
        project_root, "tests", "cuv-test-project", "cxxproject.toml"
    )
    config = load_project(config_path)

    # Generate build file
    build_dir = os.path.join(project_root, "tests", "cuv-test-project", "build_test")
    output_path = os.path.join(build_dir, "build.ninja")
    generate_build_file(config, build_dir, output_path)
    print(f"Generated build.ninja at {output_path}")
