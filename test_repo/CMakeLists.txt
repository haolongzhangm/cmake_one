cmake_minimum_required(VERSION 3.15...3.30)

project(TestProject VERSION 1.0 LANGUAGES CXX)

add_executable(test_exe main.cpp)
add_executable(test_exe_depends_shared main.cpp)

# test_exe depends on api_module
add_subdirectory(api_module)
target_link_libraries(test_exe PRIVATE api_module)
target_link_libraries(test_exe_depends_shared PRIVATE api_module_shared)

# install test_exe
install(TARGETS test_exe DESTINATION bin)
install(TARGETS test_exe_depends_shared DESTINATION bin)
