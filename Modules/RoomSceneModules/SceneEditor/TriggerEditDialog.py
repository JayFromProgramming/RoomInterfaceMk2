from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QDialog, QLineEdit


class TriggerEditDialog(QDialog):
    def __init__(self, subtype, value):
        super().__init__()
        self.subtype = subtype
        self.value = value
        self.initUI()

    def initUI(self):
        """Trigger edits only edit the subtype and value. They also provide the ability to delete the trigger."""
        self.layout = QVBoxLayout()

        self.subtype_edit = QLineEdit()
        self.subtype_edit.setText(self.subtype)
        self.subtype_edit.setFixedSize(200, 30)
        self.layout.addWidget(self.subtype_edit)

        self.value_edit = QLineEdit()
        self.value_edit.setText(self.value)
        # Adjust the size of the value edit to not be too large
        self.value_edit.setFixedSize(200, 30)
        self.layout.addWidget(self.value_edit)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        self.layout.addWidget(self.confirm_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

    def accept(self):
        self.subtype = self.subtype_edit.text()
        self.value = self.value_edit.text()
        self.done(1)

    def delete(self):
        self.done(2)

    def reject(self):
        self.done(0)


