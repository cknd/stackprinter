import random
import colorsys


__all__ = ['plaintext', 'color',
           'darkbg', 'darkbg2', 'darkbg3',
           'lightbg', 'lightbg2', 'lightbg3']

class ColorScheme():

    def __getitem__(self, name):
        raise NotImplemented

    def get_random(self, seed, highlight):
        raise NotImplemented


class plaintext(ColorScheme):

    def __getitem__(self, name):
        return "%s"

    def get_random(self, seed, highlight):
        return "%s"


class ansi(ColorScheme):
    colors = {
        'exception_type': '31',
        'exception_msg': '31',
        'highlight': '1;31',
        'header': '0',
        'lineno': '1',
        'arrow_lineno': '1',
        'dots': '0',
        'source_bold': '0',
        'source_default': '0',
        'source_comment': '0',
        'var_invisible': '0',
    }

    def __init__(self):
        self.rng = random.Random()

    def __getitem__(self, name):
        return self._ansi_tpl(self.colors[name])

    def get_random(self, seed, highlight):
        self.rng.seed(seed)
        random_code = str(self.rng.randint(32, 36))
        if self.rng.choice((True, False)):
            random_code = "1;" + random_code
        return self._ansi_tpl(random_code)

    @staticmethod
    def _ansi_tpl(color_code):
        return f"\u001b[{color_code}m%s\u001b[0m"


class HslScheme(ColorScheme):
    colors = {}

    def __getitem__(self, name):
        return self._ansi_tpl(*self.colors[name])

    def get_random(self, seed, highlight):
        self.rng.seed(seed)
        return self._ansi_tpl(*self._random_color(highlight))

    def _random_color(self, highlight):
        raise NotImplemented

    @staticmethod
    def _ansi_tpl(hue, sat, val, bold=False):
        r_, g_, b_ = colorsys.hsv_to_rgb(hue, sat, val)
        r = int(round(r_*5))
        g = int(round(g_*5))
        b = int(round(b_*5))
        point = 16 + 36 * r + 6 * g + b

        bold_tp = '1;' if bold else ''
        code_tpl = ('\u001b[%s38;5;%dm' % (bold_tp, point)) + '%s\u001b[0m'
        return code_tpl


class darkbg(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05,0.7)
        sat = 1.0
        val = 0.5
        bold = highlight

        return hue, sat, val, bold



class darkbg2(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05,0.7)
        sat = 1.0
        val = 0.8
        bold = highlight

        return hue, sat, val, bold


class darkbg3(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05,0.7)
        sat = 1.0
        val = 0.8 if highlight else 0.5
        bold = highlight

        return hue, sat, val, bold


class lightbg(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05, 0.7)
        sat = 1.0
        val = 0.5
        bold = highlight

        return hue, sat, val, bold


class lightbg2(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05, 0.7)
        sat = 1.0
        val = 0.5
        bold = True

        return hue, sat, val, bold

class lightbg3(HslScheme):
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

    def _random_color(self, highlight):
        hue = self.rng.uniform(0.05, 0.7)
        sat = 1.0
        val = 0.5
        bold = True

        return hue, sat, val, bold



color = darkbg2


if __name__ == '__main__':
    scheme = darkbg3()
    for attr in [
        'exception_type',
        'exception_msg',
        'highlight',
        'header',
        'lineno',
        'arrow_lineno',
        'dots',
        'source_bold',
        'source_default',
        'source_comment',
        'var_invisible',
    ]:
        print(scheme[attr] % attr)
    exit()
    import numpy as np
    hsl_scheme = HslScheme()

    for hue in np.arange(0,1.05,0.05):
        print('\n\nhue %.2f\nsat' % hue)
        for sat in np.arange(0,1.05,0.05):
            print('%.2f  ' % sat, end='')
            for val in np.arange(0,1.05,0.05):
                tpl = hsl_scheme._ansi_tpl(hue, sat, val)
                # number = " (%.1f %.1f %.1f)" % (hue, sat, val)
                number = ' %.2f' % val
                print(tpl % number, end='')
            print('  %.2f' % sat)
