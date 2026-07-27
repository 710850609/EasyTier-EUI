# EasyTier 适配器架构设计（修订版）

## 概述

引入 **门面模式（Facade）** + **适配器模式（Adapter）**，屏蔽不同 EasyTier 版本实现的调用差异：

1. **版本隔离**：FFI v2.4.5、FFI main 分支、CLI 子进程三套实现统一接口
2. **升级安全**：未来 FFI 符号变更时，只需新增适配器，不影响现有代码
3. **自动降级**：按优先级自动选择可用适配器，任何一个可用即可正常运行
4. **独立包**：`et_adapters` 是 `backend/` 下的独立一级包，与 `utils/` 平级，职责清晰

## 包结构

```
backend/
├── et_adapters/                          # 独立包（与 utils/ 平级）
│   ├── __init__.py                       # 导出 EasyTierFacade, get_facade()
│   ├── interface.py                      # IEasyTierAdapter 抽象接口
│   ├── facade.py                         # EasyTierFacade 门面
│   ├── ffi_base.py                       # BaseFfiAdapter（FFI 共享逻辑）
│   ├── ffi_adapter.py                    # FfiAdapter（当前默认，v2.4.5/v2.6.4 FFI，7 符号）
│   ├── ffi_main.py                       # FfiMainAdapter（预留，main 分支未来新接口）
│   └── core_cli.py                       # CoreCliAdapter（CLI 子进程）
│
└── utils/
    └── check_peers.py                    # 兼容层（保留工具函数，节点检测委托给适配器）
```

> **设计原则**：`et_adapters` 是独立包，不依赖 `utils`。业务层直接导入 `et_adapters`，`EasyTierFacade` 即对外 API。`utils/check_peers.py` 反向依赖 `et_adapters`，作为节点检测兼容层存在。

## 架构图

```
┌──────────────────────────────────────────────────────────────┐
│  业务层                                                      │
│  services.py  /  monitor.py  /  et_core.py  /  peers.py     │
│                                                              │
│  from et_adapters import get_facade                          │
│  et_bridge = get_facade()                                    │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              EasyTierFacade（门面）                           │
│              backend/et_adapters/facade.py                   │
│                                                              │
│  职责：                                                       │
│  - 自动检测并选择可用适配器                                    │
│  - 管理 current_instance_name 缓存                            │
│  - 所有方法委托给当前适配器                                    │
│                                                              │
│  ADAPTERS = [FfiMainAdapter, FfiAdapter, CoreCliAdapter]  │
└──────────────────────────┬───────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐  ┌─────────▼────────┐  ┌──────▼──────────┐
│FfiMainAdapter│  │   FfiAdapter     │  │CoreCliAdapter   │
│              │  │                  │  │                 │
│ 预留，未来     │  │ 当前默认          │  │ CLI 子进程       │
│ main 分支新    │  │ v2.4.5/v2.6.4    │  │ subprocess       │
│ 接口开发       │  │ FFI，7 符号       │  │                 │
│              │  │                  │  │ 兜底方案         │
│ FFI 采集      │  │ FFI 采集          │  │ CLI 采集         │
│              │  │ collect_network  │  │ easytier-cli     │
│              │  │ _infos           │  │ peer --json      │
└──────┬───────┘  └────────┬────────┘  └──────┬──────────┘
       │                   │                   │
       └────────┬──────────┘                   │
                │                              │
    ┌───────────▼───────────┐                  │
    │   BaseFfiAdapter      │                  │
    │                       │                  │
    │  共享逻辑：            │                  │
    │  - 加载 .so           │                  │
    │  - 符号检测            │                  │
    │  - 通用 FFI 调用       │                  │
    │  - 数据格式化           │                  │
    │  - 线程锁管理           │                  │
    └───────────┬───────────┘                  │
                │                              │
                ▼                              ▼
        libeasytier_ffi.so          easytier-core / easytier-cli
```

## 抽象接口 `IEasyTierAdapter`

只有 4 个核心方法，所有适配器必须实现：

```python
class IEasyTierAdapter(ABC):
    """EasyTier 统一适配接口"""

    @abstractmethod
    def start_network(self, toml_config: str, instance_name: str) -> int:
        """启动网络实例，返回 0 成功 / -1 失败"""
        ...

    @abstractmethod
    def stop_network(self, instance_name: str = None) -> int:
        """
        停止网络实例。
        instance_name=None 时停止所有实例，返回 0 成功 / -1 失败
        """
        ...

    @abstractmethod
    def get_network_infos(self, max_length: int = 10) -> Dict[str, Any]:
        """
        获取网络信息，返回格式：
        {
            "实例名": {
                "dev_name": "easytier0",
                "my_node_info": {...},
                "routes": [...],
                "peers": [...],
                "peer_route_pairs": [...],
                "running": True,
                "error_msg": None,
                "foreign_network_summary": [...],
            }
        }
        """
        ...

    @abstractmethod
    def get_version(self) -> str:
        """获取 EasyTier 版本号"""
        ...
```

## BaseFfiAdapter — FFI 共享逻辑

```python
class BaseFfiAdapter(IEasyTierAdapter):
    """
    FFI 适配器基类，封装两个 FFI 版本共用的逻辑。

    子类必须定义：
    - REQUIRED_SYMBOLS: List[str]   — 必须存在的符号名
    - MISSING_SYMBOLS: List[str]    — 预期缺失的符号名（用于区分版本）
    """

    def __init__(self):
        self._lib = None
        self._lock = threading.RLock()
        self._load_library()

    # ── 库加载 ──
    def _load_library(self):
        """多路径查找并加载 libeasytier_ffi.so"""
        so_paths = [
            Path(__file__).parent.parent / "libeasytier_ffi.so",
            "./libeasytier_ffi.so",
            "/data/local/tmp/libeasytier_ffi.so",
        ]
        for path in so_paths:
            try:
                self._lib = ctypes.CDLL(str(path))
                self._setup_functions()
                break
            except OSError:
                continue

    def _has_symbol(self, name: str) -> bool:
        """检测 .so 中是否存在指定符号"""
        try:
            getattr(self._lib, name)
            return True
        except AttributeError:
            return False

    # ── 可用性检测 ──
    def is_available(self) -> bool:
        """检测当前适配器是否可用（仅供 Facade 内部使用，非接口方法）"""
        if self._lib is None:
            return False
        return (all(self._has_symbol(s) for s in self.REQUIRED_SYMBOLS) and
                all(not self._has_symbol(s) for s in self.MISSING_SYMBOLS))

    # ── FFI 函数签名绑定 ──
    def _setup_functions(self):
        lib = self._lib
        lib.parse_config.argtypes = [c_char_p]
        lib.parse_config.restype = c_int

        lib.run_network_instance.argtypes = [c_char_p]
        lib.run_network_instance.restype = c_int

        lib.retain_network_instance.argtypes = [POINTER(c_char_p), c_size_t]
        lib.retain_network_instance.restype = c_int

        lib.collect_network_infos.argtypes = [POINTER(KeyValuePair), c_size_t]
        lib.collect_network_infos.restype = c_int

        lib.set_tun_fd.argtypes = [c_char_p, c_int]
        lib.set_tun_fd.restype = c_int

        lib.get_error_msg.argtypes = [POINTER(c_char_p)]
        lib.get_error_msg.restype = None

        lib.free_string.argtypes = [c_char_p]
        lib.free_string.restype = None

    # ── 通用实现 ──
    def start_network(self, toml, name):
        """解析配置 → 启动实例"""
        with self._lock:
            if self._lib.parse_config(toml.encode('utf-8')) != 0:
                return -1
            return self._lib.run_network_instance(toml.encode('utf-8'))

    def stop_network(self, name=None):
        """
        stop_network 通用实现：
        - name=None → 停止所有实例（retain_network_instance(None, 0)）
        - name 指定 → 保留除该实例外的所有实例，间接停止指定实例
        """
        if name is None:
            return self._retain_instances([])
        all_instances = self._list_all_instance_names()
        keep = [n for n in all_instances if n != name]
        return self._retain_instances(keep)

    def _retain_instances(self, names: List[str]) -> int:
        with self._lock:
            if not names:
                return self._lib.retain_network_instance(None, 0)
            encoded = [n.encode('utf-8') for n in names]
            arr = (c_char_p * len(names))(*encoded)
            return self._lib.retain_network_instance(arr, len(names))

    def _list_all_instance_names(self) -> List[str]:
        """从 collect_network_infos 获取所有实例名"""
        info = self._collect_via_raw_ffi(20)
        return list(info.keys())

    def get_last_error(self) -> str:
        with self._lock:
            out = c_char_p()
            self._lib.get_error_msg(ctypes.byref(out))
            if out.value is None:
                return ""
            result = out.value.decode('utf-8')
            self._lib.free_string(out)
            return result

    def set_tun_fd(self, name, fd):
        with self._lock:
            return self._lib.set_tun_fd(name.encode('utf-8'), fd)

    # ── 原始 FFI 采集（共用） ──
    def _collect_via_raw_ffi(self, max_len):
        with self._lock:
            infos = (KeyValuePair * max_len)()
            count = self._lib.collect_network_infos(infos, max_len)
            if count < 0:
                return {}
        result = {}
        for i in range(min(count, max_len)):
            key = infos[i].key.decode('utf-8') if infos[i].key else ""
            value = infos[i].value.decode('utf-8') if infos[i].value else ""
            result[key] = json.loads(value) if value else {}
            self._lib.free_string(infos[i].key)
            self._lib.free_string(infos[i].value)
        return result

    # ── 版本号：从二进制文件提取（正则搜版本字符串） ──
    def get_version(self) -> str:
        """
        从 .so 二进制中正则提取版本号。
        版本号格式：X.Y.Z-xxxxxxxx（commit hash）
        如：2.6.4-8428a89d
        """
        try:
            with open(self._lib._name, 'rb') as f:
                data = f.read()
            match = re.search(rb'(\d+\.\d+\.\d+-[a-f0-9]{8})', data)
            return match.group(1).decode() if match else "unknown"
        except Exception:
            return "unknown"

    # ── 数据格式化（共用） ──
    @staticmethod
    def _format_bytes(b): ...
    def _cost_to_string(self, cost): ...
    def _nat_type_to_string(self, nat_type): ...
    def _ipv4_addr_to_string(self, addr_obj): ...
    def _ipv4_inet_to_string(self, inet_obj): ...
    def _list_peer_route_pair(self, peers, routes): ...
```

## FfiMainAdapter — 预留，未来 main 分支新接口开发

> **当前状态**：FfiMainAdapter 与 FfiAdapter 符号完全一致（7 符号），故降级链中两个适配器会同时可用，FfiMainAdapter 因其优先级更高被选中。当前 FfiMainAdapter 行为与 FfiAdapter 完全相同，预留的目的是未来 main 分支 FFI 新增符号（如 `delete_network_instance`、`list_instance`、`call_json_rpc`）时，只需修改 `REQUIRED_SYMBOLS` 即可自动区分。

```python
class FfiMainAdapter(BaseFfiAdapter):
    """预留，未来 main 分支新接口开发"""

    REQUIRED_SYMBOLS = [
        'parse_config', 'run_network_instance', 'retain_network_instance',
        'collect_network_infos',
        'set_tun_fd',
        'get_error_msg', 'free_string',
    ]
    MISSING_SYMBOLS = []

    def get_network_infos(self, max_len=10):
        """通过 collect_network_infos FFI 采集"""
        return self._collect_via_raw_ffi(max_len)

    def get_version(self) -> str:
        return super().get_version()
```

## FfiAdapter — 当前默认 FFI 适配器

```python
class FfiAdapter(BaseFfiAdapter):
    """
    EasyTier FFI 适配器，当前默认实现。
    适配 v2.4.5 / v2.6.4 两个版本（两者导出符号完全一致，均为 7 符号）。
    """

    REQUIRED_SYMBOLS = [
        'parse_config', 'run_network_instance', 'retain_network_instance',
        'collect_network_infos',
        'set_tun_fd',
        'get_error_msg', 'free_string',
    ]
    MISSING_SYMBOLS = []

    def get_network_infos(self, max_len=10):
        """通过 collect_network_infos FFI 采集"""
        return self._collect_via_raw_ffi(max_len)

    def get_version(self) -> str:
        """从 .so 二进制正则提取版本号"""
        return super().get_version()
```

## CoreCliAdapter — CLI 子进程（兜底方案）

```python
class CoreCliAdapter(IEasyTierAdapter):
    """
    通过 easytier-core / easytier-cli 子进程实现。
    适用于未集成 FFI 的桌面环境，或作为 FFI 不可用时的兜底方案。

    这是唯一完整实现节点检测的适配器，因为只有它拥有 easytier-core 和 easytier-cli 二进制。
    """

    def __init__(self):
        self._core_path = None
        self._cli_path = None
        self._process = None
        self._find_binaries()

    def _find_binaries(self):
        self._core_path = self._find_binary('easytier-core')
        self._cli_path = self._find_binary('easytier-cli')

    def _find_binary(self, name):
        """查找单个二进制文件，支持多路径搜索"""
        ...

    def is_available(self):
        """仅供 Facade 内部使用，非接口方法"""
        return self._core_path is not None and self._cli_path is not None

    def get_version(self) -> str:
        """执行 easytier-core --version 获取版本"""
        try:
            output = subprocess.check_output(
                [self._core_path, '--version'], stderr=subprocess.STDOUT, timeout=5
            )
            return output.decode().strip()
        except Exception:
            return "unknown"

    def start_network(self, toml, name):
        """写入临时配置文件，启动 easytier-core 子进程"""
        config_path = Path(tempfile.gettempdir()) / f"easytier_{name}.toml"
        config_path.write_text(toml)
        self._process = subprocess.Popen(
            [self._core_path, '-c', str(config_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return 0 if self._process.poll() is None else -1

    def stop_network(self, name=None):
        """终止子进程（name=None 时终止所有）"""
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
        return 0

    def get_network_infos(self, max_len=10):
        """执行 easytier-cli peer --json"""
        output = subprocess.check_output(
            [self._cli_path, '-o', 'json', 'peer'], timeout=10
        )
        return json.loads(output)

    # ── 节点检测（CLI 独有功能） ──
    def check_peers(self, peer_list, max_wait=10):
        """启动临时 easytier-core 实例，检测节点连通性"""
        ...

    def check_peers_available(self, rpc_port, peer_list):
        """通过 easytier-cli peer --json 检测已连接节点"""
        ...

    def check_connector(self, rpc_port):
        """通过 easytier-cli connector --json 检测连接器状态"""
        ...
```

## EasyTierFacade — 门面

```python
class EasyTierFacade:
    """
    EasyTier 门面，自动选择可用适配器。

    优先级（降级链）：
    1. FfiMainAdapter  — 预留，未来 main 分支新接口
    2. FfiAdapter       — 当前默认（v2.4.5/v2.6.4 FFI）
    3. CoreCliAdapter   — CLI 子进程（兜底）
    """

    ADAPTER_CLASSES = [FfiMainAdapter, FfiAdapter, CoreCliAdapter]

    def __init__(self, adapter_class=None):
        self._instance_name: Optional[str] = None
        if adapter_class:
            self._adapter = adapter_class()
        else:
            self._adapter = self._auto_detect()

    def _auto_detect(self) -> IEasyTierAdapter:
        for cls in self.ADAPTER_CLASSES:
            adapter = cls()
            if adapter.is_available():
                logger.info(f"EasyTier adapter: {cls.__name__}")
                return adapter
        raise RuntimeError("No EasyTier adapter available")

    @property
    def adapter_name(self) -> str:
        return type(self._adapter).__name__

    @property
    def current_instance_name(self) -> Optional[str]:
        """当前运行的实例名（供 services.py stop_all 使用）"""
        return self._instance_name

    # ── 核心委托方法 ──
    def start_network(self, toml, name):
        self._instance_name = name
        return self._adapter.start_network(toml, name)

    def stop_network(self, name=None):
        self._instance_name = None
        return self._adapter.stop_network(name)

    def get_network_infos(self, max_len=10):
        return self._adapter.get_network_infos(max_len)

    def get_version(self):
        return self._adapter.get_version()

    # ── 扩展方法（不在接口中，但 Facade 聚合提供） ──
    def check_peers(self, peer_list, max_wait=10):
        if hasattr(self._adapter, 'check_peers'):
            return self._adapter.check_peers(peer_list, max_wait)
        raise NotImplementedError("Current adapter does not support check_peers")

    def check_peers_available(self, rpc_port, peer_list):
        if hasattr(self._adapter, 'check_peers_available'):
            return self._adapter.check_peers_available(rpc_port, peer_list)
        raise NotImplementedError("Current adapter does not support check_peers_available")

    def check_connector(self, rpc_port):
        if hasattr(self._adapter, 'check_connector'):
            return self._adapter.check_connector(rpc_port)
        raise NotImplementedError("Current adapter does not support check_connector")

    # ── 单例 ──
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

## 版本差异对比

| 功能 | FfiMainAdapter | FfiAdapter | CoreCliAdapter |
|---|---|---|---|
| **状态** | 预留 | 当前默认 | 兜底 |
| **实现方式** | FFI `collect_network_infos` | FFI `collect_network_infos` | `easytier-cli peer --json` |
| **启动网络** | `parse_config` + `run_network_instance` | 同左 | `subprocess.Popen` |
| **停止网络** | `retain_network_instance`（None=停全部） | 同左 | `process.terminate()` |
| **获取版本** | 正则搜 `.so` 二进制 | 正则搜 `.so` 二进制 | `easytier-core --version` |
| **节点检测** | ❌ 不支持 | ❌ 不支持 | ✅ 完整支持 |
| **线程安全** | `threading.RLock` | `threading.RLock` | 子进程隔离 |
| **Android 兼容** | ✅ | ✅ | ❌ 无二进制 |

## 降级链

```
启动 → FfiMainAdapter.is_available()?
         ├─ 是 → 使用 FfiMainAdapter（预留，未来 main 分支新接口）
         └─ 否 → FfiAdapter.is_available()?
                   ├─ 是 → 使用 FfiAdapter（当前默认，v2.4.5/v2.6.4 FFI）
                   └─ 否 → CoreCliAdapter.is_available()?
                             ├─ 是 → 使用 CoreCliAdapter（CLI 子进程）
                             └─ 否 → RuntimeError("No EasyTier adapter available")
```

## 业务层导入方式

去掉 `et_bridge.py`，业务层直接从 `et_adapters` 导入：

```python
# services.py / monitor.py / et_core.py
from et_adapters import get_facade
et_bridge = get_facade()
```

`_current_instance_name` 替换为 Facade 的 `current_instance_name` property：

```python
# services.py stop_all 中
# 旧: from utils.et_bridge import _current_instance_name
#      stopped = [_current_instance_name] if _current_instance_name else []
# 新:
stopped = [et_bridge.current_instance_name] if et_bridge.current_instance_name else []
```

## check_peers.py 兼容层

```python
"""EasyTier 节点检测工具（兼容层）"""
from et_adapters.facade import EasyTierFacade

# 保留工具函数（不依赖适配器）
def get_random_string(length=16): ...
def get_available_port(start_port=15888, end_port=65535): ...

# 核心功能委托给适配器
def check_peers(bin_path, peer_list, max_wait_second=10):
    facade = EasyTierFacade.get_instance()
    return facade.check_peers(peer_list, max_wait_second)

def check_peers_available_use_peer(bin_path, rpc_port, peer_list):
    facade = EasyTierFacade.get_instance()
    return facade.check_peers_available(rpc_port, peer_list)

def check_peers_available_use_connector(bin_path, rpc_port):
    facade = EasyTierFacade.get_instance()
    return facade.check_connector(rpc_port)
```

## 受影响的文件

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `backend/et_adapters/__init__.py` | **新增** | 导出 `EasyTierFacade`, `get_facade` |
| `backend/et_adapters/interface.py` | **新增** | `IEasyTierAdapter` 抽象接口（4 方法） |
| `backend/et_adapters/facade.py` | **新增** | `EasyTierFacade` 门面类 |
| `backend/et_adapters/ffi_base.py` | **新增** | `BaseFfiAdapter` 基类 |
| `backend/et_adapters/ffi_adapter.py` | **新增** | `FfiAdapter`（当前默认，v2.4.5/v2.6.4 FFI） |
| `backend/et_adapters/ffi_main.py` | **新增** | `FfiMainAdapter`（预留，未来 main 分支新接口） |
| `backend/et_adapters/core_cli.py` | **新增** | `CoreCliAdapter`（CLI 子进程） |
| `backend/utils/et_bridge.py` | **删除** | 不再需要，业务层直接导入 `et_adapters` |
| `backend/utils/check_peers.py` | 修改 | 保留工具函数，节点检测委托给适配器 |
| `backend/actions/services.py` | 修改 | `from et_adapters import get_facade` |
| `backend/actions/monitor.py` | 修改 | `from et_adapters import get_facade` |
| `backend/actions/et_core.py` | 修改 | `from et_adapters import get_facade` |
| `backend/actions/peers.py` | **0 行** | `from utils import check_peers as check_util` 不变 |
| `backend/build_core.py` | 修改 | 新增 `--hidden-import et_adapters.*`，移除 `utils.et_bridge` |

## `build_core.py` 变更详情

```python
# 在现有 hidden-import 列表后新增：
"--hidden-import", "et_adapters",
"--hidden-import", "et_adapters.interface",
"--hidden-import", "et_adapters.facade",
"--hidden-import", "et_adapters.ffi_base",
"--hidden-import", "et_adapters.ffi_adapter",
"--hidden-import", "et_adapters.ffi_main",
"--hidden-import", "et_adapters.core_cli",
```

## 未来扩展

新增版本时只需：

```python
# 修改 et_adapters/ffi_main.py 的 REQUIRED_SYMBOLS
class FfiMainAdapter(BaseFfiAdapter):
    REQUIRED_SYMBOLS = [
        'parse_config', 'run_network_instance', 'retain_network_instance',
        'delete_network_instance',  # ← 新增符号
        'collect_network_infos',
        'list_instance',             # ← 新增符号
        'set_tun_fd',
        'call_json_rpc',             # ← 新增符号
        'get_error_msg', 'free_string',
    ]
    MISSING_SYMBOLS = []

# Facade 自动选择：满足新符号 → FfiMainAdapter，不满足 → FfiAdapter
```

无需修改任何业务代码。`FfiAdapter` 永远保留作为旧版兼容，新符号出现时 `FfiMainAdapter` 自动接管。