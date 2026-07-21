"""Real-time CPU usage chart using QtCharts."""

from collections import deque

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtGui import QColor, QPen

from ..models.snapshot import Snapshot


class CpuChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel("CPU 使用率历史")
        self.title_label.setStyleSheet("font-weight: bold; padding: 4px;")

        self._series = QLineSeries()
        self._series.setName("系统 CPU %")
        self._series.setColor(QColor("#89b4fa"))
        pen = QPen(QColor("#89b4fa"))
        pen.setWidth(2)
        self._series.setPen(pen)

        self._chart = QChart()
        self._chart.addSeries(self._series)
        self._chart.setTitle("")
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        self._chart.legend().hide()
        self._chart.setBackgroundBrush(QColor("#1e1e2e"))
        self._chart.setPlotAreaBackgroundBrush(QColor("#1e1e2e"))
        self._chart.setPlotAreaBackgroundVisible(True)

        self._axis_x = QDateTimeAxis()
        self._axis_x.setFormat("HH:mm:ss")
        self._axis_x.setLabelsColor(QColor("#a6adc8"))
        self._axis_x.setGridLineColor(QColor("#313244"))
        self._chart.addAxis(self._axis_x, Qt.AlignBottom)
        self._series.attachAxis(self._axis_x)

        self._axis_y = QValueAxis()
        self._axis_y.setRange(0, 100)
        self._axis_y.setLabelFormat("%d%%")
        self._axis_y.setLabelsColor(QColor("#a6adc8"))
        self._axis_y.setGridLineColor(QColor("#313244"))
        self._chart.addAxis(self._axis_y, Qt.AlignLeft)
        self._series.attachAxis(self._axis_y)

        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(self._chart_view.renderHints())

        self._buffer = deque(maxlen=60)

        layout.addWidget(self.title_label)
        layout.addWidget(self._chart_view)

    def add_point(self, snapshot: Snapshot):
        timestamp = snapshot.timestamp.timestamp() * 1000
        cpu = snapshot.system.cpu_percent

        self._buffer.append((timestamp, cpu))
        self._series.clear()
        for ts, val in self._buffer:
            self._series.append(ts, val)

        if self._buffer:
            min_ts = self._buffer[0][0]
            max_ts = self._buffer[-1][0]
            if max_ts - min_ts < 5000:
                max_ts = min_ts + 5000
            self._axis_x.setRange(
                QDateTime.fromMSecsSinceEpoch(int(min_ts)),
                QDateTime.fromMSecsSinceEpoch(int(max_ts)),
            )
