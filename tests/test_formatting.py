import re

import stackprinter


def test_frame_formatting():
    """ pin plaintext output """
    msg = stackprinter.format()
    lines = msg.strip().split('\n')

    expected = [r'File ".+test_formatting\.py", line 8, in test_frame_formatting$',
                '    6    def test_frame_formatting():',
                '    7        """ pin plaintext output """',
                '--> 8        msg = stackprinter.format()',
                "    9        lines = msg.strip().split('\\n')"]

    lines = lines[-len(expected):]
    assert re.match(expected[0], lines[0])
    assert lines[1:] == expected[1:]

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



