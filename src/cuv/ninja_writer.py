"""
Ninja build file generator for C/C++ projects.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, TextIO, Union
from toml_parser import ProjectConfig
from cuv.gen_compile_commands import CompileCommandsWriter 
from dataclasses import dataclass
import subprocess

@dataclass
class BuildFlags:
    """Data class for build flags."""

    cxx: str
    ar: str
    cxxflags: str
    ldflags: str


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
        self.objects_dir = (self.build_dir / "objects").relative_to(self.build_dir)
        self.targets_dir = (self.build_dir / "targets").relative_to(self.build_dir)
        self.module_cache_dir = (self.build_dir / "module_cache").relative_to(
            self.build_dir
        )

    def get_build_flags(self) -> BuildFlags:
        """Get build flags from project config."""
        return BuildFlags(
            cxx=self.config.cxx_compiler,
            ar=self.config.ar,
            cxxflags="-std=c++20 -Wall -O2",
            ldflags="",
        )

    def get_source_type(self, source_file: Path) -> str:
        """Determine source file type."""
        if source_file.suffix == ".cpp":
            return "cpp"
        elif source_file.suffix == ".ixx":
            return "ixx"
        elif source_file.suffix == ".cppm":
            return "cppm"
        return "unknown"

    def write_rules(self, f):
        """Write compile rules for different source types."""
        f.write(
            f"""
# 建立模組快取目錄
rule create_dir
  command = mkdir -p $out
  description = Creating directory $out

# 一般 C++ 編譯規則 - 會從快取目錄尋找模組
rule cxx_compile
  command = $cxx $cxxflags -c $in -o $out -fprebuilt-module-path=$module_cache_dir
  description = Compiling source $in

# 模組介面編譯規則 - 產生 BMI 到快取目錄
rule cxx_module_compile
  command = $cxx $cxxflags --precompile -o $out -c $in
  description = Compiling module interface $in

# 編譯靜態庫規則
rule cxx_static_library
  command = $ar rcs $out $in
  description = Linking $out

# 連結規則
rule cxx_link
  command = $cxx $in -o $out $ldflags
  description = Linking $out
"""
        )

    def gen_depedency_map(self):
        writer = CompileCommandsWriter(self.config, self.build_dir, self.objects_dir, self.targets_dir, self.module_cache_dir)

        os.makedirs(self.build_dir, exist_ok=True)

        # Write main build file
        with open(self.build_dir / "compile_commands.json", "w") as f:
            json.dump(writer.gen_build_commands(), f, indent=2)

        cmd = "clang-scan-deps-19 -compilation-database compile_commands.json -format=p1689 > deps.json"
        subprocess.run(cmd.split(" "), cwd=self.build_dir)



    def write_build_vars(self, f: TextIO):
        """Write build variables."""
        flags = self.get_build_flags()
        module_cache_dir = self.build_dir / "module_cache"
        f.write(f"cxx = {flags.cxx}\n")
        f.write(f"ar = {flags.ar}\n")
        f.write(f"module_cache_dir = {module_cache_dir}\n")
        f.write(
            f"cxxflags = {flags.cxxflags} -fprebuilt-module-path=$module_cache_dir\n"
        )
        if len(flags.ldflags) > 0:
            f.write(f"ldflags = {flags.ldflags}\n")

    def load_depedency_map(self):
        with open(self.build_dir / "deps.json", "r") as f:
            return json.load(f)

    def write_target_builds(self, f: TextIO):
        """Write build statements for object files."""
        flags = self.get_build_flags()

        # 先建立物件目錄
        f.write(f"build {self.objects_dir}: create_dir\n")
        f.write(f"build {self.module_cache_dir}: create_dir\n")
        f.write(f"build {self.targets_dir}: create_dir\n")

        for target_name, target in self.config.targets.items():
            sources = target.get("sources", [])
            target_deps = []
            obj_deps = []

            # 編譯模組
            for source_pattern in sources:
                for source_file in Path(self.project_root).glob(source_pattern):
                    source_type = self.get_source_type(source_file)
                    if source_type in ["ixx", "cppm"]:
                        pcm_file = self.module_cache_dir / (source_file.stem + ".pcm")
                        f.write(
                            f"build {pcm_file}: cxx_module_compile {source_file} | {self.module_cache_dir}\n"
                        )
                        f.write(f"  cxx = {flags['cxx']}\n")
                        f.write(
                            f"  cxxflags = {flags['cxxflags']} -I{self.project_root}/include\n"
                        )
                        obj_deps.append(pcm_file)
            obj_deps = [str(x) for x in obj_deps]
            # 編譯實現
            for source_pattern in sources:
                for source_file in Path(self.project_root).glob(source_pattern):
                    source_type = self.get_source_type(source_file)
                    if source_type != "unknown":
                        if source_type in ["cpp", "cc"]:
                            obj_file = self.objects_dir / (source_file.stem + ".o")
                            f.write(
                                f"build {obj_file}: cxx_compile {source_file} | {' '.join(obj_deps)}\n"
                            )
                            f.write(f"  cxx = {flags['cxx']}\n")
                            f.write(
                                f"  cxxflags = {flags['cxxflags']} -I{self.project_root}/include\n"
                            )
                            target_deps.append(obj_file)

            target_deps = [str(x) for x in target_deps]
            if target.get("type") == "library":
                # 連結庫文件
                lib_file = self.targets_dir / f"lib{target_name}.a"
                f.write(
                    f"build {lib_file}: cxx_static_library {' '.join(target_deps)}\n"
                )
            elif target.get("type") == "executable":
                # 連結可執行文件
                exe_file = self.targets_dir / target_name
                f.write(f"build {exe_file}: cxx_link {' '.join(target_deps)}\n")

    def write_footer(self, f: TextIO):
        """Write ninja build file footer."""
        f.write("\n# Default target\n")
        for target_name, target in self.config.targets.items():
            if target.get("type") == "library":
                lib_file = self.get_library_path(target_name)
                f.write(f"default {lib_file}\n")


def generate_build_file(
    project_config: ProjectConfig, build_dir: str, output_path: str
):
    """Generate ninja build file from project config."""
    writer = NinjaWriter(project_config, build_dir)

    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)
    writer.gen_depedency_map()
    writer.load_depedency_map()

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
        project_root, "tests", "cuv-test-project", "cproject.toml"
    )
    config = load_project(config_path)

    # Generate build file
    build_dir = os.path.join(project_root, "tests", "cuv-test-project", "build_test")
    output_path = os.path.join(build_dir, "build.ninja")
    generate_build_file(config, build_dir, output_path)
    print(f"Generated build.ninja at {output_path}")
