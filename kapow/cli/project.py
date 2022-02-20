import shutil
from importlib.resources import read_text
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
import tomlkit
from kapow import __version__
from kapow.console import console
from . import resources


class GenerateContext(Protocol):
    project_dir: Path


def file_from_template(ctx, filepath, resource_name):
    template = read_text(resources, resource_name)
    filepath.write_text(
        template.format(
            appname=ctx.project_name,
        )
    )


def create_poetry_pyproject(ctx: GenerateContext, pyproject_file: Path):
    doc = tomlkit.document()

    poetry = tomlkit.table()
    poetry["name"] = ctx.project_name
    poetry["version"] = "0.1.0"
    poetry["description"] = ""

    author = ""
    if ctx.author_name:
        author = ctx.author_name
    if ctx.author_email:
        author += f" <{ctx.author_email}>"

    poetry["authors"] = [author.strip()]

    deps = tomlkit.table()
    deps["python"] = "^3.9"
    deps["tomlkit"] = "^0.9.2"
    deps["docopt-ng"] = "^0.7.2"
    deps["rich"] = "^11.2"
    deps["kapow"] = f"^{__version__}"

    build_system = tomlkit.table()
    build_system["requires"] = ["poetry-core>=1.0.0"]
    build_system["build-backend"] = "poetry.core.masonry.api"

    scripts = tomlkit.table()
    scripts[ctx.project_name] = f"{ctx.project_name}.cli:main"

    doc["tool"] = tool = tomlkit.table()

    tool["poetry"] = poetry
    tool["poetry"]["dependencies"] = deps
    tool["poetry"]["scripts"] = scripts

    doc["build-system"] = build_system

    pyproject_file.write_text(tomlkit.dumps(doc))


def generate(ctx: GenerateContext):

    if ctx.project_dir.exists() and [f for f in ctx.project_dir.iterdir()]:
        console.print("\n[red]The project directory is not empty.[/red]")
        console.print("Select a new or empty directory when creating a project.\n")
        return

    with TemporaryDirectory() as root_dir:

        src_dir = Path(root_dir)

        if ctx.src_dir:
            src_dir = Path(root_dir, "src")

        src_dir = Path(src_dir, ctx.project_name)
        src_dir.mkdir(parents=True, exist_ok=True)

        # define project files
        readme_file = Path(root_dir, "README.md")
        pyproject_file = Path(root_dir, "pyproject.toml")
        init_py = Path(src_dir, "__init__.py")
        cli_file = Path(src_dir, "cli.py")
        commands_file = Path(src_dir, "commands.py")

        # generate file content
        create_poetry_pyproject(ctx, pyproject_file)
        file_from_template(ctx, init_py, "init.txt")

        if ctx.cli_parser == "docopt":
            file_from_template(ctx, cli_file, "cli.txt")
            file_from_template(ctx, commands_file, "commands.txt")
        elif ctx.cli_parser == "argparse":
            file_from_template(ctx, cli_file, "argparse_cli.txt")
            file_from_template(ctx, commands_file, "argparse_commands.txt")

        readme_file.touch()

        if not ctx.project_dir.exists():
            ctx.project_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(root_dir, ctx.project_dir, dirs_exist_ok=True)
