"""Collect thread-level details using kernel32 APIs."""

import ctypes
from ctypes import wintypes
import psutil

from ..models.process_info import ThreadInfo
from ..utils.win32_api import (
    kernel32, THREADENTRY32, TH32CS_SNAPTHREAD,
    query_thread_basic_info, query_thread_start_address,
    query_thread_io_priority, query_thread_page_priority,
    query_thread_cycle_time, get_thread_times,
    PROCESSENTRY32,
)
from ..utils.win32_constants import (
    THREAD_STATE_NAMES, WAIT_REASON_NAMES,
    THREAD_QUERY_INFORMATION, INVALID_HANDLE_VALUE,
    THREAD_PRIORITY_NAMES, IO_PRIORITY_NAMES, PAGE_PRIORITY_NAMES,
)


def collect_threads_for_process(pid: int) -> list[ThreadInfo]:
    """Enumerate all threads for a given process using Toolhelp snapshot."""
    threads = []
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if not snapshot or snapshot == INVALID_HANDLE_VALUE:
        return threads

    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(te)
        if kernel32.Thread32First(snapshot, ctypes.byref(te)):
            while True:
                if te.th32OwnerProcessID == pid:
                    ti = _build_thread_info(te)
                    threads.append(ti)
                    try:
                        _enrich_thread_info(ti)
                    except Exception:
                        pass
                if not kernel32.Thread32Next(snapshot, ctypes.byref(te)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)

    return threads


def collect_threads_for_all(processes: list):
    """Collect threads for all processes and attach them."""
    # Get all threads in one snapshot
    proc_map = {p.pid: p for p in processes}

    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if not snapshot or snapshot == INVALID_HANDLE_VALUE:
        return

    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(te)
        if kernel32.Thread32First(snapshot, ctypes.byref(te)):
            while True:
                pid = te.th32OwnerProcessID
                if pid in proc_map:
                    ti = _build_thread_info(te)
                    proc_map[pid].threads.append(ti)
                    try:
                        _enrich_thread_info(ti)
                    except Exception:
                        pass

                if not kernel32.Thread32Next(snapshot, ctypes.byref(te)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)


def _build_thread_info(te) -> ThreadInfo:
    return ThreadInfo(
        tid=te.th32ThreadID,
        pid=te.th32OwnerProcessID,
        base_priority=te.tpBasePri,
        dynamic_priority=te.tpDeltaPri,
    )


def _enrich_thread_info(ti: ThreadInfo):
    """Get detailed thread info via OpenThread + NtQueryInformationThread."""
    try:
        h_thread = kernel32.OpenThread(THREAD_QUERY_INFORMATION, False, ti.tid)
    except OSError:
        return

    try:
        # Basic info (affinity, priorities)
        try:
            basic = query_thread_basic_info(h_thread)
            ti.base_priority = basic.BasePriority
            ti.dynamic_priority = basic.Priority
            ti.affinity_mask = basic.AffinityMask or None
        except Exception:
            pass

        # Start address
        addr = query_thread_start_address(h_thread)
        if addr:
            ti.start_address = addr

        # IO priority
        io_prio = query_thread_io_priority(h_thread)
        if io_prio is not None:
            ti.io_priority = io_prio

        # Page priority
        page_prio = query_thread_page_priority(h_thread)
        if page_prio is not None:
            ti.page_priority = page_prio

        # Cycle time
        cycles = query_thread_cycle_time(h_thread)
        if cycles is not None:
            ti.cycle_time = cycles

        # Thread times
        try:
            create, exit, kernel, user = get_thread_times(h_thread)
            ti.cpu_kernel_time = kernel
            ti.cpu_user_time = user
        except Exception:
            pass

    finally:
        kernel32.CloseHandle(h_thread)


def get_thread_state_name(state_code):
    return THREAD_STATE_NAMES.get(state_code, f"Unknown({state_code})")


def get_wait_reason_name(reason_code):
    return WAIT_REASON_NAMES.get(reason_code, f"Unknown({reason_code})")
