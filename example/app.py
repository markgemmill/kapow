import logging
from launch import Application
from launch import handlers

log = logging.getLogger("appy")

CLI = """appy

Usage:
  appy run [--debug]
  appy error
  appy --help
  appy --version
  
Options:
  --debug        Turn on debug mode.
  --help -h      Show this help message.
  --version -v   Show appy version.

"""


def run(ctx):
    log.debug("appy is running!")


def error(ctx):
    raise Exception("This is all wrong!")


def validate_configuration(config):
    assert "app" in config
    assert "debug" in config["app"]


def find_command(ctx):
    if ctx.cli_args["run"] is True:
        return run
    if ctx.cli_args["error"] is True:
        return error


app = Application(
    name="appy",
    version="0.1.0",
    cli_handler=handlers.docopt_handler(CLI),
    env_handler=None,
    pre_config_handler=handlers.pre_config_handler(handlers.default_config_builder),
    config_handler=handlers.config_handler,
    post_config_handler=handlers.post_config_handler(validate_configuration),
    command_handler=handlers.command_handler(find_command),
)

if __name__ == "__main__":
    app.initialize()
    app.main()
