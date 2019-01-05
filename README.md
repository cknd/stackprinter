## Python stack formatter

This prints detailed Python stack traces, with more source context and current variable values. It's a quick way to see what your code is doing when your only debugging tool is a log file 😱

#### Before
<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/tb_before.png" width="400">

#### After
<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/tb_after.png" width="400">

## Installation


```bash
pip install stackprinter
```

## Logging exception tracebacks
Call `show` or `format` inside an _except_ block to trace the current exception. `show` prints to stderr, `format` returns a string. You can also pass exception objects explicitly.

By default, this will generate plain text. Pass `style='color'` to get funky terminal colors. For all the config options, [see the docs of `format()`](stackprinter/__init__.py#L28-L137).

```python
import stackprinter

try:
    something()
except:
    stackprinter.show()  # grab the current exception and print a traceback to stderr

    # ...or only return a string, e.g. for logging.
    message = stackprinter.format()
    logging.log(message)
```
There's also `stackprinter.set_excepthook` which replaces the default python crash message (so it works automatically without manual try/except... unless you're in IPython).

## Printing the call stack of another thread
Pass a thread object to `show` or `format`.

```python
thread = threading.Thread(target=something)
thread.start()
while True:
    stackprinter.show(thread) # or format(thread)
    time.sleep(0.1)
```

## Printing the call stack of the current thread
Call `show` or `format` outside of exception handling.

```python
stackprinter.show() # or format()
```

For people who don't like context dependent methods, there's also `show/format_current_stack()`, which does the same even inside _except_ blocks.

## Tracing a piece of code as it is executed

More for curiosity than anything else, you can watch a piece of code execute step-by-step, printing a trace of all calls & returns 'live' as they are happening. Slows everything down though, of course.
```python
tp = stackprinter.TracePrinter(style='color', suppressed_paths=[r"lib/python.*/site-packages/numpy"])
tp.enable()
a = np.ones(111)
dosomething(a)
tp.disable()
```

<img src="https://raw.githubusercontent.com/cknd/stackprinter/master/trace.png" width="400">

# How it works

Basically, this is a frame formatter. For each [frame on the call stack](https://en.wikipedia.org/wiki/Call_stack), it grabs the source code to find out which source lines reference which variables. Then it displays code and variables in the neighbourhood of the last executed line.

Since this already requires a map of where each variable occurs in the code, it was hard not to also implement the whole semantic highlighting color thing seen in the screenshots. The colors are ANSI escape codes now, but it should be fairly straightforward™ to render the underlying data without any 1980ies terminal technology. Say, a foldable and clickable HTML page with downloadable pickled variables. But for now you'll have to pipe the ANSI strings through [ansi2html](https://github.com/ralphbean/ansi2html/) or something.

# Caveats

This displays variable values as they are _at the time of formatting_. In
multi-threaded programs, variables can change while we're busy walking
the stack & printing them. So, if nothing seems to make sense, consider that
your exception and the traceback messages are from slightly different times.
Sadly, there is no responsible way to freeze all other threads as soon
as we want to inspect some thread's call stack (...or is there?)

# Docs

\*coughs\*

For now, just look at all the doc strings, e.g. of [`format()`](stackprinter/__init__.py#L28-L137)
