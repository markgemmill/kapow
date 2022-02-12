"""
Usage:
  dieder run [--name=NAME]

Options:
  --name=NAME    Say hello to this person. [default: buddy]
  -h --help      Show this help message.
  -v --version   Show app version.

"""
from kapow.console import console
from kapow.appdirs import user_full_name


def run(ctx):
    name = ctx.cli_args["--name"]
    console.print(f"Hello [yellow]{name}[/yellow][red]!!![/red]"
