from inspect import isfunction, ismodule, getmembers
from types import SimpleNamespace, ModuleType
from typing import Union, Any, Callable

from docopt import docopt as docopt_

from kapow import confirm


def docopt_handler(docs):
    def _docopt_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        ctx.cli_args = docopt_(docs, app.cli_args, version=app.version)
        return app, ctx

    return _docopt_handler


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