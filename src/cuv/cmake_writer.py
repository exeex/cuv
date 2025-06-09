import os

def generate_cmake(project):
    src_dir = project["build"]["module_root"]
    with open("build/CMakeLists.txt", "w") as f:
        f.write(f"cmake_minimum_required(VERSION 3.29)\n")
        f.write(f"project({project['project']['name']} LANGUAGES CXX)\n")
        f.write(f"set(CMAKE_CXX_STANDARD 20)\n\n")

        f.write("add_executable(main\n")
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".ixx") or file.endswith(".cpp"):
                    f.write(f"  {os.path.join(root, file)}\n")
        f.write(")\n")
