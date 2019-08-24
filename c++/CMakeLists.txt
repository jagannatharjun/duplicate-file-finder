project(DuplicateFileFinder)
cmake_minimum_required(VERSION 3.14)


find_package(OpenSSL REQUIRED)

add_executable(main main.cpp)
set_target_properties(main PROPERTIES CXX_STANDARD 17)
target_include_directories(main PUBLIC E:/Cpp/Projects/Headers/include)
target_link_libraries(main OpenSSL::Crypto)


add_executable(test test.cpp)
set_target_properties(test PROPERTIES CXX_STANDARD 17)

