import numpy as np
import pytest


def spam(thing,
         various=None,
         other=None,
         things=None):
    """
    some very long
    doc string
    """
    bla = """ another triple quoted string """
    X = np.zeros((10,10))
    X[0,0] = 1
    boing = outer_scope_thing['and']
    foo = somelist
    do_something = lambda val: spam_spam_spam(val + outer_scope_thing['and'] + boing)
    for k in X:
        if np.sum(k) != 0:
            return [[do_something(val) for val in row] for row in X]


class Hovercraft():
    @property
    def eels(self):
        try:
            return spam_spam('')
        except Exception as e:
            raise Exception('ahoi!') from e


blub = '🐍'
somelist = [1,2,3,np.zeros((23,42)), np.ones((42,23))]
outer_scope_thing = {'various': 'things',
                     123: 'in a dict',
                     'and': np.ones((42,23)),
                     'in a list': somelist}

def deco(f):
    bla = '🐍🐍🐍'
    def closure(*args, **kwargs):
        kwargs['zap'] = bla
        return f(*args, **kwargs)

    return closure

@deco
def spam_spam(boing, zap='!'):
    thing = boing + zap
    spam(thing)


def spam_spam_spam(val):
    if np.sum(val) != 42:
        bla = val.T.\
              T.T.\
              T

        # here is a comment \
        # that has backslashes \
        # for some reason
        eels = "here is a "\
               "multi line "\
               "string"
        # np.reshape(bla, 9000)
        try:
            bla.nonexistant_attribute
        except:
            pass

        boing = np.\
                random.rand(*bla.T.\
                        T.T)
        raise Exception('something happened')

####

@pytest.fixture
def sourcelines():
    with open(__file__, 'r') as sf:
        lines = sf.readlines()
    return lines


if __name__ == '__main__':
  import stackprinter
  try:
      Hovercraft().eels
  except:
      stackprinter.show(style='darkbg')