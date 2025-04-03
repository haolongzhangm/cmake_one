set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR i386)
set(X86_CROSS_BUILD_ARCH i386)
set(CMAKE_SYSTEM_VERSION 10)

set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET i386-windows-msvc)
set(CMAKE_C_COMPILER_TARGET i386-windows-msvc)
set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "Embedded")
# set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

# linker to -fuse-ld=lld
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fuse-ld=lld")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -fuse-ld=lld")
