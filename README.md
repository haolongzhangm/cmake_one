# cmake_one
## how to use
```
python3 run_in_docker.py --help
```
with run `run_in_docker.py` will auto prepare all needed env, for example, host env and toolchains
if you do not want to use docker, just run: `python3 cmake_one.py --help`
some example
```
(debug,remove old build,cross-Linux-riscv64)
python3 run_in_docker.py --remove_old_build --build_type Debug  --repo_dir test_repo/  cross_build --cross_build_target_os LINUX --cross_build_target_arch rv64gcv

(cross-Linux-aarch64)
python3 run_in_docker.py cross_build --cross_build_target_os LINUX --cross_build_target_arch aarch64

(cross-Android-aarch64)
python3 run_in_docker.py cross_build --cross_build_target_arch aarch64

(cross-ohos-aarch64)
python3 run_in_docker.py cross_build --cross_build_target_os OHOS --cross_build_target_arch aarch64

(host build)
python3 run_in_docker.py host_build
```
## support progress
- [x] (LINUX) host
- [x] (LINUX) cross android (aarch64,aarch32)
- [x] (LINUX) cross OHOS (aarch64)
- [x] (LINUX) cross LINUX(aarch64,aarch32,RISCV64-RVV,RISCV64-NO-RVV)
- [x] (LINUX) cross WINDOWS-X64-X86-AARCH64-AARCH32
- [ ] (MACOS) host  WINDOWS-X64-AARCH64
- [ ] (MACOS) cross IOS
