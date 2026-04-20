from typing import Any


class InterestingButFlawedClass:
    def __init__(self):
        pass

    def would_you_like_to_come_to_my_place(self):
        self.bouncy_bouncy()

    def bouncy_bouncy(self):
        raise Exception("I will not buy this record, it is scratched!")


def do_something_interesting_then_callback(callback, **kwargs: Any):
    this = "interesting"  # noqa: F841
    callback(**kwargs)
