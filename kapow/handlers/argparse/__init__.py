from argparse import ArgumentParser
from argparse import Namespace
from types import SimpleNamespace
from typing import Any
from typing import Callable
from typing import Union
from kapow import confirm


def argparse_handler(parser: ArgumentParser) -> Callable:
    """
    Factory function that returns a kapow handler function to parse
    an application's cli arguments.

    :param parser: an argparser.ArgumentParser object.
    :return: handler function

    """

    def _argparse_handler(app: "Application", ctx: Union[SimpleNamespace, Any]):
        ctx.cli_args = parser.parse_args(app.cli_args)
        return app, ctx

    return _argparse_handler


def argparse_command_finder(app: "Application", ctx: Union[SimpleNamespace, Any]):
    """
    For argparse cli parsing, the convention is to assign the command as part of
    the cli definition by adding a default "command" value:

        command_parser.set_defaults(command=command_parser)

    So, "finding" the command in this case is just a case of passing the defined
    "command" variable.

    :param app: Application object
    :param ctx: context object
    :return: Application, context

    """
    confirm.ctx_var(ctx, "cli_args", Namespace)
    app.command = ctx.cli_args.command
    return app, ctx
