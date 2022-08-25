# 0.2.8 - August 25, 2022

## Fixed
Replace deprecated distutils.LooseVersion by packaging.version

# 0.2.7 - August 12, 2022

## Fixed
- Degrade more gracefully in environments where the standard output streams (stdout, stderr) are not available, such as the `pythonw.exe` GUI. Concretely: 1) If stackprinter's `show()` function is called in such an environment and with default arguments, it will now return silently (doing nothing) instead of crashing. 2) the 'Traceprinter' toy now uses the built in print function (so that it doesn't try to access sys.stderr.write on import).

# 0.2.6 - April 2, 2022

## Added
- New kwarg `suppressed_vars` to redact certain variables, e.g. to keep secrets out of error logs

# 0.2.5 - Oct 31, 2020

## Fixed
- Allows passing `(None, None, None)` to `format_exception`
- Fixed a crashing type error that could occur in longer code scopes (e.g. in the repl)

# 0.2.4 - June 17, 2020

## Changed
- Disabled verbose formatting for KeyboardInterrupts by default. Call `format(..., suppressed_exceptions=None`) to enforce verbose printing even on a keyboard interrupt.

## Added
- New keyword arg `suppressed_exceptions` to disable verbose formatting for certain types of exceptions (generating a standard python-like traceback instead).
- New keyword arg `line_wrap` to adjust or disable the line wrap on variable values.


# 0.2.3 - May 29, 2019

(beginning of time)
