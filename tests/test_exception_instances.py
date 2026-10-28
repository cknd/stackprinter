from io import StringIO

import pytest

import stackprinter


def _raise_exception(exc):
    raise exc


@pytest.mark.parametrize('exception_type', [
    BaseException, KeyboardInterrupt, SystemExit, GeneratorExit,
    Exception, ValueError,
])
@pytest.mark.parametrize('with_traceback', [False, True])
@pytest.mark.parametrize('options', [
    {}, {'style': 'darkbg', 'suppressed_exceptions': []},
])
def test_exception_instance_matches_exc_info(exception_type, with_traceback,
                                             options):
    exc = exception_type('message')
    if with_traceback:
        try:
            _raise_exception(exc)
        except BaseException:
            pass

    exc_info = (type(exc), exc, exc.__traceback__)
    expected = stackprinter.format(exc_info, show_vals=None, **options)
    assert exception_type.__name__ in expected
    assert 'message' in expected
    if with_traceback:
        assert '_raise_exception' in expected

    assert stackprinter.format(exc, show_vals=None, **options) == expected
    output = StringIO()
    stackprinter.show(exc, file=output, show_vals=None, **options)
    assert output.getvalue() == expected + '\n'


@pytest.mark.parametrize('thing', [
    42, 'message', object(), [], BaseException, KeyboardInterrupt, ValueError,
])
def test_format_rejects_non_exception_instances(thing):
    with pytest.raises(ValueError, match='Expected an exception instance'):
        stackprinter.format(thing)
