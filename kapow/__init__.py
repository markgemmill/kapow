import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Callable
from typing import ClassVar
from typing import Union
import kapow.handlers.core
from . import confirm
from . import handlers
from .errors import LaunchError

__version__ = "0.2.1"


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
        cli_handler: Union[bool, Callable, None] = True,
        env_handler: Union[bool, Callable, None] = True,
        appdir_handler: Union[bool, Callable, None] = True,
        config_handler: Union[bool, Callable, None] = True,
        context_handler: Union[bool, Callable, None] = True,
        logging_config_handler: Union[bool, Callable, None] = True,
        command_finder: Union[bool, Callable, None] = True,
        error_handler: Union[Callable, None] = None,
        main_factory: Union[Callable, None] = None,
        **kwargs,
    ):
        self.name = name
        self.version = version
        self.context_class = context_class
        # these handlers are mandatory
        self.main_factory = kapow.handlers.core.main_factory
        self.error_handler = kapow.handlers.core.error_handler

        self._handlers = {}
        self._execution_order = []

        self._add_handler("cli_handler", cli_handler, kapow.handlers.core.cli_handler)
        self._add_handler("env_handler", env_handler, kapow.handlers.core.env_handler)
        self._add_handler(
            "appdir_handler", appdir_handler, kapow.handlers.core.appdir_handler
        )
        self._add_handler(
            "config_handler",
            config_handler,
            kapow.handlers.core.config_handler_factory(),
        )
        self._add_handler(
            "context_handler", context_handler, kapow.handlers.core.context_handler
        )
        self._add_handler(
            "logging_config_handler",
            logging_config_handler,
            kapow.handlers.core.logging_config_factory(),
        )
        self._add_handler(
            "command_handler", command_finder, kapow.handlers.core.command_finder
        )

        # special case
        self._add_handler(
            "error_handler", error_handler, kapow.handlers.core.error_handler
        )
        self._add_handler(
            "main_factory", main_factory, kapow.handlers.core.main_factory
        )

        for name, handler in kwargs.items():
            if name.startswith("before_") or name.startswith("after_"):
                self._add_handler(name, handler)

        # for testing purposes
        if "cli_args" in kwargs:
            self._cli_args = kwargs["cli_args"]

    def _add_handler(self, name, handler, default=None):

        # do not load the handler
        if handler is None:
            return

        # load the default handler
        if handler is True:
            if not default:
                raise LaunchError("Using True requires a default handler.")
            self._handlers[name] = default
            self._execution_order.append(name)
            return

        if name == "error_handler" and handler is not None:
            confirm.error_func(handler)
            self.error_handler = handler
            return

        if name == "main_factory" and handler is not None:
            confirm.command_func(handler)
            self.main_factory = handler
            return

        confirm.handler_func(handler)

        # insert a user defined handler - before or after the named standard handler
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
            return

        # load the default handler
        self._handlers[name] = handler
        self._execution_order.append(name)

    @property
    def cli_args(self):
        if hasattr(self, "_cli_args"):
            return self._cli_args
        return sys.argv[1:]

    @property
    def main(self) -> Callable:
        """

        :return: main function
        """
        return self.main_factory(self)
