"""Code-drawn pixel decorations: no external fonts or bitmap dependencies."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QWidget, QComboBox, QSpinBox, QStyle, QStyleOptionComboBox, QStyleOptionSpinBox


def wordmark() -> QPixmap:
    """Small 5×7 block alphabet for the brand; body text stays readable."""
    letters = {
        'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
        'I': ('11111', '00100', '00100', '00100', '00100', '00100', '11111'),
        'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
        'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
        'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
        'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
        'C': ('01111', '10000', '10000', '10000', '10000', '10000', '01111'),
        'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
        ' ': ('00000',) * 7,
    }
    result = QPixmap(240, 28)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    for index, letter in enumerate('PIXEL LOCK'):
        for y, row in enumerate(letters[letter]):
            for x, bit in enumerate(row):
                if bit == '1':
                    painter.fillRect(index * 24 + x * 4, y * 4, 4, 4, QColor('#b8fa70'))
    painter.end()
    return result


class PixelComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option,
                                          QStyle.SubControl.SC_ComboBoxArrow, self)
        painter = QPainter(self)
        for row, width in enumerate((10, 6, 2)):
            painter.fillRect(rect.center().x() - width // 2,
                             rect.center().y() - 2 + row * 2, width, 2, QColor('#73dfef'))


class PixelSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        painter = QPainter(self)
        for control, plus in ((QStyle.SubControl.SC_SpinBoxUp, True),
                              (QStyle.SubControl.SC_SpinBoxDown, False)):
            rect = self.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option, control, self)
            x, y = rect.center().x(), rect.center().y()
            painter.fillRect(x - 4, y, 8, 2, QColor('#73dfef'))
            if plus:
                painter.fillRect(x - 1, y - 3, 2, 8, QColor('#73dfef'))


GLYPHS = {
    'lock': ('0001111000', '0010000100', '0010000100', '0010000100', '0111111110',
             '0111111110', '0111001110', '0111001110', '0111111110', '0111111110'),
    'unlock': ('0000111100', '0001000010', '0001000010', '0001000000', '0111111110',
               '0111111110', '0111001110', '0111001110', '0111111110', '0111111110'),
    'folder': ('0000000000', '0111100000', '0100111110', '0100000010', '0111111110',
               '0100000010', '0100000010', '0100000010', '0111111110', '0000000000'),
    'save': ('0111111100', '0101001010', '0101001010', '0101111010', '0100000010',
             '0101111010', '0101001010', '0101001010', '0111111110', '0000000000'),
}


def pixel_icon(name: str, color: str) -> QIcon:
    canvas = QPixmap(40, 40)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    for y, row in enumerate(GLYPHS[name]):
        for x, bit in enumerate(row):
            if bit == '1':
                painter.fillRect(x * 4, y * 4, 4, 4, QColor(color))
    painter.end()
    return QIcon(canvas)


class PixelBackdrop(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#101722'))
        for y in range(8, self.height(), 24):
            for x in range(8, self.width(), 24):
                painter.fillRect(x, y, 2, 2, QColor('#243145'))
        # A stepped, cartridge-like accent beneath the title.
        for i, width in enumerate((108, 84, 60)):
            painter.fillRect(self.width() - width - 24, 5 + i * 4, width, 2, QColor('#43634c'))
        painter.end()


PIXEL_STYLESHEET = """
QWidget#root {
    color: #e7eef4;
    font-family: "Consolas", "Microsoft YaHei UI", monospace;
    font-size: 13px;
}
QFrame#panel, QFrame#previewCard {
    background: #1b2636;
    border: 3px solid #52647a;
    border-top-color: #8d9db1;
    border-left-color: #8d9db1;
    border-bottom-color: #303e52;
    border-right-color: #303e52;
}
QLabel#brand { color: #b8fa70; font-size: 32px; letter-spacing: 4px; }
QLabel#pixelEmblem { background: #182a27; border: 3px solid #b8fa70; }
QLabel#sectionTitle { color: #73dfef; font-size: 13px; letter-spacing: 0px; }
QLabel#cardTitle { color: #e7eef4; font-size: 13px; }
QLabel#subtitle, QLabel#muted, QLabel#cardHint { color: #b0bfd0; }
QLabel#badge { background: #b8fa70; border: 2px solid #e0ffb5; padding: 9px; }
QLabel#previewCanvas { background: #0b111b; border: 2px solid #52647a; color: #a5b6cc; }
QPushButton {
    background: #b8fa70; color: #111827;
    border: 2px solid #e0ffb5;
    border-right: 4px solid #5f873b;
    border-bottom: 5px solid #5f873b;
    padding: 10px 12px; letter-spacing: 0px;
}
QPushButton:hover { background: #d0ff94; border-top-color: #ffffff; }
QPushButton:pressed { background: #9bdb5c; border-width: 2px; padding-top: 13px; }
QPushButton#secondaryButton, QPushButton#languageButton {
    background: #2e4057; color: #e7eef4;
    border: 2px solid #7389a4;
    border-right: 4px solid #172436;
    border-bottom: 5px solid #172436;
}
QPushButton#secondaryButton:hover, QPushButton#languageButton:hover { background: #405874; }
QPushButton#secondaryButton:pressed, QPushButton#languageButton:pressed { background: #22334b; }
QPushButton:disabled, QPushButton#secondaryButton:disabled {
    background: #253143; color: #7e8c9f; border-color: #3a485c;
}
QPushButton:focus, QComboBox:focus, QSpinBox:focus { border-color: #ffd36b; }
QComboBox, QSpinBox { background: #101925; border: 2px solid #657992; }
QComboBox QAbstractItemView { background: #1b2636; selection-background-color: #405874; }
QLabel#statusBar { background: #73dfef; color: #101925; border: 2px solid #b9f7ff; }
QLabel#statusMeta { color: #b8fa70; }
QFrame#separator { background: #52647a; min-height: 3px; max-height: 3px; }
"""
