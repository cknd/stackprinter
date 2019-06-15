import sys
import pytest
import stackprinter.extraction as ex

@pytest.fixture
def frameinfo():
    somevalue = 'spam'
    fr = sys._getframe()
    return ex.get_info(fr)

def test_frameinfo(frameinfo):
    fi = frameinfo
    assert fi.filename.endswith('test_frame_inspection.py')
    assert fi.function == 'frameinfo'
    assert fi.assignments['somevalue'] == 'spam'
