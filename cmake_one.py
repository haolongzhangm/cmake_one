#!/usr/bin/env python3

import argparse
import logging
import os
import platform
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

    # Android-termux will detect as Linux, so we do not declare for Android
    # when is host build, we will use host compiler and build for host arch
    SUPPORT_BUILD_ENV = ["Linux", "Windows", "Darwin"]

    cross_build_configs = {
        "ANDROID": ["x86_64", "i386", "aarch64", "armv7-a"],
        "LINUX": ["aarch64", "armv7-a", "rv64gcv0p7", "rv4norvv"],
        "OHOS": ["aarch64"],
        "IOS": ["aarch64", "armv7-a"],
    }

    def code_not_imp():
        raise CODE_NOT_IMP

    def detect_build_env(self):
        self.BUILD_ENV = platform.system()
        assert (
            self.BUILD_ENV in self.SUPPORT_BUILD_ENV
        ), "now only support build env at: {}".format(self.SUPPORT_BUILD_ENV)
        if self.BUILD_ENV == "Windows":
            self.NINJA_BASE = "Ninja"
        logging.debug("build at host env: {}".format(self.BUILD_ENV))

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
            "--build_with_ninja_verbose",
            action="store_true",
            help="ninja with verbose, default off",
        )
        parser.add_argument(
            "--repo_dir",
            type=str,
            default=os.path.join(os.path.dirname(__file__), "test_repo"),
            help="repo dir, default is os.path.join(os.path.dirname(__file__), 'test_repo'), you can specify it for build other repo",
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
            "--cmake_options",
            type=str,
            default=None,
            help="cmake options, used to config repo self define options, like -DENABLE_ASAN=ON, as this build tools is for all cmake project, so we can not config all options, so provide this option for user to config self define options",
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
            help="cross build target os, now support: {}".format(
                self.cross_build_configs.keys()
            ),
        )
        cross_build_p.add_argument(
            "--cross_build_target_arch",
            type=str,
            default="aarch64",
            help="cross build target arch, now support: {}".format(
                self.cross_build_configs
            ),
        )

        host_build_p = sub_parser.add_parser("host_build", help="do host build,")
        host_build_p.add_argument(
            "--build_for_32bit",
            action="store_true",
            help="build for 32bit, default off, only support for host build",
        )

        args = parser.parse_args()

        # check repo_dir is valid and convert to abs path
        args.repo_dir = os.path.abspath(args.repo_dir)
        assert os.path.isdir(
            args.repo_dir
        ), "error config --repo_dir {} is not a valid dir: is not dir".format(
            args.repo_dir
        )

        # check args.repo_dir should have CMakeLists.txt
        assert os.path.isfile(
            os.path.join(args.repo_dir, "CMakeLists.txt")
        ), "error config --repo_dir {} is not a valid dir: can not find CMakeLists.txt".format(
            args.repo_dir
        )

        # config build_dir and convert to abs path
        if args.build_dir is None:
            args.build_dir = os.path.join(args.repo_dir, "build")
        args.build_dir = os.path.abspath(args.build_dir)

        if args.install_dir is None:
            args.install_dir = os.path.join(args.build_dir, "install")
        args.install_dir = os.path.abspath(args.install_dir)

        # remove old build dir if need
        if args.remove_old_build:
            logging.debug("remove old build dir: {}".format(args.build_dir))
            subprocess.check_call("rm -rf {}".format(args.build_dir), shell=True)
            logging.debug("remove old install dir: {} done".format(args.install_dir))
            subprocess.check_call("rm -rf {}".format(args.install_dir), shell=True)
        logging.debug("create new build dir: {}".format(args.build_dir))
        subprocess.check_call("mkdir -p {}".format(args.build_dir), shell=True)
        logging.debug("create new install dir: {}".format(args.install_dir))
        subprocess.check_call("mkdir -p {}".format(args.install_dir), shell=True)

        logging.debug(
            "build dir info: repo_dir: {} build_dir: {} install_dir: {}".format(
                args.repo_dir, args.build_dir, args.install_dir
            )
        )

        # now cd to build_dir
        os.chdir(args.build_dir)

        if args.sub_command == "cross_build":
            # check cross_build_target_arch
            logging.debug("cross build now")
            assert (
                args.cross_build_target_os in self.cross_build_configs.keys()
            ), "error config: not support --cross_build_target_os {} now support one of: {}".format(
                args.cross_build_target_os, self.cross_build_configs.keys()
            )
            assert (
                args.cross_build_target_arch
                in self.cross_build_configs[args.cross_build_target_os]
            ), "error config: not support --cross_build_target_arch {} now support one of: {}".format(
                args.cross_build_target_arch,
                self.cross_build_configs[args.cross_build_target_os],
            )
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
                ), "error config env: NDK_ROOT: {}, can not find android toolchains: {}".format(
                    ndk_path, android_toolchains
                )
                logging.debug("use NDK toolchains: {}".format(android_toolchains))
                ABI_NATIVE_LEVEL_MAPS = {
                    "x86_64": ["x86_64", 21],
                    "i386": ["x86", 16],
                    "aarch64": ["arm64-v8a", 30],
                    "armv7-a": ["armeabi-v7a with NEON", 30],
                }
                assert (
                    args.cross_build_target_arch in ABI_NATIVE_LEVEL_MAPS
                ), "codeissue happened, please fix add {} to ABI_NATIVE_LEVEL_MAPS".format(
                    args.cross_build_target_arch
                )
                an = ABI_NATIVE_LEVEL_MAPS[args.cross_build_target_arch]
                self.toolchains_config = '-DCMAKE_TOOLCHAIN_FILE={} -DANDROID_ABI=\\"{}\\" -DANDROID_NATIVE_API_LEVEL={}'.format(
                    android_toolchains, an[0], an[1]
                )
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
                ), "error config env: NDK_ROOT: {}, can not find ohos toolchains: {}".format(
                    ohos_ndk_path, ohos_toolchains
                )
                logging.debug("use ohos NDK toolchains: {}".format(ohos_toolchains))
                self.toolchains_config = "-DCMAKE_TOOLCHAIN_FILE={} -DOHOS_STL=c++_static -DOHOS_ARCH=arm64-v8a -DOHOS_PLATFORM=OHOS".format(
                    ohos_toolchains
                )
            elif args.cross_build_target_os == "IOS":
                # cross-build for IOS no need strip target
                self.NINJA_INSTALL_STR = "install"
                assert (
                    self.BUILD_ENV == "Darwin"
                ), "error: do not support build for IOS at: {}, only support at MACOS host".format(
                    self.BUILD_ENV
                )
                IOS_ARCH_MAPS = {
                    "aarch64": "arm64",
                    "armv7-a": "armv7",
                }
                assert (
                    args.cross_build_target_arch in IOS_ARCH_MAPS
                ), "codeissue happened, do not support arch {} for IOS".format(
                    args.cross_build_target_arch
                )
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
                ), "code issue happened, can not find ios toolchains: {}".format(
                    ios_toolchains
                )
                OS_PLATFORM = "OS"
                XCODE_IOS_PLATFORM = "iphoneos"

                self.toolchains_config = "-DCMAKE_TOOLCHAIN_FILE={} -DIOS_TOOLCHAIN_ROOT={} -DOS_PLATFORM={} -DXCODE_IOS_PLATFORM={} -DIOS_ARCH={} -DCMAKE_ASM_COMPILER={} -DCMAKE_MAKE_PROGRAM=ninja".format(
                    ios_toolchains,
                    ios_toolchains,
                    OS_PLATFORM,
                    XCODE_IOS_PLATFORM,
                    IOS_ARCH_MAPS[args.cross_build_target_arch],
                    "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang",
                )
            elif args.cross_build_target_os == "LINUX":
                rv64gcv0p7_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/riscv64-rvv-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    rv64gcv0p7_toolchains
                ), "code issue happened, can not find rv64gcv0p7 toolchains: {}".format(
                    rv64gcv0p7_toolchains
                )
                rv64norvv_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/riscv64-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    rv64norvv_toolchains
                ), "code issue happened, can not find rv64norvv toolchains: {}".format(
                    rv64norvv_toolchains
                )
                aarch64_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/aarch64-linux-gnu.toolchain.cmake",
                )
                assert os.path.isfile(
                    aarch64_toolchains
                ), "code issue happened, can not find aarch64 toolchains: {}".format(
                    aarch64_toolchains
                )
                armv7a_toolchains = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "toolchains/arm-linux-gnueabihf.toolchain.cmake",
                )
                assert os.path.isfile(
                    armv7a_toolchains
                ), "code issue happened, can not find armv7a toolchains: {}".format(
                    armv7a_toolchains
                )

                logging.debug(
                    "config for cross build LINUX-{}".format(
                        args.cross_build_target_arch
                    )
                )
                toolchains_maps = {
                    "aarch64": "-DCMAKE_TOOLCHAIN_FILE={}".format(aarch64_toolchains),
                    "armv7-a": "-DCMAKE_TOOLCHAIN_FILE={}".format(armv7a_toolchains),
                    "rv64gcv0p7": "-DCMAKE_TOOLCHAIN_FILE={}".format(
                        rv64gcv0p7_toolchains
                    ),
                    "rv64norvv": "-DCMAKE_TOOLCHAIN_FILE={}".format(
                        rv64norvv_toolchains
                    ),
                }
                assert (
                    args.cross_build_target_arch in toolchains_maps
                ), "code issue happened, please add {} to toolchains_maps if support".format(
                    args.cross_build_target_arch
                )
                self.toolchains_config = toolchains_maps[args.cross_build_target_arch]
            else:
                logging.error(
                    "code issue happened for: {} please FIXME!!!".format(
                        args.cross_build_target_os
                    )
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
                    "code issue happened for: {} please FIXME!!!".format(self.BUILD_ENV)
                )
                code_not_imp()
        else:
            logging.error(
                "code issue happened for: {} please FIXME!!!".format(args.sub_command)
            )
            code_not_imp()

        if args.build_with_ninja_verbose:
            self.NINJA_VERBOSE = "-v"

        cmake_config = 'cmake -G Ninja -H\\"{}\\" -B\\"{}\\" {} -DCMAKE_INSTALL_PREFIX=\\"{}\\"'.format(
            args.repo_dir, args.build_dir, self.toolchains_config, args.install_dir
        )
        cmake_config = cmake_config + " -DCMAKE_BUILD_TYPE={}".format(args.build_type)
        if args.cmake_options:
            cmake_config = cmake_config + " {}".format(args.cmake_options)

        # handle host build 32bit
        host_32bit_args = {"Windows": "", "Linux": "-m32", "Darwin": "-m32"}
        assert (
            self.BUILD_ENV in host_32bit_args
        ), "code issue happened!!, please add 32bit build flags for: {} in host_32bit_args".format(
            self.BUILD_ENV
        )
        if args.sub_command == "host_build" and args.build_for_32bit:
            assert (
                cmake_config.find("CMAKE_C_FLAGS") < 0
            ), "code issue happened: double config CMAKE_C_FLAGS please FIXME!!"
            cmake_config = cmake_config + ' -DCMAKE_C_FLAGS=\\"{}\\"'.format(
                host_32bit_args[self.BUILD_ENV]
            )
            assert (
                cmake_config.find("CMAKE_CXX_FLAGS") < 0
            ), "code issue happened: double config CMAKE_CXX_FLAGS please FIXME!!"
            cmake_config = cmake_config + ' -DCMAKE_CXX_FLAGS=\\"{}\\"'.format(
                host_32bit_args[self.BUILD_ENV]
            )

        logging.debug("python3 args: {}".format(args))
        config_cmd = "{}".format(cmake_config)
        logging.debug("cmake config: {}".format(config_cmd))
        subprocess.check_call('bash -c "{}"'.format(config_cmd), shell=True)
        build_cmd = "{} {} {}".format(
            self.NINJA_BASE, self.NINJA_INSTALL_STR, self.NINJA_VERBOSE
        )
        logging.debug("cmake build: {}".format(build_cmd))
        subprocess.check_call('bash -c "{}"'.format(build_cmd), shell=True)


if __name__ == "__main__":
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    b = Build()
    b.build()
