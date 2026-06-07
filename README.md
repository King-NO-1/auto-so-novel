<div align="center">
  <h1>📚 auto-so-novel</h1>
  <p><strong>SoNovel WebUI API 批量下载客户端</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python">
    <img src="https://img.shields.io/badge/status-stable-green?style=flat-square">
    <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square">
  </p>
  <p>把书名写在 <code>books.txt</code> 里，自动搜索→匹配→下载，一套走完。</p>
</div>

---

## ✨ 特色

- 🎯 **智能匹配** — 搜索结果前 3 条中按书名模糊匹配，多个匹配自动选更新时间最新的
- ⏭ **跳过历史** — 搜不到的书自动记录，下次直接跳过不再浪费搜索
- 🔌 **零配置** — 自动管理 SoNovel 的启动、WebUI 开关、进程清理
- 📝 **完整日志** — 每次运行生成独立日志文件，搜索→匹配→下载全程可追溯

## 📋 使用

### 1. 准备

确保已安装 [SoNovel](https://github.com/freeok/so-novel) 和 Python 3.8+：

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
| `MAX_WORKERS` | `1` | 同时下载本书 |
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

## 🔄 工作流程

```
books.txt ──→ 搜索 API ──→ 匹配前 3 条 ──→ 选最新 ──→ 下载 ──→ downloads/
                ↑                              │
                └── 未搜到？记录跳过历史，下次跳过 ┘
```

## 📌 依赖

- [SoNovel](https://github.com/freeok/so-novel) — 小说下载引擎（Java）
- Python 3.8+, [requests](https://pypi.org/project/requests/)

## 📄 许可证

MIT
