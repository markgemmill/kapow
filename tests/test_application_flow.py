from common import Handler
from kapow import Application


def test_application_():
    def command_handler_func(app, ctx):
        def command(ctx):
            print("running command...")

        app.command = command
        return app, ctx

    app = Application("test", "0.1.0", command_handler=command_handler_func)
    assert app.name == "test"
    assert app.version == "0.1.0"
    app.main()


def test_application_standard_execution_flow():
    messages = []
    app = Application(
        "test",
        "0.1.0",
        cli_handler=Handler("CLI", messages),
        env_handler=Handler("ENV", messages),
        appdir_handler=Handler("APPDIR", messages),
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        pre_logging_config_handler=Handler("PRE-LOGGING", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_handler=Handler("CMD", messages).command(),
        error_handler=Handler("ERR", messages).error_handler(),
    )
    app.main()

    assert messages == [
        "CLI",
        "ENV",
        "APPDIR",
        "CONFIG",
        "CONTEXT",
        "PRE-LOGGING",
        "LOGGING",
        "CMD HANDLER",
        "CMD CALLED",
    ]


def test_application_error_execution_flow():
    messages = []
    app = Application(
        "test",
        "0.1.0",
        cli_handler=Handler("CLI", messages, raise_err=True),
        env_handler=Handler("ENV", messages),
        appdir_handler=Handler("APPDIR", messages),
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_handler=Handler("CMD", messages).command(),
        error_handler=Handler("ERR", messages).error_handler(),
    )
    app.main()

    assert messages == ["CLI", "ERR CLI raised an error"]


def test_application_error_execution_flow_2():
    messages = []
    app = Application(
        "test",
        "0.1.0",
        cli_handler=Handler("CLI", messages),
        env_handler=Handler("ENV", messages),
        appdir_handler=Handler("APPDIR", messages),
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        pre_logging_config_handler=Handler("PRE-LOGGING", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_handler=Handler("CMD", messages, raise_err=True).command(),
        error_handler=Handler("ERR", messages).error_handler(),
    )
    app.main()

    assert messages == [
        "CLI",
        "ENV",
        "APPDIR",
        "CONFIG",
        "CONTEXT",
        "PRE-LOGGING",
        "LOGGING",
        "CMD HANDLER",
        "CMD CALLED",
        "ERR CMD raised an error",
    ]


def test_application_turn_off_handler():
    messages = []
    app = Application(
        "test",
        "0.1.0",
        cli_handler=None,
        env_handler=None,
        appdir_handler=None,
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        pre_logging_config_handler=Handler("PRE-LOGGING", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_handler=Handler("CMD", messages).command(),
        error_handler=Handler("ERR", messages).error_handler(),
    )
    app.main()

    assert messages == [
        "CONFIG",
        "CONTEXT",
        "PRE-LOGGING",
        "LOGGING",
        "CMD HANDLER",
        "CMD CALLED",
    ]


def test_application_insert_before_after_handlers():
    messages = []
    app = Application(
        "test",
        "0.1.0",
        cli_handler=None,
        env_handler=None,
        appdir_handler=None,
        config_handler=Handler("CONFIG", messages),
        context_handler=Handler("CONTEXT", messages),
        pre_logging_config_handler=Handler("PRE-LOGGING", messages),
        logging_config_handler=Handler("LOGGING", messages),
        command_handler=Handler("CMD", messages).command(),
        error_handler=Handler("ERR", messages).error_handler(),
        before_config_handler=Handler("BEFORE CONFIG", messages),
        after_logging_config_handler=Handler("AFTER LOGGING", messages),
        after_command_handler=Handler("AFTER CMD", messages),
    )
    app.main()

    assert messages == [
        "BEFORE CONFIG",
        "CONFIG",
        "CONTEXT",
        "PRE-LOGGING",
        "LOGGING",
        "AFTER LOGGING",
        "CMD HANDLER",
        "AFTER CMD",
        "CMD CALLED",
    ]
