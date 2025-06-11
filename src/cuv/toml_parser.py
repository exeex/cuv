import toml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

@dataclass
class ProjectConfig:
    """Project configuration data class."""
    project_name: str
    version: str
    cxx_standard: str
    warnings: str
    warnings_as_errors: bool
    targets: Dict[str, Dict[str, Any]]
    c_compiler: str
    cxx_compiler: str
    ar: str
    project_root: Path

    def get_target_sources(self, target_name: str) -> List[str]:
        """Get sources for a specific target."""
        target = self.targets.get(target_name, {})
        return target.get('sources', [])
    
    def get_target_type(self, target_name: str) -> Optional[str]:
        """Get type of a specific target."""
        target = self.targets.get(target_name, {})
        return target.get('type')

def load_project(path: Union[str, Path]) -> ProjectConfig:
    """Load and parse a cproject.toml file into a ProjectConfig object."""

    abs_path = Path(path).resolve()
    if not abs_path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")
    
    config = toml.load(abs_path)
    project_root = abs_path.parent
    
    # Parse and validate configuration
    project = config.get('project', {})
    targets = project.get('targets', {})
    toolchain = project.get('toolchain', {})
    settings = project.get('settings', {})
    
    return ProjectConfig(
        project_name=project.get('name', ''),
        version=project.get('version', ''),
        cxx_standard=settings.get('cxx_standard', '20'),
        warnings=settings.get('warnings', 'all'),
        warnings_as_errors=settings.get('warnings_as_errors', False),
        targets=targets,
        c_compiler=toolchain.get('C_COMPILER', ''),
        cxx_compiler=toolchain.get('CXX_COMPILER', ''),
        ar=toolchain.get('AR', ''),
        project_root=project_root
    )

if __name__ == "__main__":
    # Test parsing the example project
    test_project_path = Path(__file__).parent.parent.parent 
    toml_path = test_project_path / "tests" / "cuv-test-project" / "cproject.toml"
    
    try:
        project = load_project(toml_path)
        
        print("=== Project Configuration ===")
        print(f"Project Name: {project.project_name}")
        print(f"Version: {project.version}")
        print(f"Warnings: {project.warnings}")
        print(f"Warnings as Errors: {project.warnings_as_errors}")
        print(f"C++ Standard: C++{project.cxx_standard}")
        print(f"C Compiler: {project.c_compiler}")
        print(f"C++ Compiler: {project.cxx_compiler}")
        print(f"AR: {project.ar}")
        
        print("\n=== Targets ===")
        for target_name in project.targets:
            target_type = project.get_target_type(target_name)
            sources = project.get_target_sources(target_name)
            print(f"\nTarget: {target_name}")
            print(f"  Type: {target_type}")
            print("  Sources:")
            for source in sources:
                print(f"    {source}")
                
    except Exception as e:
        print(f"Error loading project: {str(e)}")
        exit(1)
