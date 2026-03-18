cmake_minimum_required(VERSION 3.28)
project(mde_cpp_starter LANGUAGES C CXX)

set(CMAKE_C_STANDARD 23)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(mde_cpp_starter src/main.cpp)
