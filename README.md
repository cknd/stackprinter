## Python stack formatter

This prints more detailed Python stack traces, with some source context and the current variable contents. It's a quick way to see what your code is doing when you don't have an IDE or even a debugger for some reason, say when all you have for debugging is a log file.

#### Before
<img src="tb_before.png" width="400">

#### After
<img src="tb_after.png" width="400">

# Usage

## Log detailed tracebacks for exceptions
Just call `show` or `format` in an except block.

By default, this produces a plain text string. Pass `style='color'` to get semantic highlighting like above. See the docs for `format` for the full set of configs.

```python
import stackprinter

try:
    something()
except:
    stackprinter.show(style='color')  # grab the current exception and print it to stderr

    # ...or only return a string, e.g. for logging.
    # defaults to plain text.
    message = stackprinter.format()
    logging.log(message)
```
There's also a `stackprinter.set_excepthook`, which replaces the default python crash message by this one (so it works everywhere without the extra `try/catch`ing... unless you're running in IPython).

You can also pass things like exception objects explicitely (see docs).

## See the call stack of another thread
Pass the thread object to `show` or `format`

```python
thread = threading.Thread(target=something)
thread.start()
while True:
    stackprinter.show(thread)
    time.sleep(0.1)
```

## See the call stack of the current thread
```python
stackprinter.show()
```

## Trace a piece of code as it is executed

More as a toy than anything else, you can watch a piece of code step-by-step, by printing a trace of each function call & return 'live' as they are happening.
```python
tp = TracePrinter(style='color', suppressed_paths=[r"lib/python.*/site-packages/numpy"])
tp.enable()
a = np.ones(111)
dosomething(a)
tp.disable()
```

<img src="trace.png" width="400">

# How it works

Basically, this is a frame formatter. For each [frame on the call stack](https://en.wikipedia.org/wiki/Call_stack), it grabs the source code to find out which source lines reference which variables. Then it displays code and variables in the neighbourhood of the last executed line. Since it knows where in the code each variable occurs, it's relatively easy to do semantic highlighting.

The frame inspection routines are independent of any actual string formatting, so it should be fairly straightforward to write other formatter types on top. Like, foldable and clickable html pages instead of text logs, with download links for pickled variable contents?

# Caveats

Inspecting and formatting isn't thread safe: Other threads don't stop just because we're looking at their call stacks. So, in multi-threaded programs, variables may change _while we're busy walking through the stack and printing it_. This can create confusing logs in some rare cases. If in doubt, and you still don't have a debugger, maybe play with the `Traceprinter` (see above). It hooks into the interpreter's `trace` function to print frames immediately as they are executed. This is basically an automated version of putting lots of print statements in your code. Slows everything down though, of course.

# Docs

\*coughs\*

For now, look at doc strings
