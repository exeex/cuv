import os
from pathlib import Path
from typing import List, Dict, Any, TextIO, Union
from toml_parser import ProjectConfig
from dataclasses import dataclass
import json

@dataclass
class BuildFlags:
    """Data class for build flags."""
    cxx: str
    ar: str
    cxxflags: str
    ldflags: str

class CompileCommandsWriter:
    def __init__(
        self,
        project_config: ProjectConfig,
        build_dir: Union[str, Path],
        objects_dir: Union[str, Path],
        targets_dir: Union[str, Path],
        module_cache_dir: Union[str, Path],
    ):
        """
        Initialize CompileCommandsWriter with project configuration and build directory.

        Args:
            project_config: Project configuration object
            build_dir: Absolute path to build directory
            objects_dir: Absolute path to objects directory
            targets_dir: Absolute path to targets directory
            module_cache_dir: Absolute path to module cache directory
        """
        self.config = project_config
        self.project_root = Path(project_config.project_root)
        self.build_dir = Path(build_dir)
        self.objects_dir = Path(objects_dir)
        self.targets_dir = Path(targets_dir)
        self.module_cache_dir = Path(module_cache_dir)


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



    def gen_build_commands(self):
        """Write build statements for object files."""
        flags = self.get_build_flags()

        commands: List[Dict[str, str]] = []
        for target_name, target in self.config.targets.items():
            sources = target.get("sources", [])

            for source_pattern in sources:
                for source_file in Path(self.project_root).glob(source_pattern):
                    source_type = self.get_source_type(source_file)
                    if source_type in ["ixx", "cppm"]:
                        out_file = self.module_cache_dir / (source_file.stem + ".pcm")
                        command = f"{flags.cxx} {source_file} -o {out_file} {flags.cxxflags} -I{self.project_root}/include --precompile\n"
                        
                    elif source_type in ["cpp", "cc"]:
                        out_file = self.objects_dir / (source_file.stem + ".o")
                        command = f"{flags.cxx} {source_file} -o {out_file} {flags.cxxflags} -I{self.project_root}/include\n"

                    commands.append({
                        "directory": str(self.project_root),
                        "file": str(source_file.relative_to(self.project_root)),
                        "command": command,
                        "output": str(out_file),
                    })

        return commands



def generate_compile_commands(
    project_config: ProjectConfig, build_dir: Union[str, Path]
):

    project_root = Path(project_config.project_root)
    build_dir = Path(build_dir)
    objects_dir = (build_dir / "objects").relative_to(build_dir)
    targets_dir = (build_dir / "targets").relative_to(build_dir)
    module_cache_dir = (build_dir / "module_cache").relative_to(
        build_dir
    )
    writer = CompileCommandsWriter(project_config, build_dir, objects_dir, targets_dir, module_cache_dir)

    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)

    # Write main build file
    with open(build_dir / "compile_commands.json", "w") as f:
        json.dump(writer.gen_build_commands(), f, indent=2)



if __name__ == "__main__":
    # Load project config
    from toml_parser import load_project
    from pathlib import Path

    project_root = Path(os.path.abspath(__file__)).parent.parent.parent
    config_path = project_root / "tests" / "cuv-test-project" / "cproject.toml"
    config = load_project(config_path)

    # Generate build file
    build_dir = os.path.join(project_root, "tests", "cuv-test-project", "build_test")
    generate_compile_commands(config, build_dir)
    print(f"Generated compile_commands.json at {build_dir}")
