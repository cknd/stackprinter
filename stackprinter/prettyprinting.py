import os
import pprint

from stackprinter.extraction import UnresolvedAttribute
from stackprinter.utils import inspect_callable

try:
    import numpy as np
except ImportError:
    np = False
else:
    from distutils.version import LooseVersion
    is_modern_numpy = LooseVersion(np.__version__) >= LooseVersion('1.14')
    # numpy's array2string method gained some new keywords after version 1.13

MAXLEN_DICT_KEY_REPR = 25  # truncate dict keys to this nr of characters

# TODO see where the builtin pprint module can be used instead of all this
# (but how to extend it for e.g. custom np array printing?)

def format_value(value, indent=0, truncation=None, wrap=60,
                 max_depth=2, depth=0):
    """
    Stringify some object

    Params
    ---
    value: object to be formatted

    indent: int
        insert extra spaces on each line

    truncation: int
        cut after this nr of characters

    wrap: int
        insert linebreaks after this nr of characters, use 0 to never add a linebreak

    max_depth: int
        max repeated calls to this function when formatting container types

    depth: int
        current nesting level

    Returns
    ---
    string
    """

    if depth > max_depth:
        return '...'

    if isinstance(value, UnresolvedAttribute):
        reason = "# %s" % (value.exc_type)
        val_tpl = reason + "\n%s = %s"
        lastval_str = format_value(value.last_resolvable_value,
                                   truncation=truncation, indent=3, depth=depth+1)
        val_str = val_tpl % (value.last_resolvable_name, lastval_str)
        indent = 10

    elif isinstance(value, (list, tuple, set)):
        val_str = format_iterable(value, truncation, max_depth, depth)

    elif isinstance(value, dict):
        val_str = format_dict(value, truncation, max_depth, depth)

    elif np and isinstance(value, np.ndarray):
        val_str = format_array(value, minimize=depth > 0)

    elif callable(value):
        name, filepath, method_owner, ln = inspect_callable(value)
        filename = os.path.basename(filepath) if filepath is not None else None
        if filename is None:
            val_str = safe_repr(value)
        elif method_owner is None:
            name_s = safe_str(name)
            filename_s = safe_str(filename)
            ln_s = safe_str(ln)
            val_str = "<function '%s' %s:%s>" % (name_s, filename_s, ln_s)
        else:
            name_s = safe_str(name)
            filename_s = safe_str(filename)
            method_owner_s = safe_str(method_owner)
            ln_s = safe_str(ln)
            val_str = "<method '%s' of %s %s:%s>" % (name_s, method_owner_s,
                                                     filename_s, ln_s)
    else:
        val_str= safe_repr_or_str(value)

    val_str = truncate(val_str, truncation)

    if depth == 0:
        val_str = wrap_lines(val_str, wrap)

    if indent > 0:
        nl_indented = '\n' + (' ' * indent)
        val_str = val_str.replace('\n', nl_indented)

    return val_str


def format_dict(value, truncation, max_depth, depth):
    typename = value.__class__.__name__
    prefix = '{' if type(value) == dict else "%s\n{" % typename
    postfix = '}'

    if depth == max_depth:
        val_str = '...'
    else:
        vstrs = []
        char_count = 0
        for k, v in value.items():
            if char_count >= truncation:
                break
            kstr = truncate(repr(k), MAXLEN_DICT_KEY_REPR)
            vstr = format_value(v, indent=len(kstr) + 3,
                                truncation=truncation, depth=depth+1)
            istr = "%s: %s" % (kstr, vstr)
            vstrs.append(istr)
            char_count += len(istr)


        val_str = ',\n '.join(vstrs)

    return prefix + val_str + postfix


def format_iterable(value, truncation, max_depth, depth):
    typename = value.__class__.__name__
    if isinstance(value, list):
        prefix = '[' if type(value) == list else "%s [" % typename
        postfix = ']'

    elif isinstance(value, tuple):
        prefix = '(' if type(value) == tuple else "%s (" % typename
        postfix = ')'

    elif isinstance(value, set):
        prefix = '{' if type(value) == set else "%s {" % typename
        postfix = '}'


    length = len(value)
    val_str = ''
    if depth == max_depth:
        val_str += '...'
    else:
        linebreak = False
        char_count = 0
        for i,v in enumerate(value):
            if char_count >= truncation:
                val_str += "..."
                break
            item_str = ''
            entry = format_value(v, indent=1, truncation=truncation,
                                 depth=depth+1)
            sep = ', ' if i < length else ''
            if '\n' in entry:
                item_str += "\n %s%s" % (entry, sep)
                linebreak = True
            else:
                if linebreak:
                    item_str += '\n'
                    linebreak = False
                item_str += "%s%s" % (entry, sep)
            val_str += item_str
            char_count += len(item_str)

    return prefix + val_str + postfix


def format_array(arr, minimize=False):
    """
    format a numpy array (with shape information)

    Params
    ---
    minimize: bool
        use an extra compact oneline format
    """
    if arr.ndim >= 1:
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

    if is_modern_numpy:
        array_rep = np.array2string(arr, max_line_width=9000, threshold=50,
                                    edgeitems=2, prefix=prefix, suffix=suffix)
    else:
        array_rep = np.array2string(arr, max_line_width=9000, prefix=prefix)

    if minimize and (len(array_rep) > 50 or arr.ndim > 1):
        array_rep = "%s%s...%s" % ('[' * arr.ndim, arr.flatten()[0], ']' * arr.ndim)


    msg += array_rep + suffix
    return msg

def safe_repr(value):
    try:
        return repr(value)
    except:
        return '# error calling repr'


def safe_str(value):
    try:
        return str(value)
    except:
        return '# error calling str'


def safe_repr_or_str(value):
    try:
        return repr(value)
    except:
        try:
            return str(value)
        except:
            return '# error calling repr and str'


def truncate(string, n):
    if not n:
        return string
    n = max(n, 0)
    if len(string) > (n+3):
        string = "%s..." % string[:n].rstrip()
    return string


def wrap_lines(string, max_width=80):
    if not max_width or max_width <= 0:
        return string

    def wrap(lines):
        for l in lines:
            length = len(l)
            if length <= max_width:
                yield l
            else:
                k = 0
                while k < length:
                    snippet = l[k:k+max_width]
                    if k > 0:
                        snippet = " " + snippet

                    yield snippet
                    k += max_width

    wrapped_lines = wrap(string.splitlines())
    return '\n'.join(wrapped_lines)
