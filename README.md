<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/darkbg.png" width="500">

# Better crash logs

This prints tracebacks / call stacks with code context and the values of nearby variables. It answers most of the questions I'd ask an interactive debugger: Where in the code did it happen, what's in the relevant local variables, and why was _that_ function called with _those_ arguments.

Basically, it's a more helpful version of Python's built-in crash message. It will either print to the console or give you a string for logging.

```bash
pip install stackprinter
```
```python
import stackprinter
stackprinter.set_excepthook()
```

### Before
```
Traceback (most recent call last):
  File "demo.py", line 10, in <module>
    dangerous_function(somelist + anotherlist)
  File "demo.py", line 4, in dangerous_function
    return sorted(blub, key=lambda xs: sum(xs))
  File "demo.py", line 4, in <lambda>
    return sorted(blub, key=lambda xs: sum(xs))
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

### After
```
File demo.py, line 10, in <module>
    8         somelist = [[1,2], [3,4]]
    9         anotherlist = [['5', 6]]
--> 10        dangerous_function(somelist + anotherlist)
    11    except:
    ..................................................
     somelist = [[1, 2], [3, 4]]
     anotherlist = [['5', 6]]
    ..................................................

File demo.py, line 4, in dangerous_function
    3     def dangerous_function(blub):
--> 4         return sorted(blub, key=lambda xs: sum(xs))
    ..................................................
     blub = [[1, 2], [3, 4], ['5', 6]]
    ..................................................

File demo.py, line 4, in <lambda>
    2
    3     def dangerous_function(blub):
--> 4         return sorted(blub, key=lambda xs: sum(xs))
    5
    ..................................................
     xs = ['5', 6]
    ..................................................

TypeError: unsupported operand type(s) for +: 'int' and 'str'
```
I sometimes use it locally instead of a debugger, but mostly it helps me sleep when my code runs somewhere where the only debug tool is a log file (though it's not a fully-grown [error monitoring system](https://sentry.io/welcome/)).

By default, it tries to be somewhat polite about screen space (showing only a few source lines & the function header, and only the variables in those lines, and only (?) 500 characters per variable). You can [configure](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L82-L127) exactly how verbose things should be.

The default output is plain text, which is good when you're logging to a file. There's also a color mode 🌈, enabled by passing `style='darkbg'` or `style='lightbg'` (or `'darkbg2'`, `'darkbg3'`, `'lightbg2'`, `'lightbg3'`) to any of the functions below. (It's an attempt at [semantic highlighting](https://medium.com/@brianwill/making-semantic-highlighting-useful-9aeac92411df), i.e. the colors follow the variables instead of the syntax.)

<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/notebook.png" width="500">


# Usage

## Exception logging
To globally replace the default python crash message, call `set_excepthook()` somewhere. This will print any uncaught exception to stderr by default. You could also [make this permanent for your python installation](#making-it-stick).

```python
import stackprinter
stackprinter.set_excepthook(style='color')
```

To see a specific exception, call [`show()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L154-L162) or [`format()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137) inside an `except` block. `show()` prints to stderr by default, `format()` returns a string, for custom logging.


```python
try:
    something()
except:
    # print the current exception to stderr:
    stackprinter.show()

    # ...or only get a string, e.g. for logging:
    logger.error(stackprinter.format())
```
You can also pass exceptions explicitly.
```python
# or explicitly grab a particular exception
try:
    something()
except ValueError as e:
    error_message = stackprinter.format(e)

```
```python
# or collect exceptions in a little jar somewhere, to log them later
try:
    something()
except ValueError as e:
    errors.append(e)

# later:
for err in errors:
    message = stackprinter.format(err)
    logger.log(message)
```

For some ideas how to integrate this more directly with the `logging` module, see [`demo_logging.py`](https://github.com/cknd/stackprinter/blob/master/demo_logging.py) and [`demo_logging_hack.py`](https://github.com/cknd/stackprinter/blob/master/demo_logging_hack.py).

For more config etc, for now, [see the docstring of `format()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L82-L127).

## Printing the current call stack
To see your own thread's current call stack, call `show` or `format` anywhere outside of exception handling.

```python
stackprinter.show() # or format()
```

## Printing the stack of another thread
To inspect the call stack of any other running thread:

```python
thread = threading.Thread(target=something)
thread.start()
# (...)
stackprinter.show(thread) # or format(thread)
```

## Tracing a piece of code

More for curiosity than anything else, you can watch a piece of code execute step-by-step, printing a trace of all calls & returns 'live' as they are happening. Slows everything down though, of course.
```python
with stackprinter.TracePrinter(style='darkbg2'):
    dosomething()
```

or
```python
tp = stackprinter.TracePrinter(style='darkbg2')
tp.enable()
dosomething()
# (...) +1 million lines
tp.disable()
```
<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/trace.png" width="300">

## Making it stick

To permanently replace the crash message for your python installation, you *could* put a file `sitecustomize.py` into the `site-packages` directory under one of the paths revealed by `python -c "import site; print(site.PREFIXES)"`, with contents like this:

```python
    # in e.g. some_virtualenv/lib/python3.x/site-packages/sitecustomize.py:
    import stackprinter
    stackprinter.set_excepthook(style='darkbg2')
```

That would give you colorful tracebacks automatically every time, even in the REPL.

(You could do a similar thing for IPython, [but they have their own method](https://ipython.readthedocs.io/en/stable/interactive/tutorial.html?highlight=startup#configuration), where the file goes into `~/.ipython/profile_default/startup` instead, and also I don't want to talk about what this module does to set an excepthook under IPython.)

# How it works

Basically, this is a frame formatter. For each [frame on the call stack](https://en.wikipedia.org/wiki/Call_stack), it grabs the source code to find out which source lines reference which variables. Then it displays code and variables in the neighbourhood of the last executed line.

Since this already requires a map of where each variable occurs in the code, it was difficult not to also implement the whole semantic highlighting color thing seen in the screenshots. The colors are ANSI escape codes now, but it should be fairly straightforward™ to render the underlying data without any 1980ies terminal technology. Say, a foldable and clickable HTML page with downloadable pickled variables. For now you'll have to pipe the ANSI strings through [ansi2html](https://github.com/ralphbean/ansi2html/) or something.

The format and everything is inspired by the excellent [`ultratb`](https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.ultratb.html) in IPython. One day I'd like to contribute the whole "find out which variables in `locals` and `globals` are nearby in the source and print only those" machine over there, after trimming its complexity a bit.

# Caveats

This displays variable values as they are _at the time of formatting_. In
multi-threaded programs, variables can change while we're busy walking
the stack & printing them. So, if nothing seems to make sense, consider that
your exception and the traceback messages are from slightly different times.
Sadly, there is no responsible way to freeze all other threads as soon
as we want to inspect some thread's call stack (...or is there?)

# Docs

\*coughs\*

For now, just look at all the doc strings, [e.g. those of `format()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137)
