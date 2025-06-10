"""
Ninja build file generator for C/C++ projects.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from toml_parser import ProjectConfig

class NinjaWriter:
    def __init__(self, project_config: ProjectConfig, build_dir: str):
        """
        Initialize NinjaWriter with project configuration and build directory.
        
        Args:
            project_config: Project configuration object
            build_dir: Absolute path to build directory
        """
        self.config = project_config
        self.build_dir = build_dir
        self.rules = []
        self.builds = []
        
    def write_build_file(self, output_path: str):
        """
        Write the generated build.ninja file.
        
        Args:
            output_path: Path to write the build.ninja file
        """
        with open(output_path, 'w') as f:
            self.write_header(f)
            self.write_rules(f)
            self.write_builds(f)
            self.write_footer(f)
    
    def write_header(self, f):
        """Write ninja build file header."""
        f.write("ninja_required_version = 1.10\n\n")
        
    def write_rules(self, f):
        """Write all build rules."""
        self.write_compile_rule(f)
        self.write_link_rule(f)
        
    def write_compile_rule(self, f):
        """Write compile rule for C++ files."""
        f.write("rule compile_cpp\n")
        f.write("  command = $cxx -MMD -MF $out.d -o $out -c $in $cxxflags\n")
        f.write("  description = CXX $out\n")
        f.write("  depfile = $out.d\n")
        f.write("  generator = 1\n")
        
    def write_link_rule(self, f):
        """Write link rule for creating libraries."""
        f.write("\nrule link\n")
        f.write("  command = $cxx -shared -o $out $in $ldflags\n")
        f.write("  description = LINK $out\n")
    
    def write_builds(self, f):
        """Write all build statements."""
        self.write_object_builds(f)
        self.write_library_build(f)
        
    def write_object_builds(self, f):
        """Write build statements for object files."""
        for target_name, target in self.config.targets.items():
            if target.get('type') == 'library':
                sources = target.get('sources', [])
                for source_pattern in sources:
                    for source_file in Path(self.config.project_root).glob(source_pattern):
                        obj_file = self.get_object_path(source_file)
                        f.write(f"build {obj_file}: compile_cpp {source_file}\n")
                        f.write(f"  cxxflags = $cxxflags\n")
    
    def write_library_build(self, f):
        """Write build statement for library."""
        for target_name, target in self.config.targets.items():
            if target.get('type') == 'library':
                objects = []
                for source_pattern in target.get('sources', []):
                    for source_file in Path(self.config.project_root).glob(source_pattern):
                        objects.append(self.get_object_path(source_file))
                
                lib_file = self.get_library_path(target_name)
                f.write(f"\nbuild {lib_file}: link {' '.join(objects)}\n")
                f.write(f"  cxxflags = $cxxflags\n")
    
    def get_object_path(self, source_file: Path) -> str:
        """Get object file path from source file."""
        rel_path = source_file.relative_to(self.config.project_root)
        obj_path = Path(self.build_dir) / "objects" / rel_path.with_suffix('.o')
        return str(obj_path)
    
    def get_library_path(self, target_name: str) -> str:
        """Get library file path."""
        return str(Path(self.build_dir) / f"lib{target_name}.so")
    
    def write_footer(self, f):
        """Write ninja build file footer."""
        f.write("\n# Default target\n")
        f.write("default all\n")

def generate_build_file(project_config: ProjectConfig, build_dir: str, output_path: str):
    """
    Generate ninja build file from project configuration.
    
    Args:
        project_config: Project configuration object
        build_dir: Absolute path to build directory
        output_path: Path to write the build.ninja file
    """
    writer = NinjaWriter(project_config, build_dir)
    writer.write_build_file(output_path)

if __name__ == "__main__":
    import sys
    import os
    from toml_parser import load_project
    
    # Test with the example project
    test_project_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  "tests", "cuv-test-project", "cproject.toml")
    
    try:
        project = load_project(test_project_path)
        build_dir = os.path.join(os.path.dirname(test_project_path), "build_test")
        output_path = os.path.join(build_dir, "build.ninja")
        os.makedirs(build_dir, exist_ok=True)
        
        generate_build_file(project, build_dir, output_path)
        print(f"Generated build.ninja at {output_path}")
        
    except Exception as e:
        print(f"Error generating build file: {str(e)}")
        sys.exit(1)
