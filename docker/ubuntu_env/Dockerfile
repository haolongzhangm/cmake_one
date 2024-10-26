FROM ubuntu:24.04

ARG USER_NAME
ARG USER_ID
ARG USER_GID
# check USER_* ARGS is set
RUN if [ -z "${USER_NAME}" ]; then echo "USER_NAME is not set"; exit 1; fi
RUN if [ -z "${USER_ID}" ]; then echo "USER_ID is not set"; exit 1; fi
RUN if [ -z "${USER_GID}" ]; then echo "USER_GID is not set"; exit 1; fi

ENV PATH=${PATH}:/home/${USER_NAME}/.local/bin

# update
RUN apt-get update -y

# build env
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
pkg-config build-essential git-lfs autoconf gdb git-core gnupg \
flex bison gperf zip curl zlib1g-dev gcc g++ rsync wget vim \
llvm clang openjdk-8-jdk python3 python3-dev python3-pip \
python3-numpy python3-setuptools python-is-python3 lsb-release

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y apt-utils \
ninja-build

# install cross-build depends
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
libgcc-11-dev-arm64-cross libstdc++-11-dev-arm64-cross \
libgcc-11-dev-armhf-cross libstdc++-11-dev-armhf-cross

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
gcc-aarch64-linux-gnu gcc-arm-linux-gnueabi gcc-arm-linux-gnueabihf

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
g++-aarch64-linux-gnu g++-arm-linux-gnueabi g++-arm-linux-gnueabihf

# for use -fuse-ld=lld
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y lld

# at last we config user info
RUN echo "build docker user info: ${USER_NAME} ${USER_ID} ${USER_GID}"

RUN groupadd -g ${USER_GID} ${USER_NAME}
RUN useradd -u ${USER_ID} -g ${USER_GID} -m -s /bin/bash ${USER_NAME}
USER ${USER_NAME}

###################### build env for USER only ######################
# install some python packages for kuma
RUN python3 -m pip install --upgrade pip --break-system-packages --ignore-installed
RUN python3 -m pip install setuptools --break-system-packages
RUN python3 -m pip install wheel --break-system-packages
RUN python3 -m pip install gitpython requests --break-system-packages

# install cmake
RUN python3 -m pip install cmake==3.29.6 --break-system-packages

# install NDK
RUN mkdir -p /home/${USER_NAME}/
RUN curl https://dl.google.com/android/repository/android-ndk-r27-linux.zip -o /home/${USER_NAME}/android-ndk-r27-linux.zip
RUN unzip /home/${USER_NAME}/android-ndk-r27-linux.zip -d /home/${USER_NAME}/
RUN rm /home/${USER_NAME}/android-ndk-r27-linux.zip
# set NDK env
ENV ANDROID_NDK_HOME=/home/${USER_NAME}/android-ndk-r27
ENV NDK_ROOT=/home/${USER_NAME}/android-ndk-r27

