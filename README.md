# CUV - C++ Unified Build System

CUV is a modern build system designed specifically for C++20 Modules, providing a development experience similar to Python's uv or Node.js's npm.

## Features

- 🚀 **Modern C++20 Module Support**: First-class support for C++20 Modules with proper dependency resolution
- 📦 **Package Management**: Manage external dependencies easily
- 🛠️ **Build System**: Ninja-based build system for fast and efficient builds
- 📦 **Project Management**: Create, build, and manage C++ projects with ease

## Getting Started

### Installation

CUV is designed to be used as a command-line tool. You can install it from source:

```bash
git clone https://github.com/exeex/cuv.git
cd cuv
pip install .
```

### CUV External Dependencies
- python >= 3.10
- ninja >= 1.12.1
- clang-scan-deps >= 19
- clang >= 19

```bash
# Recommended OS: ubuntu 24.04
sudo bash scripts/install_all.sh
```

### Creating a New Project

To create a new C++ project:

```bash
cuv new my_project
```

This will create a new project with the following structure:
```
my_project/
├── src/          # Source files
├── interface/    # Module interface files
├── build/        # Build output
├── cxxproject.toml  # Project configuration
├── .gitignore
└── LICENSE
```

### Building Your Project

Navigate to your project directory and build it:

```bash
cd my_project
cuv build
```

### Cleaning Build Artifacts

To clean the build directory:

```bash
cuv clean
```

## Project Configuration

CUV uses `cxxproject.toml` for project configuration. Here's an example configuration:

```toml
[project]
name = "my_project"
version = "0.1.0"

[project.targets]
my_project = { type = "executable", sources = ["src/*.cpp", "interface/*.cppm"] }

[project.toolchain]
C_COMPILER = "/usr/bin/clang"
CXX_COMPILER = "/usr/bin/clang++"
AR = "/usr/bin/ar"

[project.settings]
cxx_standard = "20"
warnings = "all"
warnings_as_errors = true
```

## Commands

- `cuv new <name>`: Create a new project
- `cuv build`: Build the project
- `cuv clean`: Clean build artifacts
- `cuv sync`: Sync external dependencies

## Example Project Structure

Here's a typical project structure:
```
my_project/
├── src/
│   └── main.cpp
├── interface/
│   └── hello.cppm
├── build/
├── cxxproject.toml
├── .gitignore
└── LICENSE
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details

## Support

For support, please open an issue in the GitHub repository.
