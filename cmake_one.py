#!/usr/bin/env python3

import argparse
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path


class CODE_NOT_IMP(Exception):
    pass


class Build:
    BUILD_ENV = "Linux"
    NINJA_BASE = "ninja"
    NINJA_INSTALL_STR = "install/strip"
    NINJA_VERBOSE = ""
    toolchains_config = ""
    NINJA_JOBS = ""
    NINJA_TARGET = ""
    CMAKE_C_FLAGS_CONFIG = ""
    CMAKE_CXX_FLAGS_CONFIG = ""

    # Android-termux will detect as Linux, so we do not declare for Android
    # when is host build, we will use host compiler and build for host arch
    SUPPORT_BUILD_ENV = ["Linux", "Windows", "Darwin"]

    cross_build_configs = {
        "ANDROID": ["x86_64", "i386", "aarch64", "armv7-a"],
        "LINUX": ["aarch64", "armv7-a", "rv64gcv", "rv64norvv"],
        "OHOS": ["aarch64"],
        "IOS": ["aarch64", "armv7-a"],
    }

    def code_not_imp():
        raise CODE_NOT_IMP

    def detect_build_env(self):
        self.BUILD_ENV = platform.system()
        assert (
            self.BUILD_ENV in self.SUPPORT_BUILD_ENV
        ), f"now only support build env at: {self.SUPPORT_BUILD_ENV}"
        if self.BUILD_ENV == "Windows":
            self.NINJA_BASE = "Ninja"
        logging.debug(f"build at host env: {self.BUILD_ENV}")

    def build(self):
        self.detect_build_env()
        parser = argparse.ArgumentParser(description="build tools for cmake project")
        parser.add_argument(
            "--build_type",
            type=str,
            choices=["Release", "Debug"],
            default="Release",
            help="build type, default is Release",
        )
        parser.add_argument(
            "--remove_old_build",
            action="store_true",
            help="remove old build dir before build, default off",
        )
        parser.add_argument(
            "--not_do_link_build_and_install",
            action="store_true",
            help="do not link build and install dir to repo dir, default off",
        )
        parser.add_argument(
            "--build_with_ninja_verbose",
            action="store_true",
            help="ninja with verbose, default off",
        )
        parser.add_argument(
            "--build_with_ninja_explain",
            action="store_true",
            help="ninja with -d explain to show command reason, default off",
        )
        parser.add_argument(
            "--repo_dir",
            type=str,
            default=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "test_repo"
            ),
            help="repo dir, default is os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_repo'), you can specify it for build other repo",
        )
        parser.add_argument(
            "--build_dir",
            type=str,
            default=None,
            help="if not specify, will use repo_dir/build",
        )
        parser.add_argument(
            "--install_dir",
            type=str,
            default=None,
            help="if not specify, will use build_dir/install",
        )

        parser.add_argument(
            "--ninja_jobs",
            type=int,
            default=None,
            help="ninja jobs, default is None, will use system cpu count",
        )

        parser.add_argument(
            "--ninja_target",
            type=str,
            default=None,
            help="only build specify target, default is None, Warning: if config this, will config self.NINJA_INSTALL_STR to null",
        )

        parser.add_argument(
            "--cmake_options",
            type=str,
            default=None,
            help='cmake options, used to config repo self define options, like -DENABLE_ASAN=ON, as this build tools is for all cmake project, so we can not config all options, so provide this option for user to config self define options, WARN: use "ENABLE_ASAN=ON" instead of "-DENABLE_ASAN=ON", if you want to config more than one options, split by space, for example: "ENABLE_ASAN=ON ENABLE_TSAN=ON"',
        )

        sub_parser = parser.add_subparsers(
            dest="sub_command", help="sub command for build", required=True
        )

        cross_build_p = sub_parser.add_parser(
            "cross_build", help="cross build for other arch and os"
        )

        cross_build_p.add_argument(
            "--cross_build_target_os",
            type=str,
            default="ANDROID",
            choices=self.cross_build_configs.keys(),
            help=f"cross build target os, now support: {self.cross_build_configs.keys()}",
        )
        cross_build_p.add_argument(
            "--cross_build_target_arch",
            type=str,
            default="aarch64",
            help=f"cross build target arch, now support: {self.cross_build_configs}",
        )

        host_build_p = sub_parser.add_parser("host_build", help="do host build,")
        host_build_p.add_argument(
            "--build_for_32bit",
            action="store_true",
            help="build for 32bit, default off, only support for host build",
        )

        args = parser.parse_args()

        if args.ninja_jobs:
            self.NINJA_JOBS = f"-j{args.ninja_jobs}"

        if args.ninja_target:
            self.NINJA_TARGET = args.ninja_target

        # check repo_dir is valid and convert to abs path
        args.repo_dir = os.path.abspath(args.repo_dir)
        assert os.path.isdir(
            args.repo_dir
        ), f"error config --repo_dir {args.repo_dir} is not a valid dir: is not dir"

        # check args.repo_dir should have CMakeLists.txt
        assert os.path.isfile(
            os.path.join(args.repo_dir, "CMakeLists.txt")
        ), f"error config --repo_dir {args.repo_dir} is not a valid dir: can not find CMakeLists.txt"

        # config build_dir and convert to abs path
        if args.build_dir is None:
            if args.sub_command == "cross_build":
                args.build_dir = os.path.join(
                    args.repo_dir,
                    f"build-{args.cross_build_target_os}-{args.cross_build_target_arch}-{args.build_type}",
                )
            elif args.sub_command == "host_build":
                args.build_dir = os.path.join(
                    args.repo_dir, f"build-host-{args.build_type}"
                )
                if args.build_for_32bit:
                    args.build_dir = os.path.join(
                        args.repo_dir, f"build-host-{args.build_type}-32bit"
                    )
            else:
                logging.error(
                    f"code issue happened for: {args.sub_command} please FIXME!!!"
                )
                code_not_imp()
        args.build_dir = os.path.abspath(args.build_dir)

        if args.install_dir is None:
            args.install_dir = os.path.join(args.build_dir, "install")
        args.install_dir = os.path.abspath(args.install_dir)

        if args.sub_command == "cross_build":
            # check cross_build_target_arch
            logging.debug("cross build now")
            assert (
                args.cross_build_target_os in self.cross_build_configs.keys()
            ), f"error config: not support --cross_build_target_os {args.cross_build_target_os} now support one of: {self.cross_build_configs.keys()}"
            assert (
                args.cross_build_target_arch
                in self.cross_build_configs[args.cross_build_target_os]
            ), f"error config: not support --cross_build_target_arch {args.cross_build_target_arch} now support one of: {self.cross_build_configs[args.cross_build_target_os]}"
            if args.cross_build_target_os == "ANDROID":
                assert (
                    "NDK_ROOT" in os.environ
                ), "can not find NDK_ROOT env, please download from https://developer.android.com/ndk/downloads then export it path to NDK_ROOT"
                ndk_path = os.environ.get("NDK_ROOT")
                android_toolchains = os.path.join(
                    ndk_path, "build/cmake/android.toolchain.cmake"
                )
                assert os.path.isfile(
                    android_toolchains
                ), f"error config env: NDK_ROOT: {ndk_path}, can not find android toolchains: {android_toolchains}"
                logging.debug(f"use NDK toolchains: {android_toolchains}")
                ABI_NATIVE_LEVEL_MAPS = {
                    "x86_64": ["x86_64", 21],
                    "i386": ["x86", 16],
                    "aarch64": ["arm64-v8a", 30],
                    "armv7-a": ["armeabi-v7a with NEON", 30],
                }
                assert (
                    args.cross_build_target_arch in ABI_NATIVE_LEVEL_MAPS
                ), f"codeissue happened, please fix add {args.cross_build_target_arch} to ABI_NATIVE_LEVEL_MAPS"
                an = ABI_NATIVE_LEVEL_MAPS[args.cross_build_target_arch]
                self.toolchains_config = f'-DCMAKE_TOOLCHAIN_FILE={android_toolchains} -DANDROID_ABI="{an[0]}" -DANDROID_NATIVE_API_LEVEL={an[1]}'
            elif args.cross_build_target_os == "OHOS":
                assert (
                    "OHOS_NDK_ROOT" in os.environ
                ), "can not find OHOS_NDK_ROOT env, https://gitee.com/openharmony/build/wikis/NDK/HOW%20TO%20USE%20NDK%20(linux), then export it path to OHOS_NDK_ROOT"
                ohos_ndk_path = os.environ.get("OHOS_NDK_ROOT")
                ohos_toolchains = os.path.join(
                    ohos_ndk_path, "build/cmake/ohos.toolchain.cmake"
                )
                assert os.path.isfile(
                    ohos_toolchains
                ), f"error config env: OHOS_NDK_ROOT: {ohos_ndk_path}, can not find ohos toolchains: {ohos_toolchains}"
                logging.debug(f"use ohos NDK toolchains: {ohos_toolchains}")
                self.toolchains_config = f"-DCMAKE_TOOLCHAIN_FILE={ohos_toolchains} -DOHOS_STL=c++_static -DOHOS_ARCH=arm64-v8a -DOHOS_PLATFORM=OHOS"
            elif args.cross_build_target_os == "IOS":
                # cross-build for IOS no need strip target
                self.NINJA_INSTALL_STR = "install"
                assert (
                    self.BUILD_ENV == "Darwin"
                ), f"error: do not support build for IOS at: {self.BUILD_ENV}, only support at MACOS host"
                IOS_ARCH_MAPS = {
                    "aarch64": "arm64",
                    "armv7-a": "armv7",
                }
                assert (
                    args.cross_build_target_arch in IOS_ARCH_MAPS
                ), f"codeissue happened, do not support arch {args.cross_build_target_arch} for IOS"
                """to config this, if u want to build other, like simulator or for iwatch,
                please do manually modify
                OS_PLATFORM=("OS" "OS64" "SIMULATOR" "SIMULATOR64" "TVOS" "WATCHOS" "SIMULATOR_TVOS")
                XCODE_IOS_PLATFORM=("iphoneos" "iphonesimulator" "appletvos" "appletvsimulator" "watchos", "watchsimulator")
                IOS_ARCHS=("arm64" "armv7" "armv7k" "arm64e" "armv7s"). by default we only trigger build arm64/armv7 for iphoneos
                """
                ios_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/ios.toolchain.cmake",
                )
                assert os.path.isfile(
                    ios_toolchains
                ), f"code issue happened, can not find ios toolchains: {ios_toolchains}"
                OS_PLATFORM = "OS"
                XCODE_IOS_PLATFORM = "iphoneos"

                self.toolchains_config = f"-DCMAKE_TOOLCHAIN_FILE={ios_toolchains} -DIOS_TOOLCHAIN_ROOT={ios_toolchains} -DOS_PLATFORM={OS_PLATFORM} -DXCODE_IOS_PLATFORM={XCODE_IOS_PLATFORM} -DIOS_ARCH={IOS_ARCH_MAPS[args.cross_build_target_arch]} -DCMAKE_ASM_COMPILER=/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -DCMAKE_MAKE_PROGRAM=ninja"
            elif args.cross_build_target_os == "LINUX":
                rv64gcv_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/riscv64-rvv-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    rv64gcv_toolchains
                ), f"code issue happened, can not find rv64gcv toolchains: {rv64gcv_toolchains}"
                rv64norvv_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/riscv64-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    rv64norvv_toolchains
                ), f"code issue happened, can not find rv64norvv toolchains: {rv64norvv_toolchains}"
                aarch64_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/aarch64-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    aarch64_toolchains
                ), f"code issue happened, can not find aarch64 toolchains: {aarch64_toolchains}"
                armv7a_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/arm-linux-gnueabihf.toolchain.cmake",
                )
                assert os.path.isfile(
                    armv7a_toolchains
                ), f"code issue happened, can not find armv7a toolchains: {armv7a_toolchains}"

                logging.debug(
                    f"config for cross build LINUX-{args.cross_build_target_arch}"
                )
                toolchains_maps = {
                    "aarch64": f"-DCMAKE_TOOLCHAIN_FILE={aarch64_toolchains}",
                    "armv7-a": f"-DCMAKE_TOOLCHAIN_FILE={armv7a_toolchains}",
                    "rv64gcv": f"-DCMAKE_TOOLCHAIN_FILE={rv64gcv_toolchains}",
                    "rv64norvv": f"-DCMAKE_TOOLCHAIN_FILE={rv64norvv_toolchains}",
                }
                assert (
                    args.cross_build_target_arch in toolchains_maps
                ), f"code issue happened, please add {args.cross_build_target_arch} to toolchains_maps if support"
                self.toolchains_config = toolchains_maps[args.cross_build_target_arch]
            else:
                logging.error(
                    f"code issue happened for: {args.cross_build_target_os} please FIXME!!!"
                )
                code_not_imp()

        elif args.sub_command == "host_build":
            logging.debug("host build now")
            logging.debug("we are in host build now")
            if self.BUILD_ENV == "Windows":
                # host build for Windows no need strip target
                logging.debug("host build for Windows")
                self.toolchains_config = (
                    "-DCMAKE_C_COMPILER=clang-cl.exe -DCMAKE_CXX_COMPILER=clang-cl.exe"
                )
                self.NINJA_INSTALL_STR = "install"
                # TODO: add host build for Windows
                logging.error("do not imp host build Windows now")
                code_not_imp()
            elif self.BUILD_ENV == "Linux":
                logging.debug("host build for Linux")
                self.toolchains_config = (
                    "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++"
                )
            elif self.BUILD_ENV == "Darwin":
                self.toolchains_config = (
                    "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++"
                )
                logging.debug("host build for MACOS")
                self.toolchains_config = (
                    "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++"
                )
            else:
                logging.error(
                    f"code issue happened for: {self.BUILD_ENV} please FIXME!!!"
                )
                code_not_imp()
        else:
            logging.error(
                f"code issue happened for: {args.sub_command} please FIXME!!!"
            )
            code_not_imp()

        if args.build_with_ninja_verbose:
            self.NINJA_VERBOSE = "-v"

        if args.build_with_ninja_explain:
            # force to enable verbose when explain
            self.NINJA_VERBOSE = "-v -d explain"

        cmake_config = f'cmake -G Ninja -H"{args.repo_dir}" -B"{args.build_dir}" {self.toolchains_config} -DCMAKE_INSTALL_PREFIX="{args.install_dir}" -DCMAKE_BUILD_TYPE={args.build_type}'
        if args.cmake_options:
            # split by space, then add -D to each item
            _ = args.cmake_options.split(" ")
            user_flags = " ".join([f"-D{i}" for i in _])
            logging.debug(f"user CMake override flags: {user_flags}")
            cmake_config = cmake_config + " " + user_flags + " "

        # set CMAKE_EXPORT_COMPILE_COMMANDS ON
        cmake_config = cmake_config + " -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"

        # handle host build 32bit
        host_32bit_args = {"Windows": "", "Linux": "-m32", "Darwin": "-m32"}
        assert (
            self.BUILD_ENV in host_32bit_args
        ), f"code issue happened!!, please add 32bit build flags for: {self.BUILD_ENV} in host_32bit_args"
        if args.sub_command == "host_build" and args.build_for_32bit:
            assert (
                cmake_config.find("CMAKE_C_FLAGS") < 0
            ), "code issue happened: double config CMAKE_C_FLAGS please FIXME!!"
            assert (
                cmake_config.find("CMAKE_CXX_FLAGS") < 0
            ), "code issue happened: double config CMAKE_CXX_FLAGS please FIXME!!"
            self.CMAKE_C_FLAGS_CONFIG = (
                self.CMAKE_C_FLAGS_CONFIG + f"{host_32bit_args[self.BUILD_ENV]}"
            )
            self.CMAKE_CXX_FLAGS_CONFIG = (
                self.CMAKE_CXX_FLAGS_CONFIG + f"{host_32bit_args[self.BUILD_ENV]}"
            )

        # add -g for debug build by default
        self.CMAKE_C_FLAGS_CONFIG = self.CMAKE_C_FLAGS_CONFIG + " -g"
        self.CMAKE_CXX_FLAGS_CONFIG = self.CMAKE_CXX_FLAGS_CONFIG + " -g"

        # now freeze CMAKE_C_FLAGS_CONFIG and CMAKE_CXX_FLAGS_CONFIG
        if self.CMAKE_C_FLAGS_CONFIG:
            cmake_config = (
                cmake_config + f' -DCMAKE_C_FLAGS="{self.CMAKE_C_FLAGS_CONFIG}"'
            )
        if self.CMAKE_CXX_FLAGS_CONFIG:
            cmake_config = (
                cmake_config + f' -DCMAKE_CXX_FLAGS="{self.CMAKE_CXX_FLAGS_CONFIG}"'
            )
        logging.debug(f"python3 args: {args}")
        config_cmd = f"{cmake_config}"
        if args.ninja_target:
            self.NINJA_INSTALL_STR = ""
            logging.debug(
                f"only build specify target: {args.ninja_target} , need config self.NINJA_INSTALL_STR to null, caused by ninja install/strip will trigger all target build"
            )

        # remove old build dir if need
        if args.remove_old_build:
            logging.debug(f"remove old build dir: {args.build_dir}")
            if os.path.exists(args.build_dir):
                shutil.rmtree(args.build_dir)
            logging.debug(f"remove old install dir: {args.install_dir} done")
            if os.path.exists(args.install_dir):
                shutil.rmtree(args.install_dir)
        logging.debug(f"create new build dir: {args.build_dir}")
        os.makedirs(args.build_dir, exist_ok=True)
        logging.debug(f"create new install dir: {args.install_dir}")
        os.makedirs(args.install_dir, exist_ok=True)

        logging.debug(
            f"build dir info: repo_dir: {args.repo_dir} build_dir: {args.build_dir} install_dir: {args.install_dir}"
        )

        build_cmd = f"{self.NINJA_BASE} {self.NINJA_INSTALL_STR} {self.NINJA_VERBOSE} {self.NINJA_JOBS} {self.NINJA_TARGET}"
        copy_cmd = ""
        link_install_cmd = ""
        link_build_cmd = ""
        if not args.not_do_link_build_and_install:
            link_install_cmd = f"ln -snf {args.install_dir} {args.repo_dir}/install"
            link_build_cmd = f"ln -snf {args.build_dir} {args.repo_dir}/build"
            copy_cmd = f"mv compile_commands.json {args.repo_dir}"
        with open(os.path.join(args.build_dir, "config.sh"), "w") as f:
            f.write("#!/bin/bash\n")
            f.write("set -ex\n")
            f.write(f"{config_cmd}\n")
            f.write(f"{copy_cmd}\n")
            f.write(f"{build_cmd}\n")
            f.write(f"{link_install_cmd}\n")
            f.write(f"{link_build_cmd}\n")

        # show config.sh
        logging.debug("show config.sh")
        with open(os.path.join(args.build_dir, "config.sh"), "r") as f:
            logging.debug(f.read())

        # run config.sh
        os.chdir(args.build_dir)
        logging.debug(f"run config.sh")
        subprocess.check_call(f"bash {args.build_dir}/config.sh", shell=True)


if __name__ == "__main__":
    LOG_FORMAT = "[cmake_one] - %(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    b = Build()
    b.build()
