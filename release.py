import sys
import pathlib
import platform

project_version = (
    pathlib.Path("pyproject.toml")
    .read_text()
    .split("version = ")[1]
    .split("\n")[0]
    .strip('"')
)
if platform.system() == "Windows":
    file_name = f"bbot-windows-{project_version}.exe"
    build_name = "main.exe"
else:
    file_name = f"bbot-ubuntu-{project_version}"
    build_name = "main"


if sys.argv[1] == "--version":
    print(project_version)
elif sys.argv[1] == "--name":
    print(file_name)
elif sys.argv[1] == "--buildname":
    print(build_name)
