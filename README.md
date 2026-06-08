<div align="center">
  <h1>📚 auto-so-novel — 小说批量下载脚本</h1>
  <p>
    <strong>免费 · 开源 · 自动化 · 无需手动操作</strong>
  </p>
  <p>
    一个基于 <a href="https://github.com/freeok/so-novel">so-novel</a> 引擎的<strong>小说批量下载脚本</strong>，<br>
    把书名写在 <code>books.txt</code> 里，一键<strong>批量下载小说</strong>到本地。
  </p>
  <p>
    <img src="https://img.shields.io/badge/language-Python-blue?style=flat-square">
    <img src="https://img.shields.io/badge/status-stable-green?style=flat-square">
    <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square">
  </p>
  <hr>
  <p>
    <strong>English:</strong> Batch novel downloader · Chinese novel download tool ·<br>
    Auto download web novels from multiple sources with one click.
  </p>
</div>

---

## 📖 简介

把小说名写进 `books.txt`，双击 `启动.bat`，自动搜索并批量下载到本地。基于 so-novel 引擎，支持多来源免费小说下载，自动跳过已下载、容错重试。

## 🚀 快速开始

### 完整下载流程

```
books.txt → auto-so-novel → so-novel 引擎 → 搜索 → 匹配 → 下载 → downloads/ 目录
```

### 第一步：准备环境

1. 下载 **so-novel**（小说下载引擎）：[so-novel Releases](https://github.com/freeok/so-novel/releases)
2. 下载本工具 **auto-so-novel**：[点击下载](https://github.com/King-NO-1/auto-so-novel)
3. 将 `auto-so-novel` 文件夹放入 `SoNovel` 根目录：

```
SoNovel/                 
├── app.jar                
├── config.ini              
├── runtime/                 
├── downloads/             
└── auto-so-novel/           # ← 本工具放这里
    ├── batch_download.py   
    ├── books.txt         
    └── 启动.bat           
```

> 也可通过环境变量 `SONOVEL_DIR` 或运行参数 `--sonovel-dir <路径>` 指定 so-novel 位置。

### 第二步：编辑书单

打开 `books.txt`，每行写一本小说名称：

```
斗罗大陆
全职高手
诡秘之主
庆余年
大奉打更人
```

### 第三步：一键运行

**Windows 用户：** 双击 `启动.bat`

## ⚙️ 配置说明

打开 `batch_download.py`，顶部配置区可直接修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `BOOK_TIMEOUT` | `180`（秒） | 单本小说下载超时时间 |
| `FORMAT` | `txt` | 小说下载格式 |
| `SEARCH_LIMIT` | `3` | 搜索结果匹配条数上限 |
| `SKIP_THRESHOLD` | `1` | 连续搜索失败 N 次后永久跳过 |

> ⚠️ so-novel 搜不到的书，本工具也没办法下载。

## 📌 依赖

- **[so-novel](https://github.com/freeok/so-novel)** — 开源小说下载引擎（Java）
- **Python 3.8+** — 脚本运行环境
- **[requests](https://pypi.org/project/requests/)** — HTTP 请求库

```bash
pip install requests
```

## 🏷️ 关键词

`小说下载` `批量下载小说` `网络小说下载` `免费小说下载工具` `小说爬虫` `novel download` `batch novel downloader` `Chinese novel downloader` `web novel scraper` `novel batch download` `免费下载小说` `小说采集工具` `整本小说下载` `小说下载器`

## 📄 许可证

[MIT](LICENSE)


