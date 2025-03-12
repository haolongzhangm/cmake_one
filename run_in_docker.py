import getpass
import logging
import os
import platform
import subprocess
import sys


def is_tty_supported():
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()


def get_docker_tag_and_dockerfile() -> dict:
    cwd = os.path.dirname(os.path.abspath(__file__))
    DOCKER_INFO = {
        "Linux": [
            "ubuntu_2404",
            os.path.join(cwd, "docker", "ubuntu_env", "Dockerfile"),
        ],
        "Windows": [
            "windows_env",
            os.path.join(cwd, "docker", "windows_env", "Dockerfile"),
        ],
        "Darwin": ["macos_env", os.path.join(cwd, "docker", "macos_env", "Dockerfile")],
    }
    plt = platform.system()
    assert plt in DOCKER_INFO, f"Platform {plt} is not supported"
    i = DOCKER_INFO[plt]
    tag = i[0]
    dockerfile = i[1]
    assert os.path.exists(dockerfile), f"dockerfile {dockerfile} does not exist"
    return tag, dockerfile


def run_in_docker(cmd: str):
    # check docker is installed and docker run in rootless mode
    # why need rootless, because the docker run in root mode will cause the permission issue, if you want to run in root mode, you can remove the following code
    docker_info = subprocess.check_output("docker info", shell=True)
    assert (
        b"rootless" in docker_info
    ), "Docker is not running in rootless mode, please refs: https://docs.docker.com/engine/security/rootless/ also You can run the following command to install rootless docker: curl -fsSL https://get.docker.com/rootless | sh"

    user = getpass.getuser()
    # build the docker image
    tag, dockerfile = get_docker_tag_and_dockerfile()
    path_of_dockerfile = os.path.dirname(os.path.abspath(dockerfile))
    build_cmd = f"docker build -t {tag} -f {dockerfile} {path_of_dockerfile}"
    logging.debug(f"Running: {build_cmd}")
    subprocess.check_call(build_cmd, shell=True)

    logging.debug(f"Running: {cmd} in docker")

    docker_args = "-it"
    envs = os.environ
    if "JENKINS_HOME" in envs:
        logging.debug("run in jenkins, set docker_args to -i")
        docker_args = "-i"
    if "CI_SERVER_NAME" in envs and envs["CI_SERVER_NAME"] == "GitLab":
        logging.debug("run in GitLab, set docker_args to -i")
        docker_args = "-i"
    if not is_tty_supported():
        logging.debug("tty is not supported, set docker_args to -i")
        docker_args = "-i"

    docker_cmd = f"docker run --rm {docker_args}"
    map_to_envs = ["Commit_Id", "MODELOPR_VER"]
    for env in map_to_envs:
        if env in envs:
            value = envs[env]
            docker_cmd += f" -e {env}={env}"
    # this map is used to correct compile_commands.json for sysroot
    map_to_envs_with_org_prefix = ["TEST_NOT_EXIT", "NDK_ROOT", "OHOS_NDK_ROOT"]
    for env in map_to_envs_with_org_prefix:
        if env in envs:
            value = envs[env]
            docker_cmd += f" -e CMAKE_ONE_PRFIX_{env}={value}"
    # map user .ssh to docker
    host_ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    docker_ssh_dir = f"/root/.ssh"
    docker_cmd += f" -v {host_ssh_dir}:{docker_ssh_dir}"
    # map tmp to docker tmp
    docker_cmd += " -v /tmp:/tmp:rw"
    # map the current directory to docker
    docker_cmd += f" -v {os.getcwd()}:{os.getcwd()}:rw"

    # split the cmd by space, then find --repo_dir xxx, --build_dir xxx, --install_dir xxx
    # then map the directory to docker
    cmd_parts = cmd.split()
    logging.debug(f"cmd_parts: {cmd_parts}")
    new_cmd = []
    skip = False
    for i, part in enumerate(cmd_parts):
        if part == "--repo_dir":
            d = cmd_parts[i + 1]
            d = os.path.abspath(d)
            os.makedirs(d, exist_ok=True)
            docker_cmd += f" -v {d}:{d}:rw"
            new_cmd += [part, d]
            skip = True
        elif part == "--build_dir":
            d = cmd_parts[i + 1]
            d = os.path.abspath(d)
            os.makedirs(d, exist_ok=True)
            docker_cmd += f" -v {d}:{d}:rw"
            new_cmd += [part, d]
            skip = True
        elif part == "--install_dir":
            d = cmd_parts[i + 1]
            d = os.path.abspath(d)
            os.makedirs(d, exist_ok=True)
            docker_cmd += f" -v {d}:{d}:rw"
            new_cmd += [part, d]
            skip = True
        else:
            if skip:
                skip = False
            else:
                new_cmd.append(part)
    new_cmd_str = " ".join(new_cmd)
    # add last build cmd
    docker_cmd += f" {tag} /bin/bash -c '{new_cmd_str}'"
    logging.debug(f"Running: {docker_cmd}")
    subprocess.check_call(docker_cmd, shell=True)


if __name__ == "__main__":
    LOG_FORMAT = "[run_in_docker] - %(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    cmake_one_py = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cmake_one.py"
    )
    # pass all arguments to the cmake_one.py
    def needs_quotes(arg):
        return ' ' in arg

    processed_args = [  
        f'"{arg}"' if needs_quotes(arg) else arg
        for arg in sys.argv[1:]
    ]
    # pass all arguments to the cmake_one.py
    cmd = f"python3 {cmake_one_py} {' '.join(processed_args)}"
    run_in_docker(cmd)
