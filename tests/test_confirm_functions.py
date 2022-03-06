from pathlib import Path
import pytest
from kapow import SimpleNamespace
from kapow import confirm
from kapow.errors import LaunchError


def test_confirm_expression():
    assert confirm.expr(True, "") is None

    with pytest.raises(LaunchError) as ex:
        confirm.expr(False, "Raises an error.")

    assert str(ex.value) == "Raises an error."


def test_confirm_context_variable():

    ns = SimpleNamespace()
    ns.foo = "string"
    ns.fizz = SimpleNamespace()
    ns.fizz.buzz = "string"

    assert confirm.ctx_var(ns, "fizz.buzz", str) is None

    with pytest.raises(LaunchError) as ex:
        confirm.ctx_var(ns, "foo", int)
    assert "variable foo to be type <class 'int'>" in str(ex.value)

    with pytest.raises(LaunchError) as ex:
        confirm.ctx_var(ns, "bar", str)
    assert "bar" in str(ex.value)


def test_confirm_directory_exists():
    this_file = Path(__file__)
    confirm.directory_exists(this_file)


def test_confirm_assert_callable():
    with pytest.raises(LaunchError) as ex:
        confirm.handler_func("string")
    assert "not callable: string" in str(ex.value)


def test_confirm_handler_func():

    with pytest.raises(LaunchError) as ex:
        confirm.handler_func(lambda: 0)
    assert "`<lambda>` has 0 arguments" in str(ex.value)

    def test_handler(a, b):
        pass

    assert confirm.handler_func(test_handler) is None


def test_confirm_error_func():

    with pytest.raises(LaunchError) as ex:
        confirm.error_func(lambda x, y: 0)
    assert "`<lambda>` has 2 arguments" in str(ex.value)

    def test_handler(a, b, c):
        pass

    assert confirm.error_func(test_handler) is None
