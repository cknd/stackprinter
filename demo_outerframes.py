import traceback
import stackprinter


def function1(x):
    raise RuntimeError('xxx')

def function2(x):
    function1(x)

def function3(x):
    try:
        function2(x)
    except Exception:
        # traceback.print_exc()
        stackprinter.show(style='color', add_prior_calls=True, add_summary=True)

def function4(x):
    function3(x)

def function5(x):
    function4(x)

function5(x=1)



# import stackprinter
# stackprinter.set_excepthook(style='darkbg2', add_prior_calls=True, add_summary=True)

# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import Qt

# class Window(QWidget):
#     def __init__(self):
#         super().__init__()
#         b1 = QPushButton('1')
#         b2 = QPushButton('2')
#         b1.clicked.connect(self.f1)
#         b2.clicked.connect(self.f2)
#         layout = QVBoxLayout(self)
#         layout.addWidget(b1)
#         layout.addWidget(b2)
#         self.setLayout(layout)
#     def f1(self, _):
#         self.inputMethodQuery(Qt.ImAnchorPosition)
#     def f2(self, _):
#         self.inputMethodQuery(Qt.ImAnchorPosition)
#     def inputMethodQuery(self, query):
#         if query == Qt.ImCursorPosition:
#             self.h()
#         else:
#             return super().inputMethodQuery(query) # Call 'g()'
#     def h(self):
#         raise Exception()

# app = QApplication([])
# window = Window()
# window.show()
# app.exec()