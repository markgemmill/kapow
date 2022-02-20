import logging
from importlib.resources import read_text
from os import environ
from pathlib import Path
from pathlib import PosixPath
from pathlib import WindowsPath
from types import SimpleNamespace
from typing import Any
from typing import Callable
from typing import Union
import tomlkit
from tomlkit import comment
from tomlkit import document
from tomlkit import table
from kapow import confirm
from kapow import resources
from kapow.appdirs import AppDirs
from kapow.console import console


def cli_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    ctx.cli_args = app.cli_args
    return app, ctx


def env_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    env_name = f"{app.name.upper()}_"
    ctx.env_vars = {}
    for key, value in environ.items():
        if key.startswith(env_name):
            ctx.env_vars[key] = value
    return app, ctx


def appdir_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    appdirs = AppDirs(app.name)
    ctx.dirs = app.context_class()
    ctx.dirs.app_home = appdirs.user_data_dir
    ctx.dirs.log_dir = appdirs.user_log_dir
    ctx.current_user = appdirs.user_name.lower()

    confirm.directory_exists(ctx.dirs.app_home)
    confirm.directory_exists(ctx.dirs.log_dir)

    ctx.files = app.context_class()

    return app, ctx


def default_config_builder(ctx):
    doc = document()
    doc.add(comment("default toml configuration file"))
    app = table()
    app["debug"] = True
    app["wrk_dir"] = str(ctx.dirs.app_home / "wrk_dir")
    doc["app"] = app
    ctx.files.config.write_text(tomlkit.dumps(doc))


def default_cfg_writer(ctx):
    ctx.files.config.touch()


def default_cfg_validator(config):
    pass


def config_handler_factory(
    config_writer=default_cfg_writer, config_validator=default_cfg_validator
):
    def _config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):

        confirm.ctx_var(ctx, "files", (Path, PosixPath, WindowsPath))
        ctx.files.config = Path(ctx.dirs.app_home, f"{app.name}.config.ini")

        if not ctx.files.config.exists():
            config_writer(ctx)

        ctx.config = tomlkit.loads(ctx.files.config.read_text())

        config_validator(ctx.config)

        return app, ctx

    return _config_handler


def context_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    """
    The purpose of the context handler is to coerce the context object into
    a state for the application. This might involve merging cli and config
    arguments into single values, adding new variables based on those inputs,
    removing temporary values from the context object or re-writing to a new
    context object.

    :param app: Application
    :param ctx: Context
    :return: Application, Context
    """
    return app, ctx


def default_logging_config_builder(app, ctx):
    log_cfg_txt = read_text(resources, "logging.ini")
    ctx.files.logging_config.write_text(
        log_cfg_txt.format(logfile=ctx.files.log_file, appname=app.name)
    )


def logging_config_factory(logging_config_builder=default_logging_config_builder):
    def logging_config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        # TODO: we need an option for pointing to an alternative logging config file
        confirm.ctx_var(ctx, "files", (Path, PosixPath, WindowsPath))
        ctx.files.logging_config = Path(ctx.dirs.app_home, f"{app.name}.logging.ini")
        ctx.files.log_file = Path(ctx.dirs.log_dir, f"{app.name}.logs.txt")

        if not ctx.files.logging_config.exists():
            logging_config_builder(app, ctx)

        if not ctx.files.log_file.exists():
            ctx.files.log_file.write_text("")

        logging.config.fileConfig(ctx.files.logging_config)
        app.log = logging.getLogger(app.name)

        return app, ctx

    return logging_config_handler


def command_finder(command_finder: Callable) -> Callable:
    def _command_finder(app: "Application", ctx: Union[SimpleNamespace, Any]):
        app.command = command_finder(ctx)
        return app, ctx

    return _command_finder


def error_handler(app: "Application", ctx: Union[SimpleNamespace, Any], error):
    """
    This is a special case handler that is called as the
    top level exception handler. It is called from within the `execute_handler`.

    In addition to the application and context arguments, it also takes an error argument.

    :param app: Application object
    :param ctx:  Context object
    :param error: Exception object
    :return: None

    """
    import traceback
    from rich import box
    from rich.panel import Panel

    console.print(
        f"\n  [green]{app.name}[/green] failed with error: [red]{error}[/red]\n"
    )
    console.print(Panel(traceback.format_exc().strip(), box.SQUARE, highlight=True))


def main_factory(app: "Application") -> Callable:
    """
    This is a special case handler that is the final function called
    in the kapower pipeline. It is responsible for creating
    the application's main function, which runs the application.

    It only takes an application reference, and is responsible for
    creating the context object, and for handling the top-level
    errors.

    In practice user's should not be overriding the execute handler.

    :param app: Application
    :return:
    """

    def _main():
        nonlocal app
        context = app.context_class()
        for handler_key in app._execution_order:
            try:
                handler = app._handlers[handler_key]
                app, context = handler(app, context)
            except Exception as ex:
                app.error_handler(app, context, ex)
                return

        try:
            app.command(context)
        except Exception as ex:
            app.error_handler(app, context, ex)

    return _main
