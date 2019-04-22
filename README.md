# More talkative tracebacks

This prints tracebacks / call stacks with code context and the values of nearby variables. It answers most of the questions I'd ask an interactive debugger: Where in the code were we, what's in the relevant local variables, and why was _that_ function called with _those_ arguments.

It's not a fully grown [error monitoring system](https://sentry.io/welcome/), just a more helpful version of Python's built-in crash message. I like to use it in that role even when I have a real debugger. But mostly, it helps me sleep when my code runs somewhere where the only debugging tool is a log file.

```bash
pip install stackprinter
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

By default, it tries to be somewhat polite about screen space. (It only shows a few source lines and the function header, and only the variables in the visible code, and only 500 character per variable). You can configure exactly how verbose things should be. It also attempts advanced stunts like "dot attribute lookups" and "showing the shape of numpy arrays", and you can have [funky colors like this](https://github.com/cknd/stackprinter/blob/master/tb_after.png?raw=true).

# Usage

## Exception logging
To globally replace the default python crash message, call `set_excepthook()` somewhere. This will print any uncaught exception to stderr (by default).

```python
import stackprinter
stackprinter.set_excepthook(style='color')
```

To see a specific exception, call [`show()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L154-L162) or [`format()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137) inside an `except` block. `show()` prints to stderr by default, `format()` just returns a string, for custom logging. You can also pass a previously caught exception object explicitly.


```python
try:
    something()
except:
    # grab the current exception, print the traceback to stderr:
    stackprinter.show()

    # ...or only get a string, e.g. for logging:
    logger.error(stackprinter.format())
```
```python
# or explicitely grab a particular exception
try:
    something()
except ValueError as e:
    stackprinter.show(e)  # or format(e)

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
    logging.log(message)
```

By default, all these calls will generate plain text. Pass `style='color'` to get [funky terminal colors like this](https://github.com/cknd/stackprinter/blob/master/tb_after.png?raw=true). (It's an attempt at [semantic highlighting](https://medium.com/@brianwill/making-semantic-highlighting-useful-9aeac92411df), i.e. colors mark the different variables instead of language syntax.)

You can blacklist certain file paths, to make the stack less verbose whenever it runs through those files. For example, if you call `format(exc, suppressed_paths=[r"lib/python.*/site-packages"])`, calls within installed libraries are shrunk to one line each.

For more options & details, [see the docs of `format()`](https://github.com/cknd/stackprinter/blob/master/stackprinter/__init__.py#L28-L137).

## Printing the current stack of another thread
Apart from exception tracebacks, you can also print the call stack of any live, running thread. Pass the thread object to `show` or `format`:

```python
thread = threading.Thread(target=something)
thread.start()
# (...)
stackprinter.show(thread) # or format(thread)
```

## Printing the stack of the current thread
To see your own thread's stack, call `show` or `format` anywhere outside of exception handling.

```python
stackprinter.show() # or format()
```

(There's also `show_current_stack()`, which does the same thing everywhere even inside an `except` block).

## Tracing a piece of code as it is executed

More for curiosity than anything else, you can watch a piece of code execute step-by-step, printing a trace of all calls & returns 'live' as they are happening. Slows everything down though, of course.
```python
with stackprinter.TracePrinter(style='color'):
    dosomething()
```

or, to avoid indenting existing code:
```python
tp = stackprinter.TracePrinter(style='color')
tp.enable()
dosomething()
# (...) +1 million lines
tp.disable()
```

<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/trace.png" width="400">

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
