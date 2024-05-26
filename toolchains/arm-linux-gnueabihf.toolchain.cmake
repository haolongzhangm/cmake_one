set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch32)

# now we support cross build for aarch64-linux by clang
# host always need install some base package, like clang, llvm, gcc, g++
# and install sysroot package: libgcc-11-dev-armhf-cross and libstdc++-11-dev-armhf-cross
# the version of 11 is depend on the version of gcc/g++ in host
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_C_FLAGS "--target=arm-linux-gnueabihf" CACHE STRING "c compiler flags" FORCE)
set(CMAKE_CXX_FLAGS "--target=arm-linux-gnueabihf" CACHE STRING "cxx compiler flags" FORCE)
set(CMAKE_COMMON_FLAG "-Wno-error=attributes -Wno-error=cpp -Wno-error=sign-compare")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CMAKE_COMMON_FLAG}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CMAKE_COMMON_FLAG}")
