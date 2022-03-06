from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from kapow import Application
from kapow.errors import LaunchError
from kapow.handlers import docopt
from tests.common import CLI_DOCS


class TempAppDirs:
    def __init__(self, tmpdir):
        self._dir = tmpdir

    def __call__(self, name):
        self.name = name
        return self

    @property
    def user_data_dir(self):
        return Path(self._dir, self.name)

    @property
    def user_log_dir(self):
        return Path(self._dir, self.name, "logs")

    @property
    def user_name(self):
        return "testuser"


def test_kapow_default_handlers_app_file_creation(capsys):
    def command_function(ctx):
        print("I RAN")

    app = Application(
        name="testapp",
        version="0.0.1",
        cli_handler=docopt.docopt_handler(CLI_DOCS),
        command_finder=docopt.docopt_command_finder(command_function),
    )

    with TemporaryDirectory() as tmpdir:

        appdirs = TempAppDirs(tmpdir)
        app.initialize(cli_args=["run"], appdirs_class=appdirs)
        app.main()
        output = capsys.readouterr()

        assert output.out == "I RAN\n"

        items = [d.name for d in appdirs.user_data_dir.iterdir()]
        assert items == ["logs", "testapp.config.ini", "testapp.logging.ini"]


def test_kapow_default_handlers_app_default_config_details(capsys):
    """
    Usage:
        myapp.py  --debug

    Usage:
        myapp.py run --debug
        myapp.py test --debug
    """

    def command_function(ctx):
        print("I RAN")

    app = Application(
        name="testapp",
        version="0.0.1",
        cli_handler=docopt.docopt_handler(CLI_DOCS),
        command_func=command_function,
    )

    with TemporaryDirectory() as tmpdir:
        appdirs = TempAppDirs(tmpdir)
        app.initialize(cli_args=["run"], appdirs_class=appdirs)
        app.main()
        output = capsys.readouterr()
        assert output.out == "I RAN\n"

        app_cfg = Path(appdirs.user_data_dir, "testapp.config.ini").read_text()
        assert "[app]" in app_cfg
        assert "wrk_dir = " in app_cfg


def test_kapow_default_handlers_app_default_error_handler(capsys):
    def command_function(ctx):
        raise Exception("This funky error!")

    app = Application(
        name="testapp",
        version="0.0.1",
        cli_handler=docopt.docopt_handler(CLI_DOCS),
        command_func=command_function,
    )

    with TemporaryDirectory() as tmpdir:
        appdirs = TempAppDirs(tmpdir)
        app.initialize(cli_args=["run"], appdirs_class=appdirs)
        app.main()
        output = capsys.readouterr()
        assert "This funky error!" in output.out


def test_kapow_default_handlers_app_default_env_vars_handler(capsys, monkeypatch):

    monkeypatch.setenv("TESTAPP_THINGO", "THINGO!")

    def command_function(ctx):
        print(f"I HAS A {ctx.env_vars.get('TESTAPP_THINGO', 'FOO')}")

    app = Application(
        name="testapp",
        version="0.0.1",
        cli_handler=docopt.docopt_handler(CLI_DOCS),
        command_func=command_function,
    )

    with TemporaryDirectory() as tmpdir:
        appdirs = TempAppDirs(tmpdir)
        app.initialize(cli_args=["run"], appdirs_class=appdirs)
        app.main()
        output = capsys.readouterr()
        assert "I HAS A THINGO!" in output.out


def test_passing_invalid_command_functions():
    def command_function(ctx):
        pass

    with pytest.raises(LaunchError) as ex:
        app = Application(
            name="testapp",
            version="0.0.1",
            cli_handler=docopt.docopt_handler(CLI_DOCS),
            command_finder=command_function,
            command_func=command_function,
        )

    assert "Cannot provide a command and a command finder" in str(ex.value)
