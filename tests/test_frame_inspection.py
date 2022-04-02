import sys
import pytest
import stackprinter.extraction as ex

@pytest.fixture
def frameinfo():
    somevalue = 'spam'

    supersecretthings = "gaaaah"
    class Blob():
        pass
    someobject = Blob()
    someobject.secretattribute = "uarrgh"

    fr = sys._getframe()
    hidden = [r".*secret.*", r"someobject\..*attribute"]
    return ex.get_info(fr, suppressed_vars=hidden)

def test_frameinfo(frameinfo):
    fi = frameinfo
    assert fi.filename.endswith('test_frame_inspection.py')
    assert fi.function == 'frameinfo'
    assert fi.assignments['somevalue'] == 'spam'
    assert isinstance(fi.assignments['supersecretthings'], ex.CensoredVariable)
    assert isinstance(fi.assignments['someobject.secretattribute'], ex.CensoredVariable)
