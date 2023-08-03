import pathlib
import platform
import argparse
import importlib.resources as res

project_version = (
    pathlib.Path("pyproject.toml")
    .read_text(encoding="utf-8")
    .split("version = ")[1]
    .split("\n")[0]
    .strip('"')
)

parser = argparse.ArgumentParser()
parser.add_argument("--version", action="store_true")
parser.add_argument("--name", action="store_true")
parser.add_argument("--buildname", action="store_true")
parser.add_argument("--package-tools", default="")
parser.add_argument("--beta", default="")
parser.add_argument("--replace-playwright-path", action="store_true")
parser.add_argument("--group", default="")

p = parser.parse_args()

package_tools = p.package_tools
beta_hash = f".beta.{p.beta}" if p.beta else ""
build_suffix = ".bin" if package_tools == "nuitka" else ""
group = p.group

if platform.system() == "Windows":
    file_name = f"bbot-{group}-{project_version}{beta_hash}-windows-{package_tools}.exe"
    build_name = "main.exe"
else:
    file_name = f"bbot-{group}-{project_version}{beta_hash}-ubuntu-{package_tools}"
    build_name = f"main{build_suffix}"


if p.version:
    print(f"{project_version}{beta_hash}")
elif p.name:
    print(file_name)
elif p.buildname:
    print(build_name)
elif p.replace_playwright_path:
    import playwright

    with res.path(playwright, "driver") as playwright_package_path:
        path = list(
            playwright_package_path.joinpath("package", ".local-browsers").glob(
                "chromium-*/chrome*"
            )
        )[0]
        chrome_relative_path = path.relative_to(pathlib.Path(playwright_package_path).parent)
        print(chrome_relative_path)
        yml_path = pathlib.Path("nuitka-full.yml")
        yml_path.write_text(
            yml_path.read_text().replace("$PLAYWRIGHT", str(chrome_relative_path))
        )
