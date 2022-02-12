import inspect
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Callable
from typing import ClassVar
from typing import Union
from . import handlers
from .console import Console, console

__version__ = "0.1.0"


class LaunchError(Exception):
    pass


class Application:
    """
    The Application object in essence is a specialized pipline manager.

    Every application requires a series of resources in order to run, many of which
    are common across all applications.

    The most simple scripts do not need anything other than a main function, but beyond that
    programs will typically need to pull in argument and options from the command line, configuration files,
    environment variable; define their execution environment and access to local resource; will want to configure logging;
    and finally select the appropriate entry function.

    Launch defines an ordered series of events:

    cli: parse and convert command line arguments
    environ variable: read in environment variables
    configuration: read configuration files or resource
    merge arguments: merge or override cli/environ/config arguments
    configure logging: set logging configurations
    select application's main function based on program cli/env/config
    define final error handling

    """

    def __init__(
        self,
        name: str,
        version: str,
        context_class: ClassVar = SimpleNamespace,
        console: Console = console,
        cli_handler: Union[bool, Callable, None] = True,
        env_handler: Union[bool, Callable, None] = True,
        appdir_handler: Union[bool, Callable, None] = True,
        pre_config_handler: Union[Callable, None] = None,
        config_handler: Union[bool, Callable, None] = True,
        post_config_handler: Union[Callable, None] = None,
        context_handler: Union[bool, Callable, None] = True,
        pre_logging_config_handler: Union[bool, Callable, None] = True,
        logging_config_handler: Union[bool, Callable, None] = True,
        command_handler: Union[bool, Callable, None] = True,
        error_handler: Union[Callable, None] = None,
        execute_handler: Union[Callable, None] = None,
        **kwargs,
    ):
        self.name = name
        self.version = version
        self.context_class = context_class
        self.console = console
        self.execute_handler = handlers.execute_handler
        self.error_handler = handlers.error_handler
        self._handlers = {}
        self._execution_order = []

        self._add_handler("cli_handler", cli_handler, handlers.cli_handler)
        self._add_handler("env_handler", env_handler, handlers.env_handler)
        self._add_handler("appdir_handler", appdir_handler, handlers.appdir_handler)
        self._add_handler("pre_config_handler", pre_config_handler)
        self._add_handler("config_handler", config_handler, handlers.config_handler)
        self._add_handler("post_config_handler", post_config_handler)
        self._add_handler("context_handler", context_handler, handlers.context_handler)
        self._add_handler(
            "pre_logging_config_handler",
            pre_logging_config_handler,
            handlers.pre_logging_config_handler(
                handlers.default_logging_config_builder
            ),
        )
        self._add_handler(
            "logging_config_handler",
            logging_config_handler,
            handlers.logging_config_handler,
        )
        self._add_handler("command_handler", command_handler, handlers.command_handler)

        # special case
        self._add_handler("error_handler", error_handler, handlers.error_handler)
        self._add_handler("execute_handler", execute_handler, handlers.execute_handler)

        for name, handler in kwargs.items():
            self._add_handler(name, handler)

    def assert_expr(self, expression_result: bool, assertion_message: str):
        if expression_result is False:
            raise LaunchError(assertion_message)

    def assert_ctx_var(self, ctx, path, var_type):
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

    def assert_dir(self, dirpath: Path):
        if dirpath.is_file():
            dirpath = dirpath.parent
        dirpath.mkdir(parents=True, exist_ok=True)

    def assert_handler(self, handler, arg_len=2):
        handler_sig: inspect.Signature = inspect.signature(handler)
        param_cnt = len(handler_sig.parameters.keys())
        if param_cnt != arg_len:
            raise LaunchError(
                f"A Launch handler callable must have {arg_len} arguments. `{handler.__name__}` has {param_cnt} arguements."
            )

    def _add_handler(self, name, handler, default=None):

        if handler is None:
            return

        # there are x options for a handler
        # a. native handler => value is true
        if handler is True:
            if not default:
                raise LaunchError("Using True requires a default handler.")
            self._handlers[name] = default
            self._execution_order.append(name)
            return

        if name == "error_handler" and handler is not None:
            self.assert_handler(handler, 3)
            self.error_handler = handler
            return

        if name == "execute_handler" and handler is not None:
            self.assert_handler(handler, 1)
            self.execute_handler = handler
            return

        self.assert_handler(handler)

        # c. insert handler => value is callable named before/after....
        if name.startswith("before_") or name.startswith("after_"):

            index = 0

            if name.startswith("before_"):
                relative_to_name = name.replace("before_", "")

            elif name.startswith("after_"):
                relative_to_name = name.replace("after_", "")
                index = 1

            if (
                relative_to_name not in self._handlers
                or relative_to_name not in self._execution_order
            ):
                raise LaunchError(
                    f"Expecting to insert `{name}` relative to `{relative_to_name}`, but `{relative_to_name}` does not exist."
                )

            insert_at = self._execution_order.index(relative_to_name)

            self._handlers[name] = handler
            self._execution_order.insert(insert_at + index, name)

        # b. override handler => value is callable with existing name
        elif callable(handler):
            self._handlers[name] = handler
            self._execution_order.append(name)

    def initialize(self, cli_args=None):
        """
        The primary use-case for initialize method is to provide a step
        where we could easily pass cli arguments for testing.

        :param cli_args: list of string values
        :return: None
        """
        # TODO: do we really need this? We could just override self.cli_args
        #  when we're testing
        self.cli_args = cli_args if cli_args else sys.argv[1:]

    @property
    def main(self) -> Callable:
        """

        :return: main function
        """
        return self.execute_handler(self)
