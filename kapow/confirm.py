import inspect
import sys
from pathlib import Path
from typing import Callable
from .errors import LaunchError


def expr(expression_result: bool, assertion_message: str):
    if expression_result is False:
        raise LaunchError(assertion_message)


def ctx_var(ctx, path: str, var_type):
    var_path = []
    root = ctx
    for var in path.split("."):
        var_path.append(var)
        root = getattr(root, var, None)
        if not root:
            raise LaunchError(
                f"Context missing expected value at: {'.'.join(var_path)}."
            )
    if not isinstance(root, var_type):
        raise LaunchError(
            f"Expecting context variable {'.'.join(var_path)} to be type {var_type}. Found {type(root)}."
        )


def directory_exists(dirpath: Path):
    """
    Create the directories in the path if they do not exist.

    :param dirpath:
    """
    if dirpath.is_file():
        dirpath = dirpath.parent
    dirpath.mkdir(parents=True, exist_ok=True)


def _assert_callable(handler: Callable):
    if not callable(handler):
        raise LaunchError(f"Provided object is not callable: {handler}.")


def _assert_signature(handler: Callable, expect: int = 2):
    _assert_callable(handler)
    signature: inspect.Signature = inspect.signature(handler)
    param_names = signature.parameters.keys()
    param_cnt = len(param_names)
    if param_cnt != expect:
        argument = "argument" if param_cnt == 1 else "arguments"
        raise LaunchError(
            f"A Launch handler callable must have 2 arguments (app, ctx). `{handler.__name__}` has {param_cnt} {argument}."
        )


def handler_func(handler: Callable):
    _assert_signature(handler, expect=2)


def error_func(handler: Callable):
    _assert_signature(handler, expect=3)


def command_func(handler: Callable):
    _assert_signature(handler, expect=1)
