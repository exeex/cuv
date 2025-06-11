import toml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

class ProjectConfig:
    def __init__(self, config: Dict[str, Any], project_root: str):
        self.config = config
        self.project_root = project_root
        
    @property
    def project_name(self) -> str:
        return self.config.get('project', {}).get('name', '')
    
    @property
    def version(self) -> str:
        return self.config.get('project', {}).get('version', '')
    
    @property
    def build_type(self) -> str:
        return self.config.get('build-system', {}).get('settings', {}).get('build_type', 'Release')
    
    @property
    def cxx_standard(self) -> int:
        return int(self.config.get('build-system', {}).get('compiler', {}).get('cxx_standard', '20'))
    
    @property
    def targets(self) -> Dict[str, Dict[str, Any]]:
        return self.config.get('build-system', {}).get('targets', {})
    
    def get_target_sources(self, target_name: str) -> List[str]:
        target = self.targets.get(target_name, {})
        return target.get('sources', [])
    
    def get_target_type(self, target_name: str) -> Optional[str]:
        target = self.targets.get(target_name, {})
        return target.get('type')
    
    @property
    def c_compiler(self) -> str:
        """Get the C compiler path."""
        return self.config.get('build-system', {}).get('toolchain', {}).get('C_COMPILER', '')
    
    @property
    def cxx_compiler(self) -> str:
        """Get the C++ compiler path."""
        return self.config.get('build-system', {}).get('toolchain', {}).get('CXX_COMPILER', '')

    @property
    def ar(self) -> str:
        """Get the AR archive tool path."""
        return self.config.get('build-system', {}).get('toolchain', {}).get('AR', '')

def load_project(path: str) -> ProjectConfig:
    """Load and parse a cproject.toml file."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Project file not found: {path}")
    
    config = toml.load(abs_path)
    project_root = os.path.dirname(abs_path)
    return ProjectConfig(config, project_root)

if __name__ == "__main__":
    # Test parsing the example project
    test_project_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  "tests", "cuv-test-project", "cproject.toml")
    
    try:
        project = load_project(test_project_path)
        
        print("=== Project Configuration ===")
        print(f"Project Name: {project.project_name}")
        print(f"Version: {project.version}")
        print(f"Build Type: {project.build_type}")
        print(f"C++ Standard: C++{project.cxx_standard}")
        print(f"C Compiler: {project.c_compiler}")
        print(f"C++ Compiler: {project.cxx_compiler}")
        
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
