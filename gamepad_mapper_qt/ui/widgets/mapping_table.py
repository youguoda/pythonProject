# -*- coding: utf-8 -*-
"""映射表组件"""

from typing import Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QPushButton, QWidget,
    QHBoxLayout, QHeaderView, QAbstractItemView,
)

from core.constants import THEME
from core.slots import SLOTS

_ROW_HEIGHT = 40
_BTN_HEIGHT = 28


class MappingTable(QTableWidget):
    """24 行手柄键 → 键盘键映射表"""

    bind_requested = pyqtSignal(int)
    mapping_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mappings: Dict[int, str] = {}
        self._highlight_row: int | None = None
        self._setup_table()

    def _setup_table(self):
        self.setColumnCount(3)
        self.setRowCount(len(SLOTS))
        self.setHorizontalHeaderLabels(["手柄键", "键盘键", "操作"])
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(2, 176)

        row_font = QFont("Segoe UI", 14)
        row_font.setWeight(QFont.Weight.DemiBold)

        for row, 槽 in enumerate(SLOTS):
            name, color = 槽.name, 槽.color
            dot_name = f"● {name}"
            name_item = QTableWidgetItem(dot_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            name_item.setForeground(QColor(color))
            name_item.setFont(row_font)
            self.setItem(row, 0, name_item)

            key_item = QTableWidgetItem("-")
            key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            key_item.setForeground(QColor(THEME["subtext"]))
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            key_item.setFont(row_font)
            self.setItem(row, 1, key_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 2, 6, 2)
            btn_layout.setSpacing(6)

            bind_btn = QPushButton("绑定")
            bind_btn.setObjectName("bindBtn")
            bind_btn.setFixedHeight(_BTN_HEIGHT)
            bind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            bind_btn.clicked.connect(lambda _, r=row: self.bind_requested.emit(r))
            btn_layout.addWidget(bind_btn)

            clear_btn = QPushButton("清除")
            clear_btn.setObjectName("clearBtn")
            clear_btn.setFixedHeight(_BTN_HEIGHT)
            clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_btn.clicked.connect(lambda _, r=row: self._clear_row(r))
            btn_layout.addWidget(clear_btn)

            self.setCellWidget(row, 2, btn_widget)
            self.setRowHeight(row, _ROW_HEIGHT)

        self.cellDoubleClicked.connect(self._on_double_click)

    def _on_double_click(self, row: int, _col: int):
        self.bind_requested.emit(row)

    def _clear_row(self, row: int):
        self._mappings.pop(row, None)
        item = self.item(row, 1)
        if item:
            item.setText("-")
            item.setForeground(QColor(THEME["subtext"]))
        self.mapping_changed.emit()

    def set_mapping(self, button_index: int, key_name: str):
        self._mappings[button_index] = key_name
        item = self.item(button_index, 1)
        if item:
            item.setText(key_name)
            item.setForeground(QColor(THEME["accent"]))
        self.mapping_changed.emit()

    def load_mappings(self, mappings: Dict[int, str]):
        self._mappings = dict(mappings)
        for row in range(len(SLOTS)):
            key = self._mappings.get(row, "-")
            item = self.item(row, 1)
            if item:
                item.setText(key if key else "-")
                if key and key != "-":
                    item.setForeground(QColor(THEME["accent"]))
                else:
                    item.setForeground(QColor(THEME["subtext"]))

    def get_mappings(self) -> Dict[int, str]:
        return dict(self._mappings)

    def highlight_button(self, button_index: int | None):
        if self._highlight_row is not None:
            for col in range(3):
                item = self.item(self._highlight_row, col)
                if item:
                    item.setBackground(QColor(THEME["card"]))

        self._highlight_row = button_index
        if button_index is not None:
            for col in range(3):
                item = self.item(button_index, col)
                if item:
                    item.setBackground(QColor(THEME["hover"]))

    def clear_highlight_if(self, button_index: int):
        if self._highlight_row == button_index:
            self.highlight_button(None)

    def clear_all(self):
        self._mappings.clear()
        for row in range(len(SLOTS)):
            item = self.item(row, 1)
            if item:
                item.setText("-")
                item.setForeground(QColor(THEME["subtext"]))
        self.mapping_changed.emit()
