import sys
import traceback
import linecache

def printlocals(frame, truncate=500, truncate__=True):
    sep = '.' * 50
    msg = '    %s\n' % sep
    for name, value in sorted(frame.f_locals.items()):
        if hasattr(value, '__repr__'):
            try:
                val_str = value.__repr__()
            except:
                val_str = "<error when calling __repr__>"
        else:
            try:
                val_str = str(value)
            except:
                val_str = "<error calling str()>"

        if truncate and len(val_str) > truncate:
            val_str = "%s..." % val_str[:truncate]
        if truncate__ and name.startswith('__') and len(val_str) > 50:
            val_str = "%s..." % val_str[:50]

        val_str = val_str.replace('\n', '\n        %s' % (' ' * (len(name) + 2)))
        msg += "       %s = %s\n" % (name, val_str)
    msg += '    %s' % sep
    return msg

def tb2string(tb, context=5):
    frame_strings = []
    while tb:
        frame = tb.tb_frame
        filename, name = (frame.f_code.co_filename, frame.f_code.co_name)
        lineno = tb.tb_lineno - 1
        msg = "%s in %s\n" % (filename, frame.f_code.co_name)

        lines = linecache.getlines(filename)
        start = max(lineno - context, 0)
        stop = lineno + 1
        for line_idx in range(start, stop+1):
            if line_idx == lineno:
                line_str = "--> %s " % line_idx
            else:
                line_str = "    %s " % line_idx
            try:
                line_str += lines[line_idx]
            except IndexError:
                line_str += '<error reading line>'
            msg += line_str

        msg += printlocals(frame)
        frame_strings.append(msg)
        tb = tb.tb_next

    return '\n\n\n'.join(frame_strings)

def format_traceback(tb, etype=None, evalue=None):
    msg = tb2string(tb)
    if etype is not None and evalue is not None:
        exc_str = ' '.join(traceback.format_exception_only(etype, evalue))
        msg += '\n\n' + exc_str
    return msg



if __name__ == '__main__':
    import numpy as np
    np.set_printoptions(linewidth=70)
    rng = np.random.RandomState()
    def funcB(foo):
        bar = [foo, foo]
        blafasel = "another string"
        somearray = rng.randint(0,9,size=(100,100))
        for k in range(10):
            if k == 9:
                raise Exception('ahoi')

    def funcA(boing):
        foo = boing + "oeoeoee"
        funcB(foo)

    try:
        funcA("aloahe")
    except:
        etype, exc, tb = sys.exc_info()
        print(format_traceback(tb, etype, exc))