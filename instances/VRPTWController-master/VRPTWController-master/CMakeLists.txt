cmake_minimum_required(VERSION 3.0)

set(this VRPTWController)

project(${this})

set(CMAKE_CXX_STANDARD 11)
set(${this} C CXX)

add_subdirectory(src)

add_executable(${this} src/main.cpp)
add_executable(DummySolver DummySolver.cpp)
enable_testing()
add_test(NAME DummySolver COMMAND ${this} Dummy ../Instances/Solomon/R108.txt 2000 60 932.1 1 DummySolver)

target_link_libraries(${this} PUBLIC
    Controller   
    Data
    OutputFile
    dSolution
    Instance
)

target_include_directories(${this} PUBLIC 
    ${CMAKE_SOURCE_DIR}/src
)
