from PySide.QtGui import *
from PySide.QtCore import *
import sys

class Panel(QWidget):
    def __init__(self):
        super(Panel, self).__init__()

        line = QLineEdit("My Text")
        #line.setText("My Text")
        print line.text()
        line.setReadOnly(False)
        line.setMaxLength(20)
        #line.setEchoMode(QLineEdit.Password)
        #line.setAlignment(Qt.AlignCenter)
        line.setAlignment(Qt.AlignRight)
        l = ["welcome","hello","World"]
        completer = QCompleter(l)
        line.setCompleter(completer)
        line.setPlaceholderText("Enter name here...")
        #line2 = QLineEdit()

        push = QPushButton("Push")
        push.setText("New push")
        #push.setIcon(QIcon("path/to/icon.jpg"))
        push.setShortcut("u")
        push.setToolTip("push this button!")
        #push.setCheckable(True)

        checkbox = QCheckBox("checkbox")
        checkbox.setChecked(True)
        print checkbox.isChecked()

        combo = QComboBox()
        combo.addItem("Hello")
        combo.addItems(["Goodbye","World","test","Welcome"])
        print combo.currentText()
        print combo.currentIndex()
        index = combo.findText("Welcome")
        combo.setCurrentIndex(index)

        label = QLabel("Label")

        layout = QHBoxLayout()
        layout.addWidget(line)
        layout.addWidget(push)
        #layout.addWidget(line2)
        layout.addWidget(checkbox)
        layout.addWidget(combo)
        layout.addWidget(label)
        self.setLayout(layout)


app = QApplication(sys.argv)
panel = Panel()
panel.show()
app.exec_()