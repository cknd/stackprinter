from tests.source_interesting import (
    InterestingButFlawedClass,
    do_something_interesting_then_callback,
)


class BoringClass:
    """
    Test class that calls itself recursively to create one or more sequences of "boring"
    (suppressed) stack frames in order to test and demo printing a stack with suppressed_paths=[r"source_boring\.py"]
    and truncate_suppressed_frames=True.
    """

    def __init__(self):
        self._initial_num_frames = 0
        pass

    def do_something_boring(self, for_num_of_frames: int, boring_sequences: int = 1):
        self._initial_num_frames = max(self._initial_num_frames, for_num_of_frames)
        if for_num_of_frames <= 1:
            if boring_sequences > 1:
                do_something_interesting_then_callback(
                    self.do_something_boring,
                    for_num_of_frames=self._initial_num_frames,
                    boring_sequences=boring_sequences - 1,
                )
            else:
                interesting = InterestingButFlawedClass()
                interesting.would_you_like_to_come_to_my_place()
        else:
            self.do_something_boring(for_num_of_frames=for_num_of_frames - 1, boring_sequences=boring_sequences)
