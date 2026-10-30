import stackprinter


def test_frame_formatting():
    """ pin plaintext output """
    msg = stackprinter.format()
    lines = msg.split('\n')

    expected = ['File "test_formatting.py", line 6, in test_frame_formatting',
                '    4    def test_frame_formatting():',
                '    5        """ pin plaintext output """',
                '--> 6        msg = stackprinter.format()',
                "    7        lines = msg.split('\\n')",
                '    ..................................................',
                "     stackprinter.format = <function 'format' __init__.py:17>",
                '    ..................................................',
                '',
                '']

    for k, (our_line, expected_line) in enumerate(zip(lines[-len(expected):], expected)):
        if k == 0:
            assert our_line[-52:] == expected_line[-52:]
        elif k == 6:
            assert our_line[:58] == expected_line[:58]
        else:
            assert our_line == expected_line

    # for scheme in stackprinter.colorschemes.__all__:
    #     stackprinter.format(style=scheme, suppressed_paths=[r"lib/python.*"])


def test_exception_formatting():
    from source import Hovercraft

    try:
        Hovercraft().eels
    except:
        msg_plain = stackprinter.format()
        msg_color = stackprinter.format(style='darkbg')

    lines = msg_plain.split('\n')

    assert lines[0].endswith('eels')
    assert lines[-1] == 'Exception: ahoi!'

    print(msg_plain)
    print(msg_color)


def test_none_tuple_formatting():
    output = stackprinter.format((None, None, None))
    assert output == "NoneType: None"


def test_none_value_formatting():
    output = stackprinter.format((TypeError, None, None))
    assert output == "TypeError: None"


def test_tb_with_none_lineno():
    # Regression Python 3.12+ compat.
    # Since CPython 3.12, `tb.tb_lineno` (and `frame.f_lineno`) return None when
    # the instruction at tb_lasti has no line mapping. Stackprinter used to pass
    # that None straight into source_inspection.annotate() and blow up on
    # `assert isinstance(lineno, int)`. It should now fall back gracefully.
    import sys
    import types

    import pytest

    captured = []

    def target():
        captured.append(sys._getframe())

    target()
    frame = captured[0]

    # An out-of-range tb_lasti makes CPython's tb_lineno getter return None via
    # its Py_RETURN_NONE fallback path.
    tb = types.TracebackType(None, frame, 1 << 20, -1)
    if tb.tb_lineno is not None:
        pytest.skip(
            "tb.tb_lineno didn't return None on this interpreter "
            f"({sys.version_info}); regression only applies when it does."
        )

    output = stackprinter.format((ValueError, ValueError("boom"), tb))
    assert "target" in output
    assert "ValueError: boom" in output


def _assert_exception_group_format(use_subclass=False, as_tuple=False,
                                   with_traceback=False):
    import builtins
    import traceback

    import pytest

    group_type = getattr(builtins, 'ExceptionGroup', None)
    if group_type is None:
        pytest.skip('Exception groups require Python 3.11 or newer')

    outer_type = group_type
    if use_subclass:
        class CustomGroup(group_type):
            pass
        outer_type = CustomGroup

    exc = outer_type('outer', [
        ValueError('first nested error'),
        group_type('inner', [TypeError('deeply nested error')]),
    ])
    if with_traceback:
        try:
            raise exc
        except Exception:
            pass

    thing = (type(exc), exc, exc.__traceback__) if as_tuple else exc
    expected = ''.join(traceback.format_exception(
        type(exc), exc, exc.__traceback__))
    assert stackprinter.format(thing, show_vals=None) == expected


def test_exception_group_subclass_instance():
    _assert_exception_group_format(use_subclass=True)


def test_exception_group_subclass_exc_info():
    _assert_exception_group_format(use_subclass=True, as_tuple=True)


def test_exception_group_subclass_traceback():
    _assert_exception_group_format(use_subclass=True, with_traceback=True)


def test_builtin_exception_group_instance():
    _assert_exception_group_format()


def test_builtin_exception_group_exc_info():
    _assert_exception_group_format(as_tuple=True)


def test_ordinary_exception_instance():
    output = stackprinter.format(ValueError('ordinary error'), show_vals=None)
    assert output == 'ValueError: ordinary error'
