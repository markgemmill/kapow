from .. import Application
from ..handlers import docopt as dopt
from . import commands

app = Application(
    name="kapow",
    version="__version__",
    cli_handler=dopt.docopt_handler(commands.__doc__),
    config_handler=None,
    logging_config_handler=None,
    context_handler=None,
    command_finder=dopt.docopt_command_finder(commands),
)

main = app.main

