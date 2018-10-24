from extraction import UnresolvedAttribute
from utils import inspect_callable
try:
    import numpy as np
except ImportError:
    np = False


def format_value(value, indent=0, name='', truncate=500, oneline=False):

    # TODO see where pprint can be used instead https://docs.python.org/3/library/pprint.html

    # TODO look at https://docs.python.org/3.6/library/reprlib.html for recursion-safe and size limited reprs
    # ... otoh, maybe recursion isnt a problem? https://docs.python.org/3/c-api/exceptions.html#c.Py_ReprEnter

    if isinstance(value, UnresolvedAttribute):
        # import pdb; pdb.set_trace()
        reason = "# %s" % (value.exc_type)
        val_tpl = reason + "\n%s = %s"
        lastval_str = format_value(value.last_resolvable_value, indent=3)
        val_str = val_tpl % (value.last_resolvable_name, lastval_str)
        indent = 10

    elif isinstance(value, dict):
        vstrs = []
        for k, v in value.items():
            vstr = format_value(v, truncate=min(truncate, 50), oneline=True)
            vstrs.append("%r: %s" % (k, vstr))
        dtype = value.__class__.__name__
        dtype_s = '' if dtype == 'dict' else dtype + '\n'
        val_str = dtype_s + '{' + ',\n '.join(vstrs) + '}'

    elif np and isinstance(value, np.ndarray):
        val_str = format_array(value)

    elif callable(value):
        name, filename, ln, method_owner = inspect_callable(value)
        if filename is None:
            val_str = repr(value)
        elif method_owner is None:
            val_str = "<function '%s' %s:%s>" % (name, filename, ln)
        else:
            val_str = "<method '%s' of %s %s:%s>" % (name, method_owner, filename, ln)

    # maybe just try: repr(value), because try: str(value) may already be implied (doublecheck)
    elif hasattr(value, '__repr__'):
        try:
            val_str = repr(value)
        except:
            val_str = "<error calling __repr__>"
    else:
        try:
            val_str = str(value)
        except:
            val_str = "<error calling __str__>"

    if truncate and len(val_str) > (truncate+3):
        val_str = "%s..." % val_str[:truncate]

    if oneline:
        val_str = val_str.replace('  ', '').replace('\n', '')
    else:
        nl_indented = '\n' + (' ' * (indent))
        val_str = val_str.replace('\n', nl_indented)
    return val_str

def format_array(arr):
    if arr.ndim >= 1:
        # shape_str = repr(arr.shape)
        shape = list(arr.shape)
        if len(shape) < 2:
            shape.append('')
        shape_str = "x".join(str(d) for d in shape)
        if len(shape_str) < 10:
            prefix = "%s array(" % shape_str
            msg = prefix
        else:
            prefix = ""
            msg = "%s array(\n" % shape_str
    else:
        msg = prefix = "array("

    suffix = ')'
    msg += np.array2string(arr, max_line_width=9000, threshold=50,
                           edgeitems=3, prefix=prefix, suffix=suffix)
    msg += suffix
    return msg
