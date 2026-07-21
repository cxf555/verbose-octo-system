"""Collect handle information per process via NtQuerySystemInformation."""

import ctypes
from ctypes import wintypes

from ..models.process_info import HandleInfo
from ..utils.win32_api import (
    ntdll, kernel32,
    SYSTEM_HANDLE_INFORMATION, SYSTEM_HANDLE_TABLE_ENTRY_INFO,
    SystemHandleInformation,
)


# Handle type index -> name (simplified)
_KNOWN_HANDLE_TYPES = {
    5: "File",
    7: "Event",
    8: "Key",
    9: "Section",
    10: "Semaphore",
    12: "Mutant",
    13: "Thread",
    14: "Process",
    15: "Token",
    17: "Directory",
    18: "SymbolicLink",
    19: "Timer",
    20: "Job",
    21: "KeyedEvent",
    22: "WindowStation",
    23: "Desktop",
    24: "TpWorkerFactory",
    25: "IoCompletion",
    26: "ALPC Port",
    28: "IRPTimer",
    29: "WaitCompletionPacket",
    31: "EtwRegistration",
}


def collect_all_handles() -> list[tuple[int, HandleInfo]]:
    """Collect all open handles system-wide.
    Returns list of (pid, HandleInfo). Requires SeDebugPrivilege for full results.
    """
    results = []
    buf_size = 0x100000  # 1MB initial buffer

    for _ in range(4):  # retry with larger buffer
        buf = ctypes.create_string_buffer(buf_size)
        ret_len = wintypes.DWORD()

        status = ntdll.NtQuerySystemInformation(
            SystemHandleInformation, buf, buf_size, ctypes.byref(ret_len)
        )

        if status == 0:
            break
        elif status == 0xC0000004:  # STATUS_INFO_LENGTH_MISMATCH
            buf_size *= 2
            continue
        else:
            return results  # failed
    else:
        return results

    info = ctypes.cast(buf, ctypes.POINTER(SYSTEM_HANDLE_INFORMATION)).contents
    num_handles = info.NumberOfHandles

    # The Handles field is a flexible array. Get a pointer to the first element.
    entry_ptr = ctypes.cast(
        ctypes.addressof(info.Handles),
        ctypes.POINTER(SYSTEM_HANDLE_TABLE_ENTRY_INFO)
    )

    for i in range(num_handles):
        entry = entry_ptr[i]
        type_name = _KNOWN_HANDLE_TYPES.get(entry.ObjectTypeIndex,
                                             f"Type_{entry.ObjectTypeIndex:02X}")
        results.append((
            entry.UniqueProcessId,
            HandleInfo(
                handle_value=entry.HandleValue,
                handle_type=type_name,
                granted_access=entry.GrantedAccess,
            )
        ))

    return results


def attach_handles_to_processes(processes: list, all_handles: list[tuple[int, HandleInfo]]):
    """Attach handles to matching processes in-place."""
    pid_map: dict[int, list[HandleInfo]] = {}
    for pid, handle in all_handles:
        if pid not in pid_map:
            pid_map[pid] = []
        pid_map[pid].append(handle)

    for proc in processes:
        proc.handle_count = len(pid_map.get(proc.pid, []))
        proc.handles = pid_map.get(proc.pid, [])
