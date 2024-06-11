"""Check the VCSDependency."""
from fades import parsing


def test_string_representation():
    """This is particularly tested because it's the interface to be installed."""
    dep = parsing.VCSDependency("testurl")
    assert str(dep), "testurl"


def test_contains():
    """This is particularly tested because it's how fulfilling is tested."""
    dep1 = parsing.VCSDependency("testurl")
    assert dep1.specifier.contains(None)
    assert not dep1.specifier.contains("123")


def test_equality():
    dep1 = parsing.VCSDependency("testurl")
    dep2 = parsing.VCSDependency("testurl")
    dep3 = parsing.VCSDependency("otherurl")
    assert dep1 == dep2
    assert not (dep1 == dep3)
    assert not (dep1 != dep2)
    assert dep1 != dep3
    assert not (dep1 == 123)
    assert not (dep1 == "testurl")
