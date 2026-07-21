"""Collect loaded modules (DLLs) for processes."""

import ctypes
from ctypes import wintypes

from ..models.process_info import ModuleInfo
from ..utils.win32_api import (
    kernel32, MODULEENTRY32, TH32CS_SNAPMODULE, TH32CS_SNAPMODULE32,
)
from ..utils.win32_constants import INVALID_HANDLE_VALUE


def collect_modules_for_process(pid: int) -> list[ModuleInfo]:
    """Get loaded modules for a given process."""
    modules = []

    for snap_flags in (TH32CS_SNAPMODULE, TH32CS_SNAPMODULE32):
        snapshot = kernel32.CreateToolhelp32Snapshot(snap_flags, pid)
        if not snapshot or snapshot == INVALID_HANDLE_VALUE:
            continue

        try:
            me = MODULEENTRY32()
            me.dwSize = ctypes.sizeof(me)
            if kernel32.Module32First(snapshot, ctypes.byref(me)):
                while True:
                    base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value or 0
                    modules.append(ModuleInfo(
                        name=me.szModule.decode("utf-8", errors="replace"),
                        path=me.szExePath.decode("utf-8", errors="replace"),
                        base_address=base,
                        size=me.modBaseSize,
                        pid=pid,
                    ))
                    if not kernel32.Module32Next(snapshot, ctypes.byref(me)):
                        break
        finally:
            kernel32.CloseHandle(snapshot)

    return modules


def collect_modules_for_processes(processes: list[tuple[int, list]]):
    """Attach modules to processes in-place. processes is list of (pid, modules_list)."""
    for pid, mod_list in processes:
        mods = collect_modules_for_process(pid)
        mod_list.extend(mods)
