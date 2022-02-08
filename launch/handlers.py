from types import SimpleNamespace
from typing import Callable, Union, Any


def cli_handler(app: 'Application', ctx: Union[SimpleNamespace, Any]):
    ctx.execution = []
    ctx.execution.append("CLI HANDLER")


def appdir_handler(app: 'Application', ctx: Union[SimpleNamespace, Any]):
    ctx.execution.append("APPDIR HANDLER")


def config_handler(app: 'Application', ctx: Union[SimpleNamespace, Any]):
    ctx.execution.append("CONFIG HANDLER")


def logging_config_handler(app: 'Application', ctx: Union[SimpleNamespace, Any]):
    ctx.execution.append("LOGGING CONFIG HANDLER")


def error_handler(app: 'Application', ctx: Union[SimpleNamespace, Any], error):
    """
    This is a special case handler that is called as the
    top level exception handler.

    In addition to the application and context arguments, it also takes an error argument.

    :param app: Application object
    :param ctx:  Context object
    :param error: Exception object
    :return: None

    """
    print(f"{app.name} failed: {error}")


def execute_handler(app: 'Application') -> Callable:
    """
    This is a special case handler that is the final function called
    in the launcher handler pipeline. It is responsible for creating
    the application's main function, which runs the application.

    It only takes an application reference, and is responsible for
    creating the context object, and for handling the top-level
    errors.

    In practice user's should not be overriding the execute handler.

    :param app: Application
    :return:
    """
    def _execution():
        context = app.context_class()
        for handler_key in app._execution_order:
            handler = app._handlers[handler_key]
            handler(app, context)
        command = app.command
        try:
            command(context)
        except Exception as ex:
            app.error_handler(app, context, ex)

    return _execution
