set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR riscv64)

# now we support cross build for riscv64-linux by clang
# host always need install some base package, like clang, llvm, gcc, g++
# and install sysroot package: libgcc-11-dev-arm64-cross and libstdc++-11-dev-arm64-cross gcc-riscv64-linux-gnu g++-riscv64-linux-gnu
# the version of 11 is depend on the version of gcc/g++ in host
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET riscv64-linux-gnu)
set(CMAKE_C_COMPILER_TARGET riscv64-linux-gnu)
set(CMAKE_COMMON_FLAG "-Wno-error=attributes -Wno-error=cpp -Wno-error=sign-compare -march=rv64gc -mabi=lp64d")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CMAKE_COMMON_FLAG}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CMAKE_COMMON_FLAG}")
# this flag just for some project use RISCV_TOOLCHAIN_ROOT to identification is RVV, infact this tools do not use it, so we just set it to a fake path
set(RISCV_TOOLCHAIN_ROOT "NO-EXIST")
