from typing import Union, Callable, ClassVar
from types import SimpleNamespace
from . import handlers


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
        appdir_handler: Union[bool, Callable, None] = True,
        config_handler: Union[bool, Callable, None] = True,
        logging_config_handler: Union[bool, Callable, None] = True,
        command_handler: Union[bool, Callable, None] = True,
        error_handler: Union[Callable, None] = None,
        execute_handler: Union[Callable, None] = None,
        **kwargs
    ):
        self.name = name
        self.version = version
        self.context_class = context_class
        self.execute_handler = handlers.execute_handler
        self.error_handler = handlers.error_handler
        self._handlers = {}
        self._execution_order = []

        self._add_handler("cli_handler", cli_handler, handlers.cli_handler)
        self._add_handler("appdir_handler", appdir_handler, handlers.appdir_handler)
        self._add_handler("config_handler", config_handler, handlers.config_handler)
        self._add_handler("logging_config_handler", logging_config_handler, handlers.logging_config_handler)
        self._add_handler("command_handler", command_handler, handlers.command_handler)

        # special case
        self._add_handler("error_handler", error_handler, handlers.error_handler)
        self._add_handler("execute_handler", execute_handler, handlers.execute_handler)

        for name, handler in kwargs.items():
            self._add_handler(name, handler)

    def _add_handler(self, name, handler, default=None):

        if name == "execute_handler" and handler is not None:
            self.execute_handler = handler
            return

        if name == "error_handler" and handler is not None:
            self.error_handler = handler
            return

        if handler is None:
            return

        if handler is True:
            self._handlers[name] = default
            self._execution_order.append(handler)

        elif callable(handler):
            index = 0
            if name.startswith("before_"):
                name = name.replace("before_", "")
                index = -1
            elif name.startswith("after_"):
                name = name.replace("after_", "")
                index = 1

            if name not in self._handlers or name not in self._execution_order:
                raise Exception(f"No such handler: {name}")

            # TODO: need to verify index is not out of range
            insert_at = self._execution_order.index(name) + index

            self._handlers[name] = handler
            self._execution_order.insert(insert_at, handler)

    @property
    def main(self):
        return self.execute_handler(self)
