FROM ubuntu:24.04

# set env
ENV PYTHON_VENV_PATH=/root/.venv
ENV PATH=${PYTHON_VENV_PATH}/bin:/root/.local/bin:${PATH}
ENV TOOLCHAIN_PATH=/root/toolchain

# update
RUN apt-get update -y

# build base env
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
pkg-config build-essential git-lfs autoconf gdb git-core gnupg \
flex bison gperf zip curl zlib1g-dev gcc g++ rsync wget vim \
llvm clang python3 python3-dev python3-pip python3-numpy \
python3-setuptools python-is-python3 lsb-release python3-venv \
apt-utils ninja-build git-lfs

# install java env
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
openjdk-21-jdk openjdk-21-jre openjdk-21-jre-headless

# install cross-build depends(arm64, arm)
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
libgcc-11-dev-arm64-cross libstdc++-11-dev-arm64-cross \
libgcc-11-dev-armhf-cross libstdc++-11-dev-armhf-cross
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
gcc-aarch64-linux-gnu gcc-arm-linux-gnueabi gcc-arm-linux-gnueabihf
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
g++-aarch64-linux-gnu g++-arm-linux-gnueabi g++-arm-linux-gnueabihf

# for use -fuse-ld=lld
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y lld

# install gitlfs
RUN git lfs install

# config python env
RUN python3 -m venv ${PYTHON_VENV_PATH}

# install some python packages for kuma
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install setuptools
RUN python3 -m pip install wheel
RUN python3 -m pip install gitpython requests

# install cmake
RUN python3 -m pip install cmake==3.29.6

RUN mkdir -p ${TOOLCHAIN_PATH}
# install ohos OpenHarmony_5.0.2.50
RUN curl https://cidownload.openharmony.cn/version/Master_Version/OpenHarmony_5.0.0.12_dev/20240219_200248/version-Master_Version-OpenHarmony_5.0.0.12_dev-20240219_200248-ohos-sdk-full.tar.gz -o ${TOOLCHAIN_PATH}/ohos-sdk-full.tar.gz
RUN tar -zxvf ${TOOLCHAIN_PATH}/ohos-sdk-full.tar.gz -C ${TOOLCHAIN_PATH}
RUN mv ${TOOLCHAIN_PATH}/manifest_tag.xml ${TOOLCHAIN_PATH}/ohos-sdk
RUN cd ${TOOLCHAIN_PATH}/ohos-sdk/linux && unzip native-linux-x64-5.0.0.12-Canary.zip
RUN rm ${TOOLCHAIN_PATH}/ohos-sdk-full.tar.gz
# set ohos env
ENV OHOS_NDK_ROOT=${TOOLCHAIN_PATH}/ohos-sdk/linux/native

# install cross-build depends(riscv64)
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
libgcc-11-dev-riscv64-cross libstdc++-11-dev-riscv64-cross
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
gcc-riscv64-linux-gnu
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
g++-riscv64-linux-gnu

# for host i386
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
g++-multilib

# install NDK 26c
RUN curl https://dl.google.com/android/repository/android-ndk-r26c-linux.zip -o ${TOOLCHAIN_PATH}/android-ndk-r26c-linux.zip
RUN unzip ${TOOLCHAIN_PATH}/android-ndk-r26c-linux.zip -d ${TOOLCHAIN_PATH}
RUN rm ${TOOLCHAIN_PATH}/android-ndk-r26c-linux.zip
# set NDK env
ENV ANDROID_NDK_HOME=${TOOLCHAIN_PATH}/android-ndk-r26c
ENV NDK_ROOT=${TOOLCHAIN_PATH}/android-ndk-r26c

RUN python3 -m pip install json5 wget numpy

# hexagon-clang need libtinfo.so.5
RUN ln -s /lib/x86_64-linux-gnu/libtinfo.so.6 /lib/x86_64-linux-gnu/libtinfo.so.5

RUN apt-get install -y libmagic1
RUN python3 -m pip install python-magic pyyaml tqdm

# env for doxygen
RUN apt-get update -y
RUN apt-get install -y doxygen graphviz doxygen ghostscript

# install windows build env
RUN apt-get install -y wine msitools ca-certificates
RUN git clone https://github.com/haolongzhangm/msvc-wine.git
# 10.0.18362 compat for windows xp sp3
ENV MSVC_WINE_VER=44dc13b5e62ecc2373fbe7e4727a525001f403f4
ENV MSVC_SDK_DST=/opt/msvc
RUN cd msvc-wine && git checkout ${MSVC_WINE_VER} &&\
PYTHONUNBUFFERED=1 python3 ./vsdownload.py --accept-license \
--dest ${MSVC_SDK_DST} --msvc-version 17.11 --sdk-version 10.0.22621 && \
./install.sh ${MSVC_SDK_DST} && cp msvcenv-native.sh ${MSVC_SDK_DST}
RUN apt install -y winbind
