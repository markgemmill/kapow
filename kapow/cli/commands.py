"""
Usage:
  kapow init PATH

Options:
  -h --help      Show this help message.
  -v --version   Show app version.

"""
from pathlib import Path
from types import SimpleNamespace
from rich.prompt import Confirm
from rich.prompt import Prompt
from ..appdirs import user_full_name
from ..console import console
from . import project


def init(ctx):
    ns = SimpleNamespace()

    ns.project_dir = Path(ctx.cli_args["PATH"]).resolve()

    pname = ns.project_dir.stem

    ns.project_name = Prompt.ask("Project name", default=pname)
    ns.author_name = Prompt.ask("Author name", default=user_full_name())
    ns.author_email = Prompt.ask("Author email", default="")
    ns.project_type = Prompt.ask(
        "Packaging", choices=["setup", "poetry"], default="poetry"
    )
    ns.src_dir = Confirm.ask("Use src dir?", default=False)
    ns.cli_parser = Prompt.ask(
        "CLI Parser", choices=["argparse", "docopt"], default="argparse"
    )

    console.print("\nProject details:")
    console.print(f"  name: [green]{ns.project_name}[/green]")
    console.print(f"  directory: [green]{ns.project_dir}[/green]")
    console.print(f"  project type: [green]{ns.project_type}[/green]")
    if ns.src_dir:
        console.print("  use src dir: [green]yes[/green]")
    else:
        console.print("  use src dir: [red]no[/red]")
    console.print(f"  cli parser: [green]{ns.cli_parser}[/green]")
    console.print()

    if Confirm.ask("Generate project"):
        project.generate(ns)
