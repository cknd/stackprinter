import numpy
import stackprinter


def dangerous_function(blub):
    return sorted(blub, key=sum)

try:
    somelist = [[1,2], [3,4]]
    anotherlist = [['5', 6]]
    spam = numpy.zeros((3,3))
    dangerous_function(somelist + anotherlist)
except:
    stackprinter.show(style='plaintext', source_lines=4)
