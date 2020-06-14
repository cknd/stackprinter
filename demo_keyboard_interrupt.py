import time
import stackprinter


def blocking_function(x):
    print('ctrl-C me')
    time.sleep(5)

try:
    some_value = 'spam'
    blocking_function(some_value)
except:
    # Default: Only print summary info
    stackprinter.show()
    # Override:
    # stackprinter.show(suppressed_exceptions=None)
    # stackprinter.show(suppressed_exceptions=[])


