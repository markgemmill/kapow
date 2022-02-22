import pytest
from common import Handler
import kapow.handlers.core
from kapow import Application
from kapow import LaunchError
from kapow.handlers.docopt import docopt_handler
from tests.common import CLI_DOCS


def test_application_add_handler_invalid_function():
    messages = []

    def dud_handler(foo):
        pass

    with pytest.raises(LaunchError) as ex:
        app = Application(
            "test",
            "0.1.0",
            cli_handler=Handler("CLI", messages),
            env_handler=dud_handler,
        )

    assert (
        str(ex.value)
        == "A Launch handler callable must have 2 arguments (app, ctx). `dud_handler` has 1 argument."
    )


def test_application_add_handler_invalid_default():
    messages = []

    def dud_handler(foo):
        pass

    with pytest.raises(LaunchError) as ex:
        app = Application(
            "test",
            "0.1.0",
            cli_handler=Handler("CLI", messages),
            before_env_handler=True,
        )

    assert str(ex.value) == "Using True requires a default handler."


def test_application_add_handler_insert_before_non_existing_handler():
    messages = []

    def dud_handler(foo):
        pass

    with pytest.raises(LaunchError) as ex:
        app = Application(
            "test",
            "0.1.0",
            cli_handler=Handler("CLI", messages),
            before_bogus_handler=Handler("BOGUS", messages),
        )

    assert (
        str(ex.value)
        == "Expecting to insert `before_bogus_handler` relative to `bogus_handler`, but `bogus_handler` does not exist."
    )


def test_application_docopt_cli_handler():

    messages = []

    def capture_cli_args(app, ctx, messages):
        for key, val in ctx.cli_args.items():
            messages.append(f"CLI> {key}: {val}")

    app = Application(
        "test",
        "0.1.0",
        cli_handler=docopt_handler(CLI_DOCS),
        env_handler=Handler("ENV", messages),
        appdir_handler=Handler("APPDIR", messages),
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_finder=Handler("CMD", messages).command(),
        error_handler=Handler("ERR", messages).error_handler(),
        after_cli_handler=Handler("CLI ARGS", messages, func=capture_cli_args),
    )

    app.initialize(cli_args="run --debug".split(" "))

    app.main()


    assert messages[0] == "CLI ARGS"
    assert messages[1] == "CLI> run: True"
    assert messages[2] == "CLI> --debug: True"
    assert messages[3] == "CLI> --help: False"
    assert messages[4] == "CLI> --version: False"
    assert messages[5] == "ENV"


def alt_execute_handler(app):
    def _execution():
        nonlocal app
        context = app.context_class()
        handler = app._handlers["command_finder"]
        app, context = handler(app, context)

        try:
            app.command(context)
        except Exception as ex:
            kapow.handlers.core.error_handler(app, context, ex)

    return _execution


def test_application_alt_execute_handler():

    messages = []

    app = Application(
        "test",
        "0.1.0",
        command_finder=Handler("CMD", messages).command(),
        main_factory=alt_execute_handler,
    )

    app.main()

    assert messages[0] == "CMD HANDLER"
    assert messages[1] == "CMD CALLED"
