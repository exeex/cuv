import os
import shutil
from pathlib import Path
from typing import Optional

def create_project_directory(project_name: str, project_dir: Path) -> None:
    """Create the basic project directory structure."""
    # Create main directories
    (project_dir / "src").mkdir(parents=True, exist_ok=True)
    (project_dir / "interface").mkdir(parents=True, exist_ok=True)
    (project_dir / "build").mkdir(parents=True, exist_ok=True)
    
    # Create basic source files
    with open(project_dir / "src" / "main.cpp", "w") as f:
        f.write("""
import hello;

int main() {
    say_hello();
    return 0;
}
""")
    
    with open(project_dir / "src" / "hello.cpp", "w") as f:
        f.write("""
module;
#include <iostream>
module hello;

void say_hello(){
    std::cout << "Hello from module!" << std::endl;
}
""")

    # Create basic interface file
    with open(project_dir / "interface" / "hello.cppm", "w") as f:
        f.write("""
export module hello;

export void say_hello();
""")

def create_cxxproject_toml(project_name: str, project_dir: Path, 
                          cxx_standard: str = "20", 
                          compiler: Optional[str] = None) -> None:
    """Create the cxxproject.toml configuration file."""
    if compiler is None:
        # Try to find system compiler
        try:
            compiler = shutil.which("clang++") or shutil.which("g++")
        except:
            compiler = ""
            
    if compiler:
        c_compiler = compiler.replace("++", "")
    else:
        c_compiler = ""
    
    config = f"""[project]
name = "{project_name}"
version = "0.1.0"

[project.targets]
{project_name} = {{ type = "executable", sources = ["src/*.cpp", "interface/*.cppm"] }}

[project.toolchain]
C_COMPILER = "{c_compiler}"
CXX_COMPILER = "{compiler}"
AR = "/usr/bin/ar"

[project.settings]
cxx_standard = "{cxx_standard}"
warnings = "all"
warnings_as_errors = true
"""
    
    with open(project_dir / "cxxproject.toml", "w") as f:
        f.write(config)

def create_gitignore(project_dir: Path) -> None:
    """Create a basic .gitignore file."""
    gitignore_content = """
build/
*.o
*.a
*.so
*.pdb
.DS_Store
"""
    with open(project_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)

def create_license(project_dir: Path) -> None:
    """Create a default MIT license."""
    license_content = """MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    with open(project_dir / "LICENSE", "w") as f:
        f.write(license_content)

def create_new_project(project_name: str, project_dir: Path, 
                      cxx_standard: str = "20", 
                      compiler: Optional[str] = None) -> None:
    """Create a new CUV project with the given name."""
    # Validate project name
    if not project_name.isidentifier():
        raise ValueError("Project name must be a valid C++ identifier")
    
    # Check if directory exists
    if project_dir.exists():
        raise FileExistsError(f"Directory {project_dir} already exists")
    
    # Create project structure
    create_project_directory(project_name, project_dir)
    create_cxxproject_toml(project_name, project_dir, cxx_standard, compiler)
    create_gitignore(project_dir)
    create_license(project_dir)
    
    print(f"Created new project '{project_name}' at {project_dir}")
