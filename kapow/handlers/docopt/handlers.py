from inspect import getmembers
from inspect import isfunction
from inspect import ismodule
from types import ModuleType
from types import SimpleNamespace
from typing import Any
from typing import Callable
from typing import Union
from docopt import docopt as docopt_
from kapow import confirm


def docopt_handler(docs: str) -> Callable:
    """
    Factory function that returns a kapow handler function to parse
    an applications cli arguments.

    :param docs: the docopt command line definition.
    :return: handler function

    """

    def _docopt_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        ctx.cli_args = docopt_(docs, app.cli_args, version=app.version)
        return app, ctx

    return _docopt_handler


def docopt_command_finder(cmd_obj: Union[ModuleType, Callable, SimpleNamespace]):
    """
    Factory function that returns a kapow handler function that scans an object
    (either a module or an object) for a command whose name matches a key in the
    parsed docopt cli arguments (a dict).

    `docopt` commands will be lower-case names with either a True or False value.

    If a function is supplied, it will be used as the command without any lookup.

    :param cmd_obj: a module, namespace object or a function.
    :return: handler function

    """

    def match_func_name_to_cli_cmd(func_name: str, cli_args: dict) -> bool:
        """
        Search for a key in cli_args. Return True if found.

        :param func_name: name of a function
        :param cli_args: docopt cli arg dict
        :return: True or False
        """
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
