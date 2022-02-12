import logging
import logging.config
from importlib.resources import read_text
from inspect import getmembers
from inspect import isfunction
from inspect import ismodule
from os import environ
from pathlib import Path
from pathlib import PosixPath
from pathlib import WindowsPath
from types import ModuleType
from types import SimpleNamespace
from typing import Any
from typing import Callable
from typing import Union
import tomlkit
from docopt import docopt
from tomlkit import comment
from tomlkit import document
from tomlkit import table
from . import confirm
from . import resources
from .appdirs import AppDirs
from .console import console


def cli_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    ctx.cli_args = app.cli_args
    return app, ctx


def docopt_handler(docs):
    def _docopt_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        ctx.cli_args = docopt(docs, app.cli_args, version=app.version)
        return app, ctx

    return _docopt_handler


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
    ctx.files.config = Path(ctx.dirs.app_home, f"{app.name}.config.ini")
    ctx.files.logging_config = Path(ctx.dirs.app_home, f"{app.name}.logging.ini")
    ctx.files.log_file = Path(ctx.dirs.log_dir, f"{app.name}.logs.txt")

    return app, ctx


def default_config_builder(ctx):
    doc = document()
    doc.add(comment("default toml configuration file"))
    app = table()
    app["debug"] = True
    app["wrk_dir"] = str(ctx.dirs.app_home / "wrk_dir")
    doc["app"] = app
    ctx.files.config.write_text(tomlkit.dumps(doc))


def pre_config_handler(config_builder):
    def _pre_config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        confirm.ctx_var(ctx, "files.config", (Path, PosixPath, WindowsPath))

        if not ctx.files.config.exists():
            config_builder(ctx)
        return app, ctx

    return _pre_config_handler


def config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    """
    Reads toml config file format.

    :param app:
    :param ctx:
    :return:
    """
    confirm.expr(
        ctx.files.config.exists(), f"Config file does not exist: {ctx.files.config}"
    )
    ctx.config = tomlkit.loads(ctx.files.config.read_text())
    return app, ctx


def post_config_handler(config_validator):
    """
    Using the provided config_validator, validate the config data.

    config_validator should raise a LaunchError indicating the issue with the config data.

    :param config_validator:
    :return: Application, Context

    """

    def _post_config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        config_validator(ctx.config)
        return app, ctx

    return _post_config_handler


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


def pre_logging_config_handler(logging_config_builder):
    def _pre_logging_config_handler(
        app: "Application", ctx: Union[SimpleNamespace, Any]
    ):
        confirm.ctx_var(ctx, "files.logging_config", (Path, PosixPath, WindowsPath))

        if not ctx.files.logging_config.exists():
            logging_config_builder(app, ctx)

        if not ctx.files.log_file.exists():
            ctx.files.log_file.write_text("")

        return app, ctx

    return _pre_logging_config_handler


def logging_config_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
    # TODO: we need an option for pointing to an alternative logging config file
    confirm.ctx_var(ctx, "files.logging_config", (Path, PosixPath, WindowsPath))

    logging.config.fileConfig(ctx.files.logging_config)
    app.log = logging.getLogger(app.name)

    return app, ctx


def command_handler(command_finder: Callable) -> Callable:
    def _command_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        app.command = command_finder(ctx)
        return app, ctx

    return _command_handler


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


# TODO: rename to main_handler?
def execute_handler(app: "Application") -> Callable:
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


def docopt_command_finder(cmd_obj: Union[ModuleType, Callable, SimpleNamespace]):
    def match_func_name_to_cli_cmd(func_name, cli_args):
        possible_names = [func_name]
        possible_names.append(func_name.replace("_", "."))
        possible_names.append(func_name.replace("_", "-"))
        for name in possible_names:
            if name in cli_args and cli_args[name] is True:
                return True
        return False

    def _docopt_command_finder(app, ctx):
        confirm.ctx_var(ctx, "cli_args", dict)

        if isfunction(cmd_obj) or callable(cmd_obj):
            app.command = cmd_obj

        elif ismodule(cmd_obj) or isinstance(cmd_obj, SimpleNamespace):
            functions = [f for f in getmembers(cmd_obj) if isfunction(f[1])]
            for func_name, func_obj in functions:
                if match_func_name_to_cli_cmd(func_name, ctx.cli_args):
                    app.command = func_obj
                    break

        return app, ctx

    return _docopt_command_finder
