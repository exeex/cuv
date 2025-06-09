cmake_minimum_required(VERSION 3.29)
project(mainapp LANGUAGES CXX)

add_subdirectory(../mathlib mathlib_build)

add_executable(mainapp src/main.cpp)
target_link_libraries(mainapp PRIVATE mathlib)
