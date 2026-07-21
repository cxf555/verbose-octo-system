"""Windows API bindings via ctypes for deep thread/process inspection."""

import ctypes
from ctypes import wintypes

from .win32_constants import *

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
iphlpapi = ctypes.WinDLL("iphlpapi", use_last_error=True)
ws2_32 = ctypes.WinDLL("ws2_32", use_last_error=True)

# ── Structs ────────────────────────────────────────────────────────────────

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD),
                ("dwHighDateTime", wintypes.DWORD)]

class SYSTEMTIME(ctypes.Structure):
    _fields_ = [("wYear", wintypes.WORD), ("wMonth", wintypes.WORD),
                ("wDayOfWeek", wintypes.WORD), ("wDay", wintypes.WORD),
                ("wHour", wintypes.WORD), ("wMinute", wintypes.WORD),
                ("wSecond", wintypes.WORD), ("wMilliseconds", wintypes.WORD)]

class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ThreadID", wintypes.DWORD),
                ("th32OwnerProcessID", wintypes.DWORD),
                ("tpBasePri", wintypes.LONG),
                ("tpDeltaPri", wintypes.LONG),
                ("dwFlags", wintypes.DWORD)]

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.CHAR * MAX_PATH)]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD),
                ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD),
                ("modBaseAddr", ctypes.POINTER(wintypes.BYTE)),
                ("modBaseSize", wintypes.DWORD),
                ("hModule", wintypes.HMODULE),
                ("szModule", wintypes.CHAR * 256),
                ("szExePath", wintypes.CHAR * MAX_PATH)]

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD),
                ("Privileges", LUID_AND_ATTRIBUTES * 1)]

class SYSTEM_THREAD_INFORMATION(ctypes.Structure):
    _fields_ = [("KernelTime", wintypes.LARGE_INTEGER),
                ("UserTime", wintypes.LARGE_INTEGER),
                ("CreateTime", wintypes.LARGE_INTEGER),
                ("WaitTime", wintypes.DWORD),
                ("StartAddress", ctypes.POINTER(ctypes.c_void_p)),
                ("ClientId", ctypes.c_void_p * 2),
                ("Priority", wintypes.LONG),
                ("BasePriority", wintypes.LONG),
                ("ContextSwitches", wintypes.DWORD),
                ("ThreadState", wintypes.DWORD),
                ("WaitReason", wintypes.DWORD)]

class SYSTEM_PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("NextEntryOffset", wintypes.DWORD),
                ("NumberOfThreads", wintypes.DWORD),
                ("Reserved1", wintypes.BYTE * 48),
                ("ImageName", ctypes.c_wchar_p),
                ("BasePriority", wintypes.LONG),
                ("ProcessId", ctypes.c_void_p),
                ("Reserved2", ctypes.c_void_p),
                ("HandleCount", wintypes.DWORD),
                ("SessionId", wintypes.DWORD),
                ("Reserved3", ctypes.c_void_p * 4),
                ("PeakVirtualSize", ctypes.c_size_t),
                ("VirtualSize", ctypes.c_size_t),
                ("Reserved4", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("Reserved5", ctypes.c_void_p),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("Reserved6", ctypes.c_void_p),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivatePageCount", ctypes.c_size_t),
                ("Reserved7", wintypes.LARGE_INTEGER * 6)]

class THREAD_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("ExitStatus", wintypes.LONG),
                ("TebBaseAddress", ctypes.POINTER(ctypes.c_void_p)),
                ("ClientId", ctypes.c_void_p * 2),
                ("AffinityMask", ctypes.c_void_p),
                ("Priority", wintypes.LONG),
                ("BasePriority", wintypes.LONG)]

class CLIENT_ID(ctypes.Structure):
    _fields_ = [("UniqueProcess", ctypes.c_void_p),
                ("UniqueThread", ctypes.c_void_p)]

class KERNEL_USER_TIMES(ctypes.Structure):
    _fields_ = [("CreateTime", wintypes.LARGE_INTEGER),
                ("ExitTime", wintypes.LARGE_INTEGER),
                ("KernelTime", wintypes.LARGE_INTEGER),
                ("UserTime", wintypes.LARGE_INTEGER)]

class SYSTEM_HANDLE_TABLE_ENTRY_INFO(ctypes.Structure):
    _fields_ = [("UniqueProcessId", wintypes.USHORT),
                ("CreatorBackTraceIndex", wintypes.USHORT),
                ("ObjectTypeIndex", wintypes.BYTE),
                ("HandleAttributes", wintypes.BYTE),
                ("HandleValue", wintypes.USHORT),
                ("Object_", ctypes.POINTER(ctypes.c_void_p)),
                ("GrantedAccess", wintypes.DWORD)]

class SYSTEM_HANDLE_INFORMATION(ctypes.Structure):
    _fields_ = [("NumberOfHandles", wintypes.DWORD),
                ("Handles", SYSTEM_HANDLE_TABLE_ENTRY_INFO * 1)]

# TCP/UDP structs
class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwState", wintypes.DWORD),
                ("dwLocalAddr", wintypes.DWORD),
                ("dwLocalPort", wintypes.DWORD),
                ("dwRemoteAddr", wintypes.DWORD),
                ("dwRemotePort", wintypes.DWORD),
                ("dwOwningPid", wintypes.DWORD)]

class MIB_TCPTABLE_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwNumEntries", wintypes.DWORD),
                ("table", MIB_TCPROW_OWNER_PID * 1)]

class MIB_UDPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwLocalAddr", wintypes.DWORD),
                ("dwLocalPort", wintypes.DWORD),
                ("dwOwningPid", wintypes.DWORD)]

class MIB_UDPTABLE_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwNumEntries", wintypes.DWORD),
                ("table", MIB_UDPROW_OWNER_PID * 1)]

class MIB_TCP6ROW_OWNER_PID(ctypes.Structure):
    _fields_ = [("ucLocalAddr", wintypes.BYTE * 16),
                ("dwLocalScopeId", wintypes.DWORD),
                ("dwLocalPort", wintypes.DWORD),
                ("ucRemoteAddr", wintypes.BYTE * 16),
                ("dwRemoteScopeId", wintypes.DWORD),
                ("dwRemotePort", wintypes.DWORD),
                ("dwState", wintypes.DWORD),
                ("dwOwningPid", wintypes.DWORD)]

class MIB_TCP6TABLE_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwNumEntries", wintypes.DWORD),
                ("table", MIB_TCP6ROW_OWNER_PID * 1)]

class MIB_UDP6ROW_OWNER_PID(ctypes.Structure):
    _fields_ = [("ucLocalAddr", wintypes.BYTE * 16),
                ("dwLocalScopeId", wintypes.DWORD),
                ("dwLocalPort", wintypes.DWORD),
                ("dwOwningPid", wintypes.DWORD)]

class MIB_UDP6TABLE_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwNumEntries", wintypes.DWORD),
                ("table", MIB_UDP6ROW_OWNER_PID * 1)]


# ── Helpers ─────────────────────────────────────────────────────────────────

def _errcheck_zero(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return result

def _errcheck_nonzero(result, func, args):
    if result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result

def filetime_to_int64(ft):
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

def filetime_to_datetime(ft):
    import datetime
    if ft.dwLowDateTime == 0 and ft.dwHighDateTime == 0:
        return None
    # 100-nanosecond intervals since 1601-01-01
    ns100 = filetime_to_int64(ft)
    if ns100 == 0:
        return None
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=ns100 // 10)

def luid_to_int(luid):
    return (luid.HighPart << 32) | luid.LowPart


# ── kernel32 ────────────────────────────────────────────────────────────────

# CreateToolhelp32Snapshot
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.errcheck = lambda r, f, a: (
    ctypes.WinError(ctypes.get_last_error()) if r == INVALID_HANDLE_VALUE else r
)

# Process32First / Next
kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32First.restype = wintypes.BOOL

kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32Next.restype = wintypes.BOOL

# Thread32First / Next
kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32First.restype = wintypes.BOOL

kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32Next.restype = wintypes.BOOL

# Module32First / Next
kernel32.Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32First.restype = wintypes.BOOL

kernel32.Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32)]
kernel32.Module32Next.restype = wintypes.BOOL

# OpenProcess
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.errcheck = _errcheck_zero

# OpenThread
kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenThread.restype = wintypes.HANDLE
kernel32.OpenThread.errcheck = _errcheck_zero

# CloseHandle
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

# GetProcessTimes
kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(FILETIME),
                                       ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
                                       ctypes.POINTER(FILETIME)]
kernel32.GetProcessTimes.restype = wintypes.BOOL
kernel32.GetProcessTimes.errcheck = _errcheck_zero

# GetThreadTimes
kernel32.GetThreadTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(FILETIME),
                                      ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
                                      ctypes.POINTER(FILETIME)]
kernel32.GetThreadTimes.restype = wintypes.BOOL
kernel32.GetThreadTimes.errcheck = _errcheck_zero

# QueryFullProcessImageName
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                  wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.QueryFullProcessImageNameW.errcheck = _errcheck_zero

# GetProcessMemoryInfo (psapi)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]

psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,
                                         ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
                                         wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
psapi.GetProcessMemoryInfo.errcheck = _errcheck_zero

# GetSystemTimes
kernel32.GetSystemTimes.argtypes = [ctypes.POINTER(FILETIME),
                                      ctypes.POINTER(FILETIME),
                                      ctypes.POINTER(FILETIME)]
kernel32.GetSystemTimes.restype = wintypes.BOOL
kernel32.GetSystemTimes.errcheck = _errcheck_zero

# GlobalMemoryStatusEx
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64)]

kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
kernel32.GlobalMemoryStatusEx.errcheck = _errcheck_zero

# SetThreadPriority
kernel32.SetThreadPriority.argtypes = [wintypes.HANDLE, wintypes.INT]
kernel32.SetThreadPriority.restype = wintypes.BOOL
kernel32.SetThreadPriority.errcheck = _errcheck_zero

# GetThreadPriority
kernel32.GetThreadPriority.argtypes = [wintypes.HANDLE]
kernel32.GetThreadPriority.restype = wintypes.INT
# Returns THREAD_PRIORITY_ERROR_RETURN (MAXLONG) on error

# SetThreadAffinityMask
kernel32.SetThreadAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
kernel32.SetThreadAffinityMask.restype = ctypes.c_void_p  # previous mask

# SetProcessAffinityMask
kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
kernel32.SetProcessAffinityMask.restype = wintypes.BOOL
kernel32.SetProcessAffinityMask.errcheck = _errcheck_zero

# SuspendThread / ResumeThread
kernel32.SuspendThread.argtypes = [wintypes.HANDLE]
kernel32.SuspendThread.restype = wintypes.DWORD  # previous suspend count; -1 on error

kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
kernel32.ResumeThread.restype = wintypes.DWORD  # previous suspend count; -1 on error

# TerminateThread
kernel32.TerminateThread.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.TerminateThread.restype = wintypes.BOOL
kernel32.TerminateThread.errcheck = _errcheck_zero

# GetCurrentProcess / GetCurrentThread (no error checks needed)
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.GetCurrentThread.restype = wintypes.HANDLE


# ── ntdll ───────────────────────────────────────────────────────────────────

ntdll.NtQueryInformationThread.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                             ctypes.c_void_p, wintypes.DWORD,
                                             ctypes.POINTER(wintypes.DWORD)]
ntdll.NtQueryInformationThread.restype = wintypes.LONG

ntdll.NtQuerySystemInformation.argtypes = [wintypes.DWORD, ctypes.c_void_p,
                                             wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
ntdll.NtQuerySystemInformation.restype = wintypes.LONG

ntdll.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                              ctypes.c_void_p, wintypes.DWORD,
                                              ctypes.POINTER(wintypes.DWORD)]
ntdll.NtQueryInformationProcess.restype = wintypes.LONG

ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
ntdll.NtSuspendProcess.restype = wintypes.LONG

ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
ntdll.NtResumeProcess.restype = wintypes.LONG

# RtlAdjustPrivilege
ntdll.RtlAdjustPrivilege.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.BOOL,
                                       ctypes.POINTER(wintypes.BOOL)]
ntdll.RtlAdjustPrivilege.restype = wintypes.LONG

# NtSetInformationThread
ntdll.NtSetInformationThread.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                           ctypes.c_void_p, wintypes.DWORD]
ntdll.NtSetInformationThread.restype = wintypes.LONG


# ── advapi32 ────────────────────────────────────────────────────────────────

advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR,
                                             ctypes.POINTER(LUID)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
advapi32.LookupPrivilegeValueW.errcheck = _errcheck_zero

advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                        ctypes.POINTER(wintypes.HANDLE)]
advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.OpenProcessToken.errcheck = _errcheck_zero

advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL,
                                             ctypes.POINTER(TOKEN_PRIVILEGES),
                                             wintypes.DWORD, ctypes.POINTER(TOKEN_PRIVILEGES),
                                             ctypes.POINTER(wintypes.DWORD)]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
advapi32.AdjustTokenPrivileges.errcheck = _errcheck_zero


# ── iphlpapi ────────────────────────────────────────────────────────────────

iphlpapi.GetExtendedTcpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
                                           wintypes.BOOL, wintypes.DWORD, wintypes.DWORD,
                                           wintypes.DWORD]
iphlpapi.GetExtendedTcpTable.restype = wintypes.DWORD

iphlpapi.GetExtendedUdpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
                                           wintypes.BOOL, wintypes.DWORD, wintypes.DWORD,
                                           wintypes.DWORD]
iphlpapi.GetExtendedUdpTable.restype = wintypes.DWORD

TCP_TABLE_OWNER_PID_ALL = 5
UDP_TABLE_OWNER_PID = 1
TCP_TABLE_OWNER_PID_CONNECTIONS = 4
TCP_TABLE_OWNER_PID_LISTENER = 3

# ── ws2_32 ──────────────────────────────────────────────────────────────────

ws2_32.ntohs.argtypes = [wintypes.USHORT]
ws2_32.ntohs.restype = wintypes.USHORT

ws2_32.inet_ntoa.argtypes = [wintypes.DWORD]
ws2_32.inet_ntoa.restype = ctypes.c_char_p


# ── Privilege helper ────────────────────────────────────────────────────────

def enable_debug_privilege():
    """Enable SeDebugPrivilege. Returns True if successful."""
    se_debug = LUID()
    try:
        advapi32.LookupPrivilegeValueW(None, "SeDebugPrivilege", ctypes.byref(se_debug))
    except OSError:
        return False

    h_token = wintypes.HANDLE()
    try:
        advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),
                                   TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                                   ctypes.byref(h_token))
    except OSError:
        return False

    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = se_debug
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

    try:
        advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), 0, None, None)
    except OSError:
        kernel32.CloseHandle(h_token)
        return False

    kernel32.CloseHandle(h_token)
    return ctypes.get_last_error() == 0


# ── Process info helpers ────────────────────────────────────────────────────

def get_process_image_name(h_process):
    """Get full image path for a process handle."""
    buf = (wintypes.WCHAR * MAX_PATH)()
    buf_len = wintypes.DWORD(MAX_PATH)
    try:
        kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_len))
        return buf.value
    except OSError:
        return ""

def get_process_memory_info(h_process):
    """Get PROCESS_MEMORY_COUNTERS_EX for a process handle."""
    pmc = PROCESS_MEMORY_COUNTERS_EX()
    pmc.cb = ctypes.sizeof(pmc)
    psapi.GetProcessMemoryInfo(h_process, ctypes.byref(pmc), pmc.cb)
    return pmc

def get_process_times(h_process):
    """Get creation, exit, kernel, user times for a process handle. Returns tuple of datetimes."""
    create_ft = FILETIME()
    exit_ft = FILETIME()
    kernel_ft = FILETIME()
    user_ft = FILETIME()
    kernel32.GetProcessTimes(h_process, ctypes.byref(create_ft),
                             ctypes.byref(exit_ft), ctypes.byref(kernel_ft),
                             ctypes.byref(user_ft))
    return (filetime_to_datetime(create_ft),
            filetime_to_datetime(exit_ft),
            filetime_to_datetime(kernel_ft),
            filetime_to_datetime(user_ft))

def get_thread_times(h_thread):
    """Get creation, exit, kernel, user times for a thread handle. Returns tuple of datetimes."""
    create_ft = FILETIME()
    exit_ft = FILETIME()
    kernel_ft = FILETIME()
    user_ft = FILETIME()
    kernel32.GetThreadTimes(h_thread, ctypes.byref(create_ft),
                            ctypes.byref(exit_ft), ctypes.byref(kernel_ft),
                            ctypes.byref(user_ft))
    return (filetime_to_datetime(create_ft),
            filetime_to_datetime(exit_ft),
            filetime_to_datetime(kernel_ft),
            filetime_to_datetime(user_ft))


# ── Thread info helpers ─────────────────────────────────────────────────────

def query_thread_basic_info(h_thread):
    """Get THREAD_BASIC_INFORMATION for a thread handle."""
    info = THREAD_BASIC_INFORMATION()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, ThreadBasicInformation,
                                             ctypes.byref(info), ctypes.sizeof(info),
                                             ctypes.byref(ret_len))
    if status != 0:
        raise ctypes.WinError(0, f"NtQueryInformationThread(ThreadBasicInformation) failed: 0x{status:08X}")
    return info

def query_thread_times_info(h_thread):
    """Get KERNEL_USER_TIMES for a thread handle."""
    info = KERNEL_USER_TIMES()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, 1,  # ThreadTimes = 1
                                             ctypes.byref(info), ctypes.sizeof(info),
                                             ctypes.byref(ret_len))
    if status != 0:
        raise ctypes.WinError(0, f"NtQueryInformationThread(ThreadTimes) failed: 0x{status:08X}")
    return info

def query_thread_start_address(h_thread):
    """Get the start address of a thread."""
    addr = ctypes.c_void_p()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, ThreadQuerySetWin32StartAddress,
                                             ctypes.byref(addr), ctypes.sizeof(addr),
                                             ctypes.byref(ret_len))
    if status != 0:
        return None
    return addr.value or None

def query_thread_io_priority(h_thread):
    """Get the IO priority of a thread."""
    prio = wintypes.DWORD()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, ThreadIoPriority,
                                             ctypes.byref(prio), ctypes.sizeof(prio),
                                             ctypes.byref(ret_len))
    if status != 0:
        return None
    return prio.value

def query_thread_page_priority(h_thread):
    """Get the page priority of a thread."""
    prio = wintypes.DWORD()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, ThreadPagePriority,
                                             ctypes.byref(prio), ctypes.sizeof(prio),
                                             ctypes.byref(ret_len))
    if status != 0:
        return None
    return prio.value

def query_thread_cycle_time(h_thread):
    """Get the cycle time of a thread (in processor cycles)."""
    cycle_time = wintypes.ULONGLONG()
    ret_len = wintypes.DWORD()
    status = ntdll.NtQueryInformationThread(h_thread, ThreadCycleTime,
                                             ctypes.byref(cycle_time), ctypes.sizeof(cycle_time),
                                             ctypes.byref(ret_len))
    if status != 0:
        return None
    return cycle_time.value

def set_thread_io_priority(h_thread, io_priority):
    """Set the IO priority of a thread."""
    prio = wintypes.DWORD(io_priority)
    status = ntdll.NtSetInformationThread(h_thread, ThreadIoPriority,
                                           ctypes.byref(prio), ctypes.sizeof(prio))
    if status != 0:
        raise ctypes.WinError(0, f"NtSetInformationThread(ThreadIoPriority) failed: 0x{status:08X}")

def set_thread_page_priority(h_thread, page_priority):
    """Set the page priority of a thread."""
    prio = wintypes.DWORD(page_priority)
    status = ntdll.NtSetInformationThread(h_thread, ThreadPagePriority,
                                           ctypes.byref(prio), ctypes.sizeof(prio))
    if status != 0:
        raise ctypes.WinError(0, f"NtSetInformationThread(ThreadPagePriority) failed: 0x{status:08X}")


# ── Network helpers ─────────────────────────────────────────────────────────

def ip4_to_str(addr):
    """Convert a DWORD IPv4 address to string."""
    return ws2_32.inet_ntoa(addr).decode() if addr else "0.0.0.0"

def ip6_to_str(addr_bytes):
    """Convert 16-byte IPv6 address to string."""
    import socket
    try:
        return socket.inet_ntop(socket.AF_INET6, bytes(addr_bytes))
    except Exception:
        return "::"

def get_tcp_table():
    """Get extended TCP table (IPv4). Returns list of dicts."""
    buf_size = wintypes.DWORD(0)
    iphlpapi.GetExtendedTcpTable(None, ctypes.byref(buf_size), False,
                                 AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)

    buf = ctypes.create_string_buffer(buf_size.value)
    ret = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(buf_size), False,
                                       AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
    if ret != 0:
        return []

    table = ctypes.cast(buf, ctypes.POINTER(MIB_TCPTABLE_OWNER_PID)).contents
    rows = []
    for i in range(table.dwNumEntries):
        row = table.table[i]
        rows.append({
            "local_addr": ip4_to_str(row.dwLocalAddr),
            "local_port": ws2_32.ntohs(wintypes.USHORT(row.dwLocalPort)),
            "remote_addr": ip4_to_str(row.dwRemoteAddr),
            "remote_port": ws2_32.ntohs(wintypes.USHORT(row.dwRemotePort)),
            "state": row.dwState,
            "state_name": TCP_STATE_NAMES.get(row.dwState, f"Unknown({row.dwState})"),
            "pid": row.dwOwningPid,
            "family": "IPv4",
            "protocol": "TCP",
        })
    return rows

def get_tcp6_table():
    """Get extended TCP table (IPv6). Returns list of dicts."""
    buf_size = wintypes.DWORD(0)
    iphlpapi.GetExtendedTcpTable(None, ctypes.byref(buf_size), False,
                                 AF_INET6, TCP_TABLE_OWNER_PID_ALL, 0)

    buf = ctypes.create_string_buffer(buf_size.value)
    ret = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(buf_size), False,
                                       AF_INET6, TCP_TABLE_OWNER_PID_ALL, 0)
    if ret != 0:
        return []

    table = ctypes.cast(buf, ctypes.POINTER(MIB_TCP6TABLE_OWNER_PID)).contents
    rows = []
    for i in range(table.dwNumEntries):
        row = table.table[i]
        rows.append({
            "local_addr": ip6_to_str(row.ucLocalAddr),
            "local_port": ws2_32.ntohs(wintypes.USHORT(row.dwLocalPort)),
            "remote_addr": ip6_to_str(row.ucRemoteAddr),
            "remote_port": ws2_32.ntohs(wintypes.USHORT(row.dwRemotePort)),
            "state": row.dwState,
            "state_name": TCP_STATE_NAMES.get(row.dwState, f"Unknown({row.dwState})"),
            "pid": row.dwOwningPid,
            "family": "IPv6",
            "protocol": "TCP",
        })
    return rows

def get_udp_table():
    """Get extended UDP table (IPv4). Returns list of dicts."""
    buf_size = wintypes.DWORD(0)
    iphlpapi.GetExtendedUdpTable(None, ctypes.byref(buf_size), False,
                                 AF_INET, UDP_TABLE_OWNER_PID, 0)

    buf = ctypes.create_string_buffer(buf_size.value)
    ret = iphlpapi.GetExtendedUdpTable(buf, ctypes.byref(buf_size), False,
                                       AF_INET, UDP_TABLE_OWNER_PID, 0)
    if ret != 0:
        return []

    table = ctypes.cast(buf, ctypes.POINTER(MIB_UDPTABLE_OWNER_PID)).contents
    rows = []
    for i in range(table.dwNumEntries):
        entry = table.table[i]
        rows.append({
            "local_addr": ip4_to_str(entry.dwLocalAddr),
            "local_port": ws2_32.ntohs(wintypes.USHORT(entry.dwLocalPort)),
            "remote_addr": "*",
            "remote_port": 0,
            "state": 0,
            "state_name": "",
            "pid": entry.dwOwningPid,
            "family": "IPv4",
            "protocol": "UDP",
        })
    return rows

def get_udp6_table():
    """Get extended UDP table (IPv6). Returns list of dicts."""
    buf_size = wintypes.DWORD(0)
    iphlpapi.GetExtendedUdpTable(None, ctypes.byref(buf_size), False,
                                 AF_INET6, UDP_TABLE_OWNER_PID, 0)

    buf = ctypes.create_string_buffer(buf_size.value)
    ret = iphlpapi.GetExtendedUdpTable(buf, ctypes.byref(buf_size), False,
                                       AF_INET6, UDP_TABLE_OWNER_PID, 0)
    if ret != 0:
        return []

    table = ctypes.cast(buf, ctypes.POINTER(MIB_UDP6TABLE_OWNER_PID)).contents
    rows = []
    for i in range(table.dwNumEntries):
        entry = table.table[i]
        rows.append({
            "local_addr": ip6_to_str(entry.ucLocalAddr),
            "local_port": ws2_32.ntohs(wintypes.USHORT(entry.dwLocalPort)),
            "remote_addr": "*",
            "remote_port": 0,
            "state": 0,
            "state_name": "",
            "pid": entry.dwOwningPid,
            "family": "IPv6",
            "protocol": "UDP",
        })
    return rows

def get_all_network_connections():
    """Get all TCP/UDP connections for all processes."""
    connections = []
    try:
        connections.extend(get_tcp_table())
    except Exception:
        pass
    try:
        connections.extend(get_tcp6_table())
    except Exception:
        pass
    try:
        connections.extend(get_udp_table())
    except Exception:
        pass
    try:
        connections.extend(get_udp6_table())
    except Exception:
        pass
    return connections
