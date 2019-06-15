from source import sourcelines
from stackprinter import source_inspection as si


def test_source_annotation(sourcelines):
    """ """
    line_offset = 23
    source_map, line2names, name2lines, head_lns, lineno = si.annotate(sourcelines, line_offset, 42)

    # see that we didn't forget or invent any lines
    assert len(source_map) == len(sourcelines)

    # reassemble the original source, whitespace and all
    # (except when we hit the `\`-line continuations at the bottom of the
    # file - parsing collapses continued lines, so those can't be reconstructed.)
    for k, (true_line, parsed_line) in enumerate(zip(sourcelines, source_map.values())):
        if '\\' in true_line:
            assert k >= 50
            break
        reconstructed_line = ''.join([snippet for snippet, ttype in parsed_line])
        assert reconstructed_line == true_line


    # see if we found this known token
    assert source_map[17 + line_offset][5] == ('lambda', 'KW')

    # see if we found this name
    assert "spam_spam_spam" in line2names[17 + line_offset]
    assert 17 + line_offset in name2lines["spam_spam_spam"]

    # see if we found this multiline function header
    assert head_lns == [k + line_offset for k in [4,5,6,7]]

    # ... and that lineno survived the roundtrip
    assert lineno == 42