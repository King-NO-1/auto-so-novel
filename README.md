<div align="center">
  <h1>📚 auto-so-novel</h1>
  <p>自动下载小说——把书名写在 <code>books.txt</code> 里，一键批量下载。</p>
  <p>
    <img src="https://img.shields.io/badge/status-stable-green?style=flat-square">
    <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square">
  </p>
  <p>🙏 本脚本使用 <a href="https://github.com/freeok/so-novel"><strong>so-novel</strong></a> 的 WebUI API 实现下载，<br>感谢 so-novel 优秀的开源小说下载引擎。</p>
  <p>⚠️ <strong>so-novel 搜不到的书，本工具也没办法。</strong></p>
</div>

---

## 📋 使用

### 1. 准备

确保已安装 <a href="https://github.com/freeok/so-novel">SoNovel</a>，并安装 Python 依赖：

```bash
pip install requests
```

### 2. 编辑书名

打开 `books.txt`，每行一个书名：

```
斗罗大陆
全职高手
诡秘之主
```

### 3. 运行

```bash
python batch_download.py
```

脚本自动完成：清理残留进程 → 启用 WebUI → 启动 SoNovel → 逐本搜索下载 → 恢复配置。

## ⚙️ 配置

打开 `batch_download.py`，顶部配置区可直接修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SONOVEL_DIR` | `D:\Download\sonovel-windows\SoNovel` | SoNovel 安装目录 |
| `BOOK_TIMEOUT` | `180`（秒） | 单本下载超时 |
| `FORMAT` | `txt` | 下载格式 |
| `SEARCH_LIMIT` | `3` | 搜索匹配条数上限 |
| `SKIP_THRESHOLD` | `1` | 连续搜索失败 N 次后永久跳过 |

## 📁 文件说明

```
auto-so-novel/
├── batch_download.py        # 主脚本
├── books.txt                # 📝 你编辑这个——书名列表
├── README.md                # 本文件
├── batch_skip_history.json  # 跳过历史（自动维护）
├── logs/                    # 运行日志（自动生成）
└── .gitignore
```

下载的文件存放在 `{SONOVEL_DIR}/downloads/` 下。

## 📌 依赖

- [SoNovel](https://github.com/freeok/so-novel) — 小说下载引擎（Java）
- Python 3.8+, [requests](https://pypi.org/project/requests/)

## 📄 许可证

MIT
