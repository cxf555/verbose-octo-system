"""Detail panel showing process or thread information."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QGroupBox, QGridLayout, QHeaderView,
)
from PySide6.QtCore import Qt

from ..models.process_info import ProcessInfo, ThreadInfo
from ..utils.helpers import (
    format_bytes, format_duration, format_datetime, format_number, format_hex,
    get_process_priority_name,
)
from ..utils.win32_constants import (
    THREAD_PRIORITY_NAMES, IO_PRIORITY_NAMES, PAGE_PRIORITY_NAMES,
)


class DetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.tabs = QTabWidget()
        self.process_tab = ProcessDetailTab()
        self.thread_tab = ThreadDetailTab()
        self.modules_tab = ModulesTab()
        self.network_tab = NetworkTab()

        self.tabs.addTab(self.process_tab, "进程")
        self.tabs.addTab(self.thread_tab, "线程")
        self.tabs.addTab(self.modules_tab, "模块")
        self.tabs.addTab(self.network_tab, "网络")

        layout.addWidget(self.tabs)

    def show_process(self, proc: ProcessInfo):
        self.process_tab.set_process(proc)
        self.modules_tab.set_modules(proc.modules)
        self.network_tab.set_connections(proc.network_connections)
        self.tabs.setCurrentIndex(0)

    def show_thread(self, thread: ThreadInfo):
        self.thread_tab.set_thread(thread)
        self.tabs.setCurrentIndex(1)

    def clear(self):
        self.process_tab.clear()
        self.thread_tab.clear()
        self.modules_tab.clear()
        self.network_tab.clear()


class ProcessDetailTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-family: 'Cascadia Code', 'Consolas', monospace;")
        layout.addWidget(self.text)

    def set_process(self, proc: ProcessInfo):
        lines = [
            f"<b>进程名:</b> {proc.name} (PID: {proc.pid})",
            f"<b>父进程 PID:</b> {proc.parent_pid or 'N/A'}",
            f"<b>完整路径:</b> {proc.full_path or 'N/A'}",
            f"<b>命令行:</b> {proc.command_line or 'N/A'}",
            f"<b>会话 ID:</b> {proc.session_id}",
            f"<b>基础优先级:</b> {get_process_priority_name(proc.base_priority)} ({proc.base_priority})",
            "",
            f"<b>── 性能 ──</b>",
            f"<b>CPU 使用率:</b> {proc.cpu_percent:.2f}%",
            f"<b>CPU 用户时间:</b> {proc.cpu_user_time.time().strftime('%H:%M:%S') if proc.cpu_user_time else 'N/A'}",
            f"<b>CPU 内核时间:</b> {proc.cpu_kernel_time.time().strftime('%H:%M:%S') if proc.cpu_kernel_time else 'N/A'}",
            f"<b>线程数:</b> {proc.thread_count}",
            f"<b>句柄数:</b> {format_number(proc.handle_count)}",
            "",
            f"<b>── 内存 ──</b>",
            f"<b>工作集:</b> {format_bytes(proc.memory_working_set)}",
            f"<b>私有内存:</b> {format_bytes(proc.memory_private_bytes)}",
            f"<b>虚拟内存:</b> {format_bytes(proc.memory_virtual_size)}",
            f"<b>峰值工作集:</b> {format_bytes(proc.memory_peak_working_set)}",
            f"<b>页面错误:</b> {format_number(proc.page_faults)}",
            "",
            f"<b>── I/O ──</b>",
            f"<b>读取:</b> {format_bytes(proc.io_read_bytes)}",
            f"<b>写入:</b> {format_bytes(proc.io_write_bytes)}",
            "",
            f"<b>── 时间 ──</b>",
            f"<b>启动时间:</b> {format_datetime(proc.start_time)}",
            f"<b>运行时长:</b> {format_duration(proc.running_time)}",
            "",
            f"<b>── 安全 ──</b>",
            f"<b>GDI 对象:</b> {proc.gdi_objects or 'N/A'}",
            f"<b>USER 对象:</b> {proc.user_objects or 'N/A'}",
            f"<b>完整性级别:</b> {proc.integrity_level or 'N/A'}",
            f"<b>DEP:</b> {'是' if proc.dep_enabled else '否'}",
            f"<b>ASLR:</b> {'是' if proc.aslr_enabled else '否'}",
        ]
        self.text.setHtml("<br>".join(lines))

    def clear(self):
        self.text.clear()


class ThreadDetailTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-family: 'Cascadia Code', 'Consolas', monospace;")
        layout.addWidget(self.text)

    def set_thread(self, t: ThreadInfo):
        lines = [
            f"<b>线程 ID:</b> {t.tid}",
            f"<b>所属进程 PID:</b> {t.pid}",
            f"<b>CPU 用户时间:</b> {t.cpu_user_time.time().strftime('%H:%M:%S') if t.cpu_user_time else 'N/A'}",
            f"<b>CPU 内核时间:</b> {t.cpu_kernel_time.time().strftime('%H:%M:%S') if t.cpu_kernel_time else 'N/A'}",
            "",
            f"<b>── 优先级 ──</b>",
            f"<b>基础优先级:</b> {THREAD_PRIORITY_NAMES.get(t.base_priority, str(t.base_priority))} ({t.base_priority})",
            f"<b>动态优先级:</b> {t.dynamic_priority}",
            f"<b>IO 优先级:</b> {IO_PRIORITY_NAMES.get(t.io_priority, str(t.io_priority)) if t.io_priority is not None else 'N/A'}",
            f"<b>页面优先级:</b> {PAGE_PRIORITY_NAMES.get(t.page_priority, str(t.page_priority)) if t.page_priority is not None else 'N/A'}",
            "",
            f"<b>── 状态 ──</b>",
            f"<b>状态:</b> {t.thread_state or 'N/A'}",
            f"<b>等待原因:</b> {t.wait_reason or 'N/A'}",
            f"<b>挂起计数:</b> {t.suspend_count}",
            "",
            f"<b>── 上下文 ──</b>",
            f"<b>上下文切换:</b> {format_number(t.context_switches)}",
            f"<b>起始地址:</b> {format_hex(t.start_address, 64) if t.start_address else 'N/A'}",
            f"<b>周期时间:</b> {format_number(t.cycle_time) if t.cycle_time else 'N/A'}",
            "",
            f"<b>── 亲和性 ──</b>",
            f"<b>亲和性掩码:</b> {format_hex(t.affinity_mask, 64) if t.affinity_mask else 'N/A'}",
            f"<b>CPU %:</b> {t.cpu_percent:.2f}%" if t.cpu_percent else "<b>CPU %:</b> N/A",
        ]
        if t.is_suspicious:
            lines.insert(0, '<span style="color:#f38ba8;"><b>⚠ 可疑</b></span>')
        self.text.setHtml("<br>".join(lines))

    def clear(self):
        self.text.clear()


class ModulesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["模块名", "基址", "大小", "路径"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 140)
        self.tree.setColumnWidth(2, 80)
        layout.addWidget(self.tree)

    def set_modules(self, modules: list):
        self.tree.clear()
        for mod in modules[:200]:
            item = QTreeWidgetItem([
                mod.name,
                format_hex(mod.base_address, 64),
                format_bytes(mod.size),
                mod.path,
            ])
            self.tree.addTopLevelItem(item)

    def clear(self):
        self.tree.clear()


class NetworkTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["协议", "本地地址", "远程地址", "状态"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.setColumnWidth(0, 90)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 200)
        layout.addWidget(self.tree)

    def set_connections(self, connections: list):
        self.tree.clear()
        for conn in connections[:500]:
            local = f"{conn.local_addr}:{conn.local_port}"
            remote = f"{conn.remote_addr}:{conn.remote_port}" if conn.remote_port else conn.remote_addr
            item = QTreeWidgetItem([
                f"{conn.protocol} ({conn.family})",
                local,
                remote,
                conn.state,
            ])
            if conn.state == "LISTEN":
                item.setForeground(0, __import__("PySide6.QtGui").QColor("#a6e3a1"))
            elif conn.state == "ESTABLISHED":
                item.setForeground(0, __import__("PySide6.QtGui").QColor("#89b4fa"))
            self.tree.addTopLevelItem(item)

    def clear(self):
        self.tree.clear()
