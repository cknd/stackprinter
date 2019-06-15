import random


__all__ = ['color', 'darkbg', 'darkbg2', 'darkbg3',
           'lightbg', 'lightbg2', 'lightbg3']

class ColorScheme():

    def __getitem__(self, name):
        raise NotImplemented

    def get_random(self):
        raise NotImplemented


class darkbg(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0.0, 0.9, 0.6, False),
              'exception_msg':  (0.0, 0.9, 0.6, True),

              'highlight':      (0.0, 0., 0.8, True),
              'header':         (0., 0., 0.3, False),

              'lineno':         (0., 0.0, 0.1, False),
              'arrow_lineno':   (0., 0.0, 0.2, True),
              'dots':           (0., 0.0, 0.6, False),

              'source_bold':    (0.,0., 0.6, True),
              'source_default': (0.,0., 0.7, False),
              'source_comment': (0.,0.,0.2, False),
              'var_invisible':  (0.6, 0.4, 0.4, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05,0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1. #1. if highlight else 0.5
        val = 0.5 #1. if highlight else 0.3
        bold = highlight

        return hue, sat, val, bold



class darkbg2(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0., 1., 0.8, True),
              'exception_msg':  (0., 1., 0.8, True),

              'highlight':      (0., 0., 1., True),
              'header':         (0, 0, 0.6, False),

              'lineno':         (0, 0, 0.2, True),
              'arrow_lineno':   (0, 0, 0.8, True),
              'dots':           (0, 0, 0.4, False),

              'source_bold':    (0.,0.,0.8, True),
              'source_default': (0.,0.,0.8, False),
              'source_comment': (0.,0.,0.2, False),
              'var_invisible':  (0.6, 0.4, 0.4, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05,0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1. if highlight else 1.
        val = 0.8 #if highlight else 0.5
        bold = highlight

        return hue, sat, val, bold


class darkbg3(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0., 1., 0.8, True),
              'exception_msg':  (0., 1., 0.8, True),
              'highlight':      (0., 1., 0.8, True),
              'header':         (0, 0, 0.8, True),
              'lineno':         (0, 0, 0.2, True),
              'arrow_lineno':   (0, 0, 0.8, True),
              'dots':           (0, 0, 0.4, False),
              'source_bold':    (0.,0.,0.8, True),
              'source_default': (0.,0.,0.8, False),
              'source_comment': (0.,0.,0.2, False),
              'var_invisible':  (0.6, 0.4, 0.4, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05,0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1. if highlight else 1.
        val = 0.8 if highlight else 0.5
        bold = highlight

        return hue, sat, val, bold


class lightbg(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0.0, 1., 0.6, False),
              'exception_msg':  (0.0, 1., 0.6, True),

              'highlight':      (0.0, 0, 0., True),
              'header':         (0, 0, 0.2, False),

              'lineno':         (0, 0, 0.8, True),
              'arrow_lineno':   (0, 0, 0.3, True),
              'dots':           (0, 0, 0.4, False),
              'source_bold':    (0.,0.,0.2, True),
              'source_default': (0.,0.,0.1, False),
              'source_comment': (0.,0.,0.6, False),
              'var_invisible':  (0.6, 0.4, 0.2, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05, 0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1.
        val = 0.5 #0.5 #0.6 if highlight else 0.2
        bold = highlight

        return hue, sat, val, bold


class lightbg2(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0.0, 1., 0.6, False),
              'exception_msg':  (0.0, 1., 0.6, True),

              'highlight':      (0.0, 0, 0., True),
              'header':         (0, 0, 0.1, False),

              'lineno':         (0, 0, 0.5, True),
              'arrow_lineno':   (0, 0, 0.1, True),
              'dots':           (0, 0, 0.4, False),

              'source_bold':    (0.,0.,0.1, True),
              'source_default': (0.,0.,0., False),
              'source_comment': (0.,0.,0.6, False),
              'var_invisible':  (0.6, 0.4, 0.2, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05, 0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1.
        val = 0.5
        bold = True

        return hue, sat, val, bold

class lightbg3(ColorScheme):
                              # Hue, Sat, Val, Bold
    colors = {'exception_type': (0.0, 1., 0.7, False),
              'exception_msg':  (0.0, 1., 0.7, True),

              'highlight':      (0.0, 1., 0.6, True),
              'header':         (0, 0, 0.1, True),

              'lineno':         (0, 0, 0.5, True),
              'arrow_lineno':   (0, 0, 0.1, True),
              'dots':           (0, 0, 0.4, False),

              'source_bold':    (0.,0.,0., True),
              'source_default': (0.,0.,0., False),
              'source_comment': (0.,0.,0.6, False),
              'var_invisible':  (0.6, 0.4, 0.2, False)
             }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self.colors[name]

    def get_random(self, seed, highlight):
        self.rng.seed(seed)

        hue = self.rng.uniform(0.05, 0.7)
        # if hue < 0:
        #     hue = hue + 1
        sat = 1.
        val = 0.5
        bold = True

        return hue, sat, val, bold



color = darkbg2


if __name__ == '__main__':
    import numpy as np
    from utils import get_ansi_tpl

    for hue in np.arange(0,1.05,0.05):
        print('\n\nhue %.2f\nsat' % hue)
        for sat in np.arange(0,1.05,0.05):
            print('%.2f  ' % sat, end='')
            for val in np.arange(0,1.05,0.05):
                tpl = get_ansi_tpl(hue, sat, val)
                # number = " (%.1f %.1f %.1f)" % (hue, sat, val)
                number = ' %.2f' % val
                print(tpl % number, end='')
            print('  %.2f' % sat)
