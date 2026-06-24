cmake_minimum_required(VERSION 3.10)

# 上级目录（工具链和预编译库均在此处）
set(ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/..)
set(TOOLCHAIN_DIR ${ROOT_DIR}/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf)

# 交叉编译器必须在 project() 之前设置
set(CMAKE_C_COMPILER   ${TOOLCHAIN_DIR}/bin/arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_DIR}/bin/arm-linux-gnueabihf-g++)

set(CMAKE_SYSROOT        ${TOOLCHAIN_DIR}/arm-linux-gnueabihf/libc)
set(CMAKE_FIND_ROOT_PATH ${TOOLCHAIN_DIR}/arm-linux-gnueabihf)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY BOTH)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

project(extrinsic_calibration CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -Wall")

add_executable(extrinsic_calibration
    extrinsic_calibration.cpp
    main.cpp
)

# OpenCV 头文件
target_include_directories(extrinsic_calibration PRIVATE
    ${ROOT_DIR}/libs/prebuild_libs/opencv/include/opencv4
)

# OpenCV 预编译库路径
set(OPENCV_LIB_DIR ${ROOT_DIR}/libs/prebuild_libs/opencv/release/glibc_shared_lib_11.1.0)

target_link_libraries(extrinsic_calibration PRIVATE
    ${OPENCV_LIB_DIR}/libopencv_calib3d.so
    ${OPENCV_LIB_DIR}/libopencv_features2d.so
    ${OPENCV_LIB_DIR}/libopencv_flann.so
    ${OPENCV_LIB_DIR}/libopencv_imgcodecs.so
    ${OPENCV_LIB_DIR}/libopencv_imgproc.so
    ${OPENCV_LIB_DIR}/libopencv_core.so
    pthread
    dl
    m
)

message(STATUS "Cross-compiling for ARM: ${TOOLCHAIN_DIR}")
message(STATUS "CXX Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Sysroot: ${CMAKE_SYSROOT}")
