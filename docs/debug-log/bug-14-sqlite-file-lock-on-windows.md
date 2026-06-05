# Bug 14：Windows 下 SQLite 文件被占用

## 现象

在验证向量检索 smoke test 时，逻辑已经正常返回结果，但临时目录清理失败：

```text
PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。
```

被占用的文件是：

```text
memory.sqlite3
vectors.sqlite3
```

## 排查过程

1. 向量检索 smoke test 使用 `tempfile.TemporaryDirectory()` 创建临时 SQLite 文件。
2. 流程结束时 Python 尝试删除临时目录。
3. Windows 报 SQLite 文件仍被进程占用。
4. 检查 `MemoryStore` 和 `SQLiteVectorIndex`，发现代码使用：

```python
with self._connect() as conn:
    ...
```

这会提交或回滚事务，但不会自动关闭 sqlite connection。

## 根因

`sqlite3.Connection` 的 context manager 只管理事务，不负责关闭连接。Linux/macOS 上有时不明显，但 Windows 对文件锁更严格，所以临时目录删除或后续文件操作会失败。

## 修复

改成：

```python
from contextlib import closing

with closing(self._connect()) as conn:
    with conn:
        ...
```

读操作也使用 `closing(self._connect())`，保证查询结束后连接释放。

## 面试复盘说法

> 我在做向量检索 smoke test 时发现 Windows 下临时 SQLite 文件无法删除。排查后发现不是向量检索逻辑错误，而是 sqlite connection 没有显式关闭。Python 的 sqlite connection context manager 只管理事务，不负责关闭连接。  
> 修复后我给 `MemoryStore` 和 `SQLiteVectorIndex` 都加了文件释放回归测试，保证 Windows 下 SQLite 文件不会被长期占用。
