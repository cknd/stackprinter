# flake8: noqa

# Exception groups (new in py 3.11) aren't supported so far,
# but at least we fall back on the default message.

import stackprinter
stackprinter.set_excepthook()


def raise_group():
    group = ExceptionGroup('A group!',
        [Exception("Something!"), Exception("Something else!")])
    raise group


raise_group()
