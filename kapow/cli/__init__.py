import kapow.handlers.docopt
from .. import Application
from .. import handlers
from . import commands

app = Application(
    name="kapow",
    version="__version__",
    cli_handler=kapow.handlers.docopt.docopt_handler(commands.__doc__),
    pre_config_handler=None,
    config_handler=None,
    post_config_handler=None,
    pre_logging_config_handler=None,
    logging_config_handler=None,
    context_handler=None,
    command_finder=kapow.handlers.docopt.docopt_command_finder(commands),
)

main = app.main
