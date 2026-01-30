import stackprinter
from tests.source_boring import BoringClass

try:
    boring = BoringClass()
    boring.do_something_boring(for_num_of_frames=10, boring_sequences=3)
except Exception as e:
    print("Oops!", e)
    print(
        stackprinter.format(
            e, suppressed_paths=[r"source_boring\.py"], truncate_suppressed_frames=True, add_summary=False
        )
    )
