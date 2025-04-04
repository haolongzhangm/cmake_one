set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR armv7)
set(ARM_CROSS_BUILD_ARCH armv7)

# now we support cross build for aarch64-linux by clang
# host always need install some base package, like clang, llvm, gcc, g++
# and install sysroot package: libgcc-11-dev-armhf-cross and libstdc++-11-dev-armhf-cross gcc-arm-linux-gnueabi gcc-arm-linux-gnueabihf g++-arm-linux-gnueabi g++-arm-linux-gnueabihf
# the version of 11 is depend on the version of gcc/g++ in host
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET arm-linux-gnueabihf)
set(CMAKE_C_COMPILER_TARGET arm-linux-gnueabihf)
set(CMAKE_COMMON_FLAG "-Wno-error=attributes -Wno-error=cpp -Wno-error=sign-compare -mfloat-abi=hard -mfpu=neon -mthumb")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CMAKE_COMMON_FLAG}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CMAKE_COMMON_FLAG}")
