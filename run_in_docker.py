import getpass
import os
import platform
import subprocess
import sys


def get_docker_tag_and_dockerfile() -> dict:
    cwd = os.path.dirname(__file__)
    DOCKER_INFO = {
        "Linux": [
            "ubuntu_2404",
            os.path.join(cwd, "docker", "ubuntu_env", "Dockerfile"),
        ],
        "Windows": [
            "windows_env",
            os.path.join(cwd, "docker", "windows_env", "Dockerfile"),
        ],
        "Darwin":
        ["macos_env",
         os.path.join(cwd, "docker", "macos_env", "Dockerfile")],
    }
    plt = platform.system()
    assert plt in DOCKER_INFO, f"Platform {plt} is not supported"
    i = DOCKER_INFO[plt]
    tag = i[0]
    dockerfile = i[1]
    assert os.path.exists(
        dockerfile), f"dockerfile {dockerfile} does not exist"
    return tag, dockerfile


def run_in_docker(cmd: str):
    # check docker is installed
    try:
        subprocess.check_call("docker --version", shell=True)
    except subprocess.CalledProcessError:
        # HOWTO use rootless docker: https://docs.docker.com/engine/security/rootless/
        # install cmd: curl -fsSL https://get.docker.com/rootless | sh
        print(
            "Docker is not installed, please refs: https://docs.docker.com/engine/security/rootless/"
        )
        raise
    user = getpass.getuser()
    uid = os.getuid()
    gid = os.getgid()
    print(f"User: {user}, UID: {uid} GID: {gid}")
    # build the docker image
    tag, dockerfile = get_docker_tag_and_dockerfile()
    build_cmd = f"docker build --build-arg USER_NAME={user} --build-arg USER_ID={uid} --build-arg USER_GID={gid} -t {tag} -f {dockerfile} ."
    print(f"Running: {build_cmd}")
    subprocess.check_call(build_cmd, shell=True)

    print(f"Running: {cmd} in docker")

    docker_args = "-it"
    envs = os.environ
    if "JENKINS_HOME" in envs:
        print("run in jenkins, set docker_args to -i")
        docker_args = "-i"
    if "CI_SERVER_NAME" in envs and envs["CI_SERVER_NAME"] == "GitLab":
        print("run in GitLab, set docker_args to -i")
        docker_args = "-i"

    docker_cmd = f"docker run --rm {docker_args}"
    map_to_envs = ["Commit_Id", "NINJA_JOBS", "MODELOPR_VER"]
    for env in map_to_envs:
        if env in envs:
            docker_cmd += f" -e {env}=${env}"
    # map user .ssh to docker
    host_ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    docker_ssh_dir = f"/home/{user}/.ssh"
    docker_cmd += f" -v {host_ssh_dir}:{docker_ssh_dir}"
    # map tmp to docker tmp
    docker_cmd += " -v /tmp:/tmp:rw"
    # map the current directory to docker
    docker_cmd += f" -v {os.getcwd()}:{os.getcwd()}:rw"

    # split the cmd by space, then find --repo_dir xxx, --build_dir xxx, --install_dir xxx
    # then map the directory to docker
    cmd_parts = cmd.split()
    for i, part in enumerate(cmd_parts):
        if part == "--repo_dir":
            docker_cmd += f" -v {cmd_parts[i+1]}:{cmd_parts[i+1]}:rw"
        if part == "--build_dir":
            docker_cmd += f" -v {cmd_parts[i+1]}:{cmd_parts[i+1]}:rw"
        if part == "--install_dir":
            docker_cmd += f" -v {cmd_parts[i+1]}:{cmd_parts[i+1]}:rw"
    # add user id and group id
    docker_cmd += f" -u {uid}:{gid}"
    # add last build cmd
    docker_cmd += f" {tag} /bin/bash -c '{cmd}'"
    print(f"Running: {docker_cmd}")
    subprocess.check_call(docker_cmd, shell=True)


if __name__ == "__main__":
    cwd = os.path.dirname(__file__)
    # change the current working directory to the directory of this file
    os.chdir(cwd)

    cmake_one_py = os.path.join(os.path.dirname(__file__), "cmake_one.py")
    # pass all arguments to the cmake_one.py
    cmd = f"python3 {cmake_one_py} {' '.join(sys.argv[1:])}"
    run_in_docker(cmd)
