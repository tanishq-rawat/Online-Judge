import os
import tempfile
import textwrap
import time
from typing import Literal, Dict, Any

import docker
from docker.errors import ContainerError, APIError

ResultStatus = Literal["OK", "TLE", "RE", "CE", "INTERNAL_ERROR"]

class PySandboxExecutor:
    def __init__(
        self,
        image: str = "oj-python-runner",
        time_limit_sec: float = 2.0,
        memory_limit_mb: int = 256,
        cpu_cores: float = 1.0,
    ):
        self.image = image
        self.time_limit_sec = time_limit_sec
        self.memory_limit_mb = memory_limit_mb
        self.cpu_cores = cpu_cores

        # Force correct socket to avoid http+docker issues
        self.client = docker.DockerClient(base_url="unix:///var/run/docker.sock")

    def run(
        self,
        source_code: str,
        stdin_data: str = "",
    ) -> Dict[str, Any]:

        source_code = textwrap.dedent(source_code)

        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "main.py")
            input_path = os.path.join(tmpdir, "input.txt")

            with open(code_path, "w", encoding="utf-8") as f:
                f.write(source_code)

            # Write stdin data to a file
            with open(input_path, "w", encoding="utf-8") as f:
                # Ensure input ends with newline
                if stdin_data and not stdin_data.endswith('\n'):
                    stdin_data += '\n'
                f.write(stdin_data)

            volumes = {
                tmpdir: {
                    "bind": "/workspace",
                    "mode": "rw",
                }
            }

            # Use shell redirection to feed input
            command = ["sh", "-c", "python main.py < input.txt"]

            mem_limit = f"{self.memory_limit_mb}m"
            nano_cpus = int(self.cpu_cores * 1_000_000_000)

            start_time = time.time()
            container = None

            try:
                container = self.client.containers.run(
                    image=self.image,
                    command=command,
                    working_dir="/workspace",
                    volumes=volumes,
                    network_disabled=True,
                    mem_limit=mem_limit,
                    nano_cpus=nano_cpus,
                    detach=True,
                    stdout=True,
                    stderr=True,
                    tty=False,
                )

                # Poll container status
                while True:
                    container.reload()
                    state = container.attrs["State"]
                    if state["FinishedAt"] not in ("", None, "0001-01-01T00:00:00Z"):
                        break

                    if time.time() - start_time > self.time_limit_sec:
                        container.kill()
                        return {
                            "status": "TLE",
                            "stdout": "",
                            "stderr": "",
                            "exit_code": None,
                            "time_sec": round(time.time() - start_time, 4),
                        }

                    time.sleep(0.05)

                exit_code = state["ExitCode"]
                stdout_logs = container.logs(stdout=True, stderr=False).decode("utf-8", "replace")
                stderr_logs = container.logs(stdout=False, stderr=True).decode("utf-8", "replace")

                status = "OK" if exit_code == 0 else "RE"

                return {
                    "status": status,
                    "stdout": stdout_logs,
                    "stderr": stderr_logs,
                    "exit_code": exit_code,
                    "time_sec": round(time.time() - start_time, 4),
                }

            except Exception as e:
                return {
                    "status": "INTERNAL_ERROR",
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": None,
                    "time_sec": round(time.time() - start_time, 4),
                }
            finally:
                if container is not None:
                    try:
                        container.remove(force=True)
                    except:
                        pass

class CppSandboxExecutor:
    def __init__(
        self,
        image: str = "oj-cpp-runner",
        time_limit_sec: float = 2.0,
        memory_limit_mb: int = 256,
        cpu_cores: float = 1.0,
        compile_time_limit_sec: float = 10.0,
    ):
        self.image = image
        self.time_limit_sec = time_limit_sec
        self.memory_limit_mb = memory_limit_mb
        self.cpu_cores = cpu_cores
        self.compile_time_limit_sec = compile_time_limit_sec

        self.client = docker.DockerClient(base_url="unix:///var/run/docker.sock")

    def run(
        self,
        source_code: str,
        stdin_data: str = "",
    ) -> Dict[str, Any]:

        source_code = textwrap.dedent(source_code)

        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = os.path.join(tmpdir, "main.cpp")
            input_path = os.path.join(tmpdir, "input.txt")

            with open(code_path, "w", encoding="utf-8") as f:
                f.write(source_code)

            # Write stdin data to a file
            with open(input_path, "w", encoding="utf-8") as f:
                if stdin_data and not stdin_data.endswith('\n'):
                    stdin_data += '\n'
                f.write(stdin_data)

            volumes = {
                tmpdir: {
                    "bind": "/workspace",
                    "mode": "rw",
                }
            }

            mem_limit = f"{self.memory_limit_mb}m"
            nano_cpus = int(self.cpu_cores * 1_000_000_000)

            # Step 1: Compile the C++ code
            compile_result = self._compile(volumes, mem_limit, nano_cpus)
            if compile_result["status"] != "OK":
                return compile_result

            # Step 2: Execute the compiled binary
            return self._execute(volumes, mem_limit, nano_cpus)

    def _compile(
        self,
        volumes: Dict,
        mem_limit: str,
        nano_cpus: int,
    ) -> Dict[str, Any]:
        """Compile the C++ source code."""
        
        # Compile command: g++ with optimizations and warnings
        compile_command = [
            "sh", "-c",
            "g++ -O2 -std=c++17 -o main main.cpp 2>&1"
        ]

        start_time = time.time()
        container = None

        try:
            container = self.client.containers.run(
                image=self.image,
                command=compile_command,
                working_dir="/workspace",
                volumes=volumes,
                network_disabled=True,
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                detach=True,
                stdout=True,
                stderr=True,
                tty=False,
            )

            # Poll container status for compilation
            while True:
                container.reload()
                state = container.attrs["State"]
                if state["FinishedAt"] not in ("", None, "0001-01-01T00:00:00Z"):
                    break

                if time.time() - start_time > self.compile_time_limit_sec:
                    container.kill()
                    return {
                        "status": "CE",
                        "stdout": "",
                        "stderr": "Compilation timed out",
                        "exit_code": None,
                        "time_sec": round(time.time() - start_time, 4),
                    }

                time.sleep(0.05)

            exit_code = state["ExitCode"]
            output = container.logs(stdout=True, stderr=True).decode("utf-8", "replace")

            if exit_code != 0:
                return {
                    "status": "CE",
                    "stdout": "",
                    "stderr": output,
                    "exit_code": exit_code,
                    "time_sec": round(time.time() - start_time, 4),
                }

            return {
                "status": "OK",
                "compile_time_sec": round(time.time() - start_time, 4),
            }

        except Exception as e:
            return {
                "status": "INTERNAL_ERROR",
                "stdout": "",
                "stderr": f"Compilation error: {str(e)}",
                "exit_code": None,
                "time_sec": round(time.time() - start_time, 4),
            }
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except:
                    pass

    def _execute(
        self,
        volumes: Dict,
        mem_limit: str,
        nano_cpus: int,
    ) -> Dict[str, Any]:
        """Execute the compiled binary."""
        
        # Execute with input redirection
        execute_command = ["sh", "-c", "./main < input.txt"]

        start_time = time.time()
        container = None

        try:
            container = self.client.containers.run(
                image=self.image,
                command=execute_command,
                working_dir="/workspace",
                volumes=volumes,
                network_disabled=True,
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                detach=True,
                stdout=True,
                stderr=True,
                tty=False,
            )

            # Poll container status for execution
            while True:
                container.reload()
                state = container.attrs["State"]
                if state["FinishedAt"] not in ("", None, "0001-01-01T00:00:00Z"):
                    break

                if time.time() - start_time > self.time_limit_sec:
                    container.kill()
                    return {
                        "status": "TLE",
                        "stdout": "",
                        "stderr": "",
                        "exit_code": None,
                        "time_sec": round(time.time() - start_time, 4),
                    }

                time.sleep(0.05)

            exit_code = state["ExitCode"]
            stdout_logs = container.logs(stdout=True, stderr=False).decode("utf-8", "replace")
            stderr_logs = container.logs(stdout=False, stderr=True).decode("utf-8", "replace")

            status = "OK" if exit_code == 0 else "RE"

            return {
                "status": status,
                "stdout": stdout_logs,
                "stderr": stderr_logs,
                "exit_code": exit_code,
                "time_sec": round(time.time() - start_time, 4),
            }

        except Exception as e:
            return {
                "status": "INTERNAL_ERROR",
                "stdout": "",
                "stderr": str(e),
                "exit_code": None,
                "time_sec": round(time.time() - start_time, 4),
            }
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except:
                    pass