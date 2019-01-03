# Python call stack formatter

This prints detailed Python stack traces, with more source context and with the current variable contents. When you don't have an IDE or even a debugger for some reason, this is a good way to find out what a piece of code is doing. It's particularly useful when your only debugging tool is a log file.

Before & After:

<img src="tb_before.png" width="300"> <img src="tb_after.png" width="300">

# Usage

## Log detailed tracebacks after exceptions
```python
try:
    something()
except:
    # grab the latest exception and
    # print a traceback to stderr:
    stackprinter.show()

    # ...or only return the string, for logging
    message = stackprinter.format(style='plaintext')
    logging.log(ERROR, message)
```

There's also a `stackprinter.set_excepthook`, which replaces the default python crash message (so it works everywhere without the extra `try/catch`ing... unless you're running within IPython). You can also pass exception objects explicitely (see docs TODO).

## See the call stack of another thread
```python
thread = threading.Thread(target=something)
thread.start()
while True:
    stackprinter.show(thread)  # or format
    time.sleep(0.1)
```

## See the call stack of the current thread
```python
stackprinter.show()  # or format
```

## Trace a piece of code as it is executed:
```python
tp = stackprinter.Traceprinter(style='color', print_function=sys.stdout.write)
tp.enable()
dosomething()
tp.disable()

# equivalent decorator:
@stackprinter.trace(style='color')
def dosomething():
    ...
```

# How it works

Basically, this is a frame formatter. For each [frame on the call stack](https://en.wikipedia.org/wiki/Call_stack), it grabs the source code to find out which source lines reference which variables. Then it displays code and variables in the neighbourhood of the last executed line.
This yields a log that covers 90% of what I usually do with a debugger ('what was this function called with?', 'why did that argument have _that_ value?'). Since it knows where in the code each variable occurs, it even does semantic highlighting (with `style='color'`).

The frame inspection routines are independent of any actual string formatting, so it should be fairly straightforward to write other formatter types on top. Like, foldable and clickable html pages instead of text logs?

# Caveats

Inspecting and formatting isn't thread safe: Other threads don't stop just because we're looking at their call stacks. So, in multi-threaded programs, variables may change _while we're busy walking through the stack and printing it_. This can create confusing logs in some rare cases. If in doubt, and you still don't have a debugger, maybe play with the `Traceprinter` (see below): It hooks into the interpreter's `trace` function to print frames immediately as they are executed. This is basically an automated version of putting lots of print statements in your code. Slows everything down though, of course.

# Docs

