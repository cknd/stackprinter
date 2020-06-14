if __name__ == '__main__':
    import stackprinter
    from tests.source import Hovercraft

    try:
        Hovercraft().eels()
    except:
        # raise
        stackprinter.show(style='darkbg2',
                          line_wrap=40,
                          reverse=False,
                          suppressed_paths=[r"lib/python.*/site-packages/numpy"])