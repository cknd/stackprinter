from IPython.terminal.embed import InteractiveShellEmbed
shell = InteractiveShellEmbed()
shell.enable_matplotlib()

# import sys
# print(sys.excepthook)
import stackprinter
stackprinter.set_excepthook(style='darkbg2')
# print(sys.excepthook)

# def sptb(*_, **__):
#     stackprinter.show(style='darkbg2')

# shell.showtraceback = sptb
shell()