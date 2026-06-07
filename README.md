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

下载 <a href="https://github.com/freeok/so-novel/releases">SoNovel</a>（Windows 版）并解压，然后将本工具放入 SoNovel 根目录：

```
SoNovel/                     # SoNovel 引擎根目录
├── app.jar
├── config.ini
├── runtime/
├── downloads/
└── auto-so-novel/           # ← 把整个文件夹放这里
    ├── batch_download.py
    └── books.txt
```

> 也可通过环境变量 <code>SONOVEL_DIR</code> 或运行参数 <code>--sonovel-dir &lt;路径&gt;</code> 指定 SoNovel 位置。

### 2. 编辑书名

打开 `books.txt`，每行一个书名：

```
斗罗大陆
全职高手
诡秘之主
```

### 3. 运行

双击 `启动.bat`。

脚本自动完成：清理残留进程 → 启用 WebUI → 启动 SoNovel → 逐本搜索下载 → 恢复配置。

## ⚙️ 配置

打开 `batch_download.py`，顶部配置区可直接修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SONOVEL_DIR` | 自动查找 | SoNovel 目录，查找顺序：`--sonovel-dir` > `SONOVEL_DIR` 环境变量 > 项目内 `SoNovel/` > 父目录自动搜索 |
| `BOOK_TIMEOUT` | `180`（秒） | 单本下载超时 |
| `FORMAT` | `txt` | 下载格式 |
| `SEARCH_LIMIT` | `3` | 搜索匹配条数上限 |
| `SKIP_THRESHOLD` | `1` | 连续搜索失败 N 次后永久跳过 |

## 📌 依赖

- [SoNovel](https://github.com/freeok/so-novel) — 小说下载引擎（Java）
- Python 3.8+, [requests](https://pypi.org/project/requests/)

## 📄 许可证

MIT
