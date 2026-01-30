import re
from re import RegexFlag

import stackprinter
from tests.source_boring import BoringClass


def test_hide_suppressed_frames():
    # Arrange
    boring = BoringClass()

    # Act:
    try:
        boring.do_something_boring(for_num_of_frames=10)
    except Exception as e:
        fmt_stacktrace: str = stackprinter.format(
            e, suppressed_paths=["source_boring"], truncate_suppressed_frames=True, add_summary=False
        )

    # Assert
    print(fmt_stacktrace)
    matches = re.findall("source_boring\.py", fmt_stacktrace, RegexFlag.MULTILINE)
    assert len(matches) == 2
    assert "8 suppressed frames truncated" in fmt_stacktrace


def test_hide_suppressed_frames_multiple_sequences():
    # Arrange
    boring = BoringClass()

    # Act
    try:
        boring.do_something_boring(for_num_of_frames=10, boring_sequences=3)
    except Exception as e:
        fmt_stacktrace: str = stackprinter.format(
            e, suppressed_paths=["source_boring"], truncate_suppressed_frames=True, add_summary=False
        )

    # Assert
    matches_frames = re.findall("source_boring\.py", fmt_stacktrace, RegexFlag.MULTILINE)
    assert len(matches_frames) == 2 * 3  # 1 before 1 after for each of 3 sequences
    matches_hidden_label = re.findall("8 suppressed frames truncated", fmt_stacktrace, RegexFlag.MULTILINE)
    assert len(matches_hidden_label) == 3  # 3 sequences that will be truncated


def test_hide_suppressed_frames_only_two_boring_frames():
    # Arrange
    boring = BoringClass()

    # Act:
    try:
        boring.do_something_boring(for_num_of_frames=2)
    except Exception as e:
        fmt_stacktrace: str = stackprinter.format(
            e, suppressed_paths=["source_boring"], truncate_suppressed_frames=True, add_summary=False
        )

    # Assert
    print(fmt_stacktrace)
    matches = re.findall(r"source_boring\.py", fmt_stacktrace, RegexFlag.MULTILINE)
    assert len(matches) == 2
    assert "suppressed frames truncated" not in fmt_stacktrace
