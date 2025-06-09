set(CMAKE_C_COMPILER   /usr/bin/clang-18 CACHE STRING "")
set(CMAKE_CXX_COMPILER /usr/bin/clang++-18 CACHE STRING "")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPERIMENTAL_CXX_MODULE_CMAKE_API ON)

set(CMAKE_INSTALL_PREFIX "$ENV{HOME}/local" CACHE PATH "Default install path to user local")

set(CMAKE_EXPORT_PACKAGE_REGISTRY OFF)

set(CMAKE_CXX_COMPILER_FRONTEND_VARIANT "GNU")

function(add_module_library target_name)
  cmake_parse_arguments(ARG "" "" "SRC_LIST" ${ARGN})

  if(NOT ARG_SRC_LIST)
    message(FATAL_ERROR "add_module_library requires SRC_LIST argument")
  endif()

  set(MODULES "")
  set(HEADERS "")
  set(SOURCES "")

  foreach(file IN LISTS ARG_SRC_LIST)
    get_filename_component(ext ${file} EXT)
    string(TOLOWER ${ext} ext_lc)
    if(ext_lc STREQUAL ".ixx")
      list(APPEND MODULES ${file})
    elseif(ext_lc STREQUAL ".h" OR ext_lc STREQUAL ".hpp" OR ext_lc STREQUAL ".hxx")
      list(APPEND HEADERS ${file})
    elseif(ext_lc STREQUAL ".cpp" OR ext_lc STREQUAL ".cc" OR ext_lc STREQUAL ".cxx")
      list(APPEND SOURCES ${file})
    else()
      message(WARNING "[add_module_library] Unknown source type: ${file}")
    endif()
  endforeach()

  add_library(${target_name} STATIC)

  if(SOURCES)
    target_sources(${target_name} PRIVATE ${SOURCES})
  endif()

  if(MODULES)
    target_sources(${target_name}
      PRIVATE
        FILE_SET cxx_modules TYPE CXX_MODULES FILES ${MODULES}
    )
  endif()

  if(HEADERS)
    target_sources(${target_name}
      PRIVATE
        FILE_SET headers TYPE HEADERS FILES ${HEADERS}
    )
  endif()
endfunction()

