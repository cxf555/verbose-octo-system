"""CPU affinity editor dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QGroupBox, QGridLayout, QMessageBox,
)
from PySide6.QtCore import Qt

from ..utils.helpers import cpu_affinity_to_cores, cores_to_affinity


class AffinityDialog(QDialog):
    def __init__(self, current_mask: int, max_cores: int = 64, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CPU 亲和性")
        self.setMinimumWidth(400)
        self._max_cores = min(max_cores, 64)
        self._current_mask = current_mask
        self._selected_cores = set(cpu_affinity_to_cores(current_mask))
        self._result_mask = current_mask

        layout = QVBoxLayout(self)

        info = QLabel(f"选择此线程可以运行的 CPU 核心。\n当前掩码: 0x{current_mask:X}")
        info.setWordWrap(True)
        layout.addWidget(info)

        group = QGroupBox("CPU 核心")
        grid = QGridLayout(group)
        self._checkboxes = []

        cols = 8
        for i in range(self._max_cores):
            cb = QCheckBox(f"CPU {i}")
            cb.setChecked(i in self._selected_cores)
            self._checkboxes.append(cb)
            grid.addWidget(cb, i // cols, i % cols)

        layout.addWidget(group)

        quick_layout = QHBoxLayout()
        all_btn = QPushButton("全选")
        none_btn = QPushButton("全不选")
        even_btn = QPushButton("偶数核")
        odd_btn = QPushButton("奇数核")
        all_btn.clicked.connect(lambda: self._set_all(True))
        none_btn.clicked.connect(lambda: self._set_all(False))
        even_btn.clicked.connect(self._set_even)
        odd_btn.clicked.connect(self._set_odd)
        quick_layout.addWidget(all_btn)
        quick_layout.addWidget(none_btn)
        quick_layout.addWidget(even_btn)
        quick_layout.addWidget(odd_btn)
        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("应用")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self._apply)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _set_all(self, checked: bool):
        for cb in self._checkboxes:
            cb.setChecked(checked)

    def _set_even(self):
        for i, cb in enumerate(self._checkboxes):
            cb.setChecked(i % 2 == 0)

    def _set_odd(self):
        for i, cb in enumerate(self._checkboxes):
            cb.setChecked(i % 2 == 1)

    def _apply(self):
        cores = [i for i, cb in enumerate(self._checkboxes) if cb.isChecked()]
        if not cores:
            QMessageBox.warning(self, "错误", "至少需要选择一个 CPU 核心。")
            return
        self._result_mask = cores_to_affinity(cores)
        self.accept()

    @property
    def result_mask(self) -> int:
        return self._result_mask
