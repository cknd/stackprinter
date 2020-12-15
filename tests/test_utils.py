import re

from stackprinter.utils import match


def test_match():
    assert match('my/ignored/path', None) is False
    assert match('my/ignored/path', 'ignored')
    assert match('my/ignored/path', ['not', 'ignored'])
    assert match('my/ignored/path', [re.compile('not ignored'), re.compile('ignored')])
