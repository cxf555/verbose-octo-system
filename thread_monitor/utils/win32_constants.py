# Windows API constants

# Process access rights
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_SET_INFORMATION = 0x0200
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_TERMINATE = 0x0001

# Thread access rights
THREAD_QUERY_INFORMATION = 0x0040
THREAD_QUERY_LIMITED_INFORMATION = 0x0800
THREAD_SET_INFORMATION = 0x0020
THREAD_SUSPEND_RESUME = 0x0002
THREAD_TERMINATE = 0x0001
THREAD_SET_LIMITED_INFORMATION = 0x0400

# Toolhelp snapshot flags
TH32CS_SNAPHEAPLIST = 0x00000001
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
TH32CS_SNAPALL = (TH32CS_SNAPHEAPLIST | TH32CS_SNAPPROCESS |
                  TH32CS_SNAPTHREAD | TH32CS_SNAPMODULE)
TH32CS_INHERIT = 0x80000000

# Thread states (from Thread32First/Next dwThreadState)
THREAD_STATE_INITIALIZED = 0
THREAD_STATE_READY = 1
THREAD_STATE_RUNNING = 2
THREAD_STATE_STANDBY = 3
THREAD_STATE_TERMINATED = 4
THREAD_STATE_WAIT = 5
THREAD_STATE_TRANSITION = 6
THREAD_STATE_UNKNOWN = 7

THREAD_STATE_NAMES = {
    0: "Initialized",
    1: "Ready",
    2: "Running",
    3: "Standby",
    4: "Terminated",
    5: "Wait",
    6: "Transition",
    7: "Unknown",
}

# Thread wait reasons
WAIT_REASON_EXECUTIVE = 0
WAIT_REASON_FREE_PAGE = 1
WAIT_REASON_PAGE_IN = 2
WAIT_REASON_POOL_ALLOCATION = 3
WAIT_REASON_DELAY_EXECUTION = 4
WAIT_REASON_SUSPENDED = 5
WAIT_REASON_USER_REQUEST = 6
WAIT_REASON_WR_EXECUTIVE = 7
WAIT_REASON_WR_FREE_PAGE = 8
WAIT_REASON_WR_PAGE_IN = 9
WAIT_REASON_WR_POOL_ALLOCATION = 10
WAIT_REASON_WR_DELAY_EXECUTION = 11
WAIT_REASON_WR_USER_REQUEST = 12
WAIT_REASON_WR_EVENT_PAIR = 13
WAIT_REASON_WR_QUEUE = 14
WAIT_REASON_WR_LPC_RECEIVE = 15
WAIT_REASON_WR_LPC_REPLY = 16
WAIT_REASON_WR_VIRTUAL_MEMORY = 17
WAIT_REASON_WR_PAGE_OUT = 18
WAIT_REASON_WR_RENDEZVOUS = 19
WAIT_REASON_WR_KEYED_EVENT = 20
WAIT_REASON_WR_TERMINATED = 21
WAIT_REASON_WR_PROCESS_IN_SWAP = 22
WAIT_REASON_WR_CPU_RATE_CONTROL = 23
WAIT_REASON_WR_CALLOUT_STACK = 24
WAIT_REASON_WR_KERNEL = 25
WAIT_REASON_WR_RESOURCE = 26
WAIT_REASON_WR_PUSH_LOCK = 27
WAIT_REASON_WR_MUTEX = 28
WAIT_REASON_WR_QUANTUM_END = 29
WAIT_REASON_WR_DISPATCH_INT = 30
WAIT_REASON_WR_PREEMPTED = 31
WAIT_REASON_WR_YIELD_EXECUTION = 32
WAIT_REASON_WR_FAST_MUTEX = 33
WAIT_REASON_WR_GUARDED_MUTEX = 34
WAIT_REASON_WR_RUNDOWN = 35
WAIT_REASON_MAXIMUM = 36

WAIT_REASON_NAMES = {
    0: "Executive",
    1: "FreePage",
    2: "PageIn",
    3: "PoolAllocation",
    4: "DelayExecution",
    5: "Suspended",
    6: "UserRequest",
    7: "WrExecutive",
    8: "WrFreePage",
    9: "WrPageIn",
    10: "WrPoolAllocation",
    11: "WrDelayExecution",
    12: "WrUserRequest",
    13: "WrEventPair",
    14: "WrQueue",
    15: "WrLpcReceive",
    16: "WrLpcReply",
    17: "WrVirtualMemory",
    18: "WrPageOut",
    19: "WrRendezvous",
    20: "WrKeyedEvent",
    21: "WrTerminated",
    22: "WrProcessInSwap",
    23: "WrCpuRateControl",
    24: "WrCalloutStack",
    25: "WrKernel",
    26: "WrResource",
    27: "WrPushLock",
    28: "WrMutex",
    29: "WrQuantumEnd",
    30: "WrDispatchInt",
    31: "WrPreempted",
    32: "WrYieldExecution",
    33: "WrFastMutex",
    34: "WrGuardedMutex",
    35: "WrRundown",
    36: "Maximum",
}

# THREADINFOCLASS for NtQueryInformationThread
ThreadBasicInformation = 0
ThreadTimes = 1
ThreadPriority = 2
ThreadBasePriority = 3
ThreadAffinityMask = 4
ThreadImpersonationToken = 5
ThreadDescriptorTableEntry = 6
ThreadEnableAlignmentFaultFixup = 7
ThreadEventPair = 8
ThreadQuerySetWin32StartAddress = 9
ThreadZeroTlsCell = 10
ThreadPerformanceCount = 11
ThreadAmILastThread = 12
ThreadIdealProcessor = 13
ThreadPriorityBoost = 14
ThreadSetTlsArrayAddress = 15
ThreadIsIoPending = 16
ThreadHideFromDebugger = 17
ThreadBreakOnTermination = 18
ThreadSwitchLegacyState = 19
ThreadIsTerminated = 20
ThreadLastSystemCall = 21
ThreadIoPriority = 22
ThreadCycleTime = 23
ThreadPagePriority = 24
ThreadActualBasePriority = 25
ThreadTebInformation = 26
ThreadCSwitchMon = 27
ThreadCSwitchPmu = 28
ThreadWow64Context = 29
ThreadGroupInformation = 30
ThreadUmsInformation = 31
ThreadCounterProfiling = 32
ThreadIdealProcessorEx = 33
ThreadCpuAccountingInformation = 34
ThreadSuspendCount = 35
ThreadActualGroupAffinity = 36
ThreadDynamicCodePolicyInfo = 37
ThreadSubsystemInformationType = 38

# SYSTEMINFOCLASS for NtQuerySystemInformation
SystemBasicInformation = 0
SystemPerformanceInformation = 2
SystemTimeOfDayInformation = 3
SystemProcessInformation = 5
SystemHandleInformation = 16
SystemProcessorPerformanceInformation = 8

# Token privileges
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

# MIB_TCPROW_STATE for TCP connections
MIB_TCP_STATE_CLOSED = 1
MIB_TCP_STATE_LISTEN = 2
MIB_TCP_STATE_SYN_SENT = 3
MIB_TCP_STATE_SYN_RCVD = 4
MIB_TCP_STATE_ESTAB = 5
MIB_TCP_STATE_FIN_WAIT1 = 6
MIB_TCP_STATE_FIN_WAIT2 = 7
MIB_TCP_STATE_CLOSE_WAIT = 8
MIB_TCP_STATE_CLOSING = 9
MIB_TCP_STATE_LAST_ACK = 10
MIB_TCP_STATE_TIME_WAIT = 11
MIB_TCP_STATE_DELETE_TCB = 12

TCP_STATE_NAMES = {
    1: "CLOSED",
    2: "LISTEN",
    3: "SYN_SENT",
    4: "SYN_RCVD",
    5: "ESTABLISHED",
    6: "FIN_WAIT1",
    7: "FIN_WAIT2",
    8: "CLOSE_WAIT",
    9: "CLOSING",
    10: "LAST_ACK",
    11: "TIME_WAIT",
    12: "DELETE_TCB",
}

# AF_INET / AF_INET6
AF_INET = 2
AF_INET6 = 23

# Thread priority classes (base priority)
THREAD_PRIORITY_IDLE = -15
THREAD_PRIORITY_LOWEST = -2
THREAD_PRIORITY_BELOW_NORMAL = -1
THREAD_PRIORITY_NORMAL = 0
THREAD_PRIORITY_ABOVE_NORMAL = 1
THREAD_PRIORITY_HIGHEST = 2
THREAD_PRIORITY_TIME_CRITICAL = 15

THREAD_PRIORITY_NAMES = {
    -15: "Idle",
    -2: "Lowest",
    -1: "Below Normal",
    0: "Normal",
    1: "Above Normal",
    2: "Highest",
    15: "Time Critical",
}

# IO Priority
IO_PRIORITY_VERY_LOW = 0
IO_PRIORITY_LOW = 1
IO_PRIORITY_NORMAL = 2
IO_PRIORITY_HIGH = 3
IO_PRIORITY_CRITICAL = 4

IO_PRIORITY_NAMES = {
    0: "Very Low",
    1: "Low",
    2: "Normal",
    3: "High",
    4: "Critical",
}

# Page Priority
PAGE_PRIORITY_IDLE = 1
PAGE_PRIORITY_NORMAL = 5
PAGE_PRIORITY_HIGH = 6

PAGE_PRIORITY_NAMES = {
    1: "Idle (1)",
    2: "2",
    3: "3",
    4: "4",
    5: "Normal (5)",
    6: "High (6)",
    7: "7",
}

# Handle types
OBJ_TYPE_FILE = 0
OBJ_TYPE_EVENT = 1
OBJ_TYPE_SECTION = 2
OBJ_TYPE_SEMAPHORE = 3
OBJ_TYPE_MUTANT = 4
OBJ_TYPE_THREAD = 5
OBJ_TYPE_PROCESS = 6
OBJ_TYPE_KEY = 7
OBJ_TYPE_TOKEN = 8
OBJ_TYPE_DIRECTORY = 9
OBJ_TYPE_SYMBOLIC_LINK = 10
OBJ_TYPE_JOBOBJECT = 11
OBJ_TYPE_TIMER = 12
OBJ_TYPE_KEYED_EVENT = 13
OBJ_TYPE_WINDOW_STATION = 14
OBJ_TYPE_DESKTOP = 15
OBJ_TYPE_TMWORKERFACTORY = 16
OBJ_TYPE_IOCOMPLETION = 17
OBJ_TYPE_IRPTIMER = 18
OBJ_TYPE_WAITCOMPLETIONPACKET = 19
OBJ_TYPE_ALPC_PORT = 20
OBJ_TYPE_ETWREGOBJECT = 22
OBJ_TYPE_WMI_GUID = 23

# Error codes
ERROR_NO_MORE_FILES = 18
ERROR_ACCESS_DENIED = 5
ERROR_NOT_ALL_SUPPORTED = 50

# INVALID_HANDLE_VALUE (Python 3.13+ wintypes 中已移除, 需自行定义)
# HANDLE 是 void* 类型, INVALID_HANDLE_VALUE = (HANDLE)(LONG_PTR)-1
INVALID_HANDLE_VALUE = -1

# MAX_PATH
MAX_PATH = 260

# Image file machine types
IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_FILE_MACHINE_ARM64 = 0xAA64
