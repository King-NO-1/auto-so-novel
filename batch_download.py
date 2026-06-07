"""
auto_so_novel — SoNovel 批量下载脚本
通过 WebUI API (HTTP) 自动搜索+下载小说

用法:
  1. 在 books.txt 列出书名（每行一本）
  2. python batch_download.py

依赖:
  - SoNovel (https://github.com/freeok/so-novel) 已安装
  - Python 3.8+，requests 库

更新说明 v4:
  - 移除榜单扫描模式，专注 books.txt
  - 搜索匹配改为前 3 条中按书名匹配，多匹配选更新时间最新的
  - 新增跳过历史：连续 N 次搜索不到后不再搜
"""

import requests
import time
import sys
import os
import re
import signal
import atexit
import socket
import subprocess
import configparser
import threading
import json
from datetime import datetime

# Windows 终端强制 UTF-8
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ========== 配置区 ==========

# 项目目录（脚本所在目录）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 书名文件路径（每行一个书名，与脚本同目录）
BOOK_FILE = os.path.join(PROJECT_DIR, "books.txt")

# SoNovel 路径（指向安装目录）
SONOVEL_DIR = r"D:\Download\sonovel-windows\SoNovel"
JAVA_EXE = os.path.join(SONOVEL_DIR, "runtime", "bin", "java.exe")
APP_JAR = os.path.join(SONOVEL_DIR, "app.jar")
CONFIG_INI = os.path.join(SONOVEL_DIR, "config.ini")
JVM_INI = os.path.join(SONOVEL_DIR, "sonovel.l4j.ini")
JAVA_LOG = os.path.join(SONOVEL_DIR, "logs", "webui-server.log")

# 脚本自身日志目录（项目目录下）
LOG_DIR = os.path.join(PROJECT_DIR, "logs")

# 下载格式
FORMAT = "txt"

# 搜索结果匹配条数上限（取前 N 条匹配）
SEARCH_LIMIT = 3

# 单本下载超时（秒）
BOOK_TIMEOUT = 180  # 3 分钟

# 搜索跳过阈值：搜索不到的书连续 N 次后不再搜
SKIP_THRESHOLD = 1
SKIP_HISTORY_FILE = os.path.join(PROJECT_DIR, "batch_skip_history.json")

# ========== 配置区结束 ==========

BASE_URL = "http://localhost:7765"

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 脚本自身日志
log_file = open(os.path.join(LOG_DIR, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                "w", encoding="utf-8")


def log(msg, nl=True):
    """打印并写日志"""
    formatted = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    if nl:
        print(formatted, flush=True)
    else:
        print(formatted, end="", flush=True)
    log_file.write(formatted + "\n")
    log_file.flush()


def load_skip_history():
    """加载搜索跳过历史"""
    if os.path.exists(SKIP_HISTORY_FILE):
        try:
            with open(SKIP_HISTORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_skip_history(history):
    """保存搜索跳过历史"""
    try:
        with open(SKIP_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[警告] 保存跳过历史失败: {e}")


# 模块级跳过历史缓存
_skip_history = None


class SonovelClient:
    def __init__(self):
        self.session = requests.Session()

    def health_check(self):
        try:
            r = self.session.get(f"{BASE_URL}/config", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def search(self, keyword):
        """聚合搜索，返回结果列表"""
        r = self.session.get(
            f"{BASE_URL}/search/aggregated",
            params={"kw": keyword},
            timeout=120
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data.get("data", [])
        return data

    def fetch_book(self, url, book_name, author="", source_id=None):
        """同步下载书籍到服务器的 downloads 目录"""
        params = {"url": url, "bookName": book_name, "format": FORMAT}
        if author:
            params["author"] = author
        if source_id is not None:
            params["sourceId"] = str(source_id)
        r = self.session.get(
            f"{BASE_URL}/book-fetch",
            params=params,
            timeout=7200
        )
        r.raise_for_status()
        try:
            data = r.json()
            if isinstance(data, dict) and data.get("code", 200) != 200:
                raise RuntimeError(data.get("message", "未知错误"))
        except ValueError:
            pass
        return r


def enable_web_mode():
    """临时启用 WebUI 模式"""
    config = configparser.ConfigParser()
    config.read(CONFIG_INI, encoding="utf-8")
    if config.has_section("web") and config.get("web", "enabled", fallback="0") == "0":
        config.set("web", "enabled", "1")
        with open(CONFIG_INI, "w", encoding="utf-8") as f:
            config.write(f)
        return True
    return False


def restore_web_mode():
    """恢复 WebUI 模式为关闭"""
    config = configparser.ConfigParser()
    config.read(CONFIG_INI, encoding="utf-8")
    if config.has_section("web") and config.get("web", "enabled", fallback="") == "1":
        config.set("web", "enabled", "0")
        with open(CONFIG_INI, "w", encoding="utf-8") as f:
            config.write(f)


def read_jvm_args():
    """从 sonovel.l4j.ini 读取 JVM 参数

    注意: 不加载 -Dfile.encoding 参数（该参数用于终端 TUI 模式，
    但会在 Web 模式下破坏 HTTP 请求的 UTF-8 URL 解码）
    """
    args = ["-Dmode=web"]
    if os.path.exists(JVM_INI):
        with open(JVM_INI, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("-Dfile.encoding"):
                    continue
                args.append(line)
    return args


def start_web_server():
    """启动 SoNovel WebUI 服务（stdout/stderr -> 日志文件）"""
    jvm_args = read_jvm_args()
    cmd = [JAVA_EXE] + jvm_args + ["-jar", APP_JAR]
    log(f"启动命令: {' '.join(cmd)}")
    os.makedirs(os.path.dirname(JAVA_LOG), exist_ok=True)
    java_log = open(JAVA_LOG, "a", encoding="utf-8", buffering=1)
    return subprocess.Popen(
        cmd,
        cwd=SONOVEL_DIR,
        stdout=java_log,
        stderr=subprocess.STDOUT,
    )


def check_process_alive(proc):
    """检查进程是否还活着"""
    return proc.poll() is None


def check_port_available(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except OSError:
            return False


def sanitize_filename(name):
    """移除 Windows 文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '', name)


def is_book_name_match(search_result_name, input_name):
    """判断搜索结果的书名是否匹配输入的书名

    规则:
    1. 去空格后精确匹配 → 确认
    2. 一方完全包含另一方，且短书名长度 ≥ 长书名的 50% → 确认
    3. 否则 → 不匹配
    """
    a = search_result_name.replace(" ", "").replace("　", "")
    b = input_name.replace(" ", "").replace("　", "")

    if a == b:
        return True

    if not a or not b:
        return False
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    if short in long:
        if len(short) / len(long) >= 0.5:
            return True

    return False


def download_one(client, book_name):
    """下载单本书：搜索 → 前 3 条匹配 → 选更新时间最新的下载"""
    log(f"{'='*50}")
    log(f"[搜索] {book_name}")

    global _skip_history
    if _skip_history is None:
        _skip_history = load_skip_history()
    book_key = book_name.strip()
    if _skip_history.get(book_key, 0) >= SKIP_THRESHOLD:
        log(f"[跳过] 《{book_name}》已连续 {SKIP_THRESHOLD} 次搜索失败，跳过")
        return False

    try:
        results = client.search(book_name)
    except Exception as e:
        log(f"[失败] 搜索出错: {e}")
        return False

    if not results:
        log(f"[失败] 未搜到: {book_name}")
        _skip_history[book_key] = _skip_history.get(book_key, 0) + 1
        save_skip_history(_skip_history)
        return False

    # 前 SEARCH_LIMIT 条里找匹配的
    matches = []
    for r in results[:SEARCH_LIMIT]:
        fn = r.get("bookName", "")
        if is_book_name_match(fn, book_name):
            matches.append(r)

    if not matches:
        log(f"[失败] 前 {SEARCH_LIMIT} 条无匹配: {book_name}")
        _skip_history[book_key] = _skip_history.get(book_key, 0) + 1
        save_skip_history(_skip_history)
        return False

    # 选结果
    if len(matches) == 1:
        selected = matches[0]
        log(f"[匹配] 《{selected.get('bookName','')}」")
    else:
        # 多个匹配，按最后更新时间降序
        def _update_key(r):
            return r.get("lastUpdateTime") or r.get("latestChapter") or ""
        matches.sort(key=_update_key, reverse=True)
        selected = matches[0]
        update_time = selected.get("lastUpdateTime", "")
        version = f"（更新: {update_time}）" if update_time else ""
        log(f"[多匹配] {len(matches)} 个匹配，选最新: 《{selected.get('bookName','')}」{version}")

    title = selected.get("bookName", "")
    author = selected.get("author", "")
    url = selected.get("url", "")
    source = selected.get("sourceName", "")

    log(f"[选中] 《{title}」({author}) {source}")

    if not url:
        log(f"[失败] 无 URL")
        return False

    try:
        fetch_with_progress(client, url, title, author)

        # 验证文件
        downloads_dir = os.path.join(SONOVEL_DIR, "downloads")
        found = False
        for dirpath, _, filenames in os.walk(downloads_dir):
            for fn in filenames:
                if fn.endswith(f".{FORMAT}"):
                    fn_no_ext = fn.rsplit(".", 1)[0]
                    fn_title = fn_no_ext.split("(")[0] if "(" in fn_no_ext else fn_no_ext
                    if is_book_name_match(fn_title, title):
                        size_mb = os.path.getsize(os.path.join(dirpath, fn)) / 1024 / 1024
                        log(f"[完成] 《{title}」 {size_mb:.1f}MB -> {fn}")
                        found = True
                        break
            if found:
                break
        if not found:
            log(f"[警告] 《{title}」文件未找到（可能下载失败）")
            return False

        # 下载成功，清除跳过历史
        if book_key in _skip_history:
            del _skip_history[book_key]
            save_skip_history(_skip_history)

        return True
    except Exception as e:
        log(f"[失败] 下载出错: {e}")
        return False


def fetch_with_progress(client, url, title, author):
    """带进度提示和完成检测的下载

    双重检测:
    1. 后台线程发 HTTP 请求
    2. 主线程轮询 downloads 根目录检测文件生成+稳定
    """
    downloads_dir = os.path.join(SONOVEL_DIR, "downloads")

    def file_exists():
        """检查 downloads 根目录下目标文件是否已生成"""
        try:
            for fn in os.listdir(downloads_dir):
                if not fn.endswith(f".{FORMAT}"):
                    continue
                fpath = os.path.join(downloads_dir, fn)
                if not os.path.isfile(fpath):
                    continue
                fn_no_ext = fn.rsplit(".", 1)[0]
                fn_title = fn_no_ext.split("(")[0] if "(" in fn_no_ext else fn_no_ext
                if is_book_name_match(fn_title, title):
                    return fpath
        except OSError:
            pass
        return None

    result = {"done": False, "error": None, "response": None}
    done_event = threading.Event()

    def do_fetch():
        try:
            resp = client.fetch_book(url, title, author)
            result["response"] = resp
        except Exception as e:
            result["error"] = e
        finally:
            result["done"] = True
            done_event.set()

    t = threading.Thread(target=do_fetch, daemon=True)
    t.start()

    start = time.time()
    prev_size = -1
    stable_count = 0

    while not done_event.is_set() or stable_count < 3:
        done_event.wait(5)
        elapsed = int(time.time() - start)

        found_path = file_exists()
        if found_path:
            try:
                current_size = os.path.getsize(found_path)
            except OSError:
                current_size = 0

            if current_size == prev_size and prev_size > 0:
                stable_count += 1
                if stable_count >= 3:
                    log(f"  [{title}] 文件稳定 {current_size/1024/1024:.1f}MB ({elapsed}s)")
                    return
            else:
                stable_count = 0
                prev_size = current_size
                if not done_event.is_set():
                    log(f"  [{title}] 文件存在 ({current_size/1024/1024:.1f}MB)，等待合并完成...")

        if elapsed >= BOOK_TIMEOUT:
            if file_exists():
                log(f"  [{title}] 超时但文件已生成，视为完成")
                return
            raise TimeoutError(f"下载超时 {BOOK_TIMEOUT}s")

        if elapsed > 0 and elapsed % 15 == 0:
            status = f"(HTTP {'done' if done_event.is_set() else 'waiting'}, stable {stable_count}/3)"
            log(f"  [{title}] 等待... {elapsed}s/{BOOK_TIMEOUT}s {status}")


def load_book_list():
    """加载书名列表"""
    if os.path.exists(BOOK_FILE):
        with open(BOOK_FILE, encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
        if names:
            return names, BOOK_FILE
    log(f"错误: {BOOK_FILE} 为空或不存在")
    log("请在 books.txt 中每行写一个书名")
    sys.exit(1)


def kill_java_processes():
    """清理残留的 SoNovel Java 进程（只杀占用 7765 端口的）"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if not (":7765" in line):
                continue
            state_col = line.strip().split()
            if not state_col:
                continue
            pid = state_col[-1]
            if not pid.isdigit():
                continue
            log(f"  发现端口 7765 被 PID {pid} 占用，正在关闭...")
            subprocess.run(["taskkill", "/f", "/pid", pid],
                           capture_output=True, timeout=5)
            return
        log("  端口 7765 未被占用")
    except Exception as e:
        log(f"  清理过程异常: {e}")


def filter_existing_books(books):
    """检查 downloads 目录，返回尚未下载的书名列表"""
    downloads_dir = os.path.join(SONOVEL_DIR, "downloads")
    skipped = 0
    log("[检查] 扫描已有文件...")
    existing_files = []
    for dirpath, _, filenames in os.walk(downloads_dir):
        for fn in filenames:
            if fn.endswith(f".{FORMAT}"):
                existing_files.append(fn)

    pending = []
    for name in books:
        found = False
        for fn in existing_files:
            fn_no_ext = fn.rsplit(".", 1)[0]
            fn_title = fn_no_ext.split("(")[0] if "(" in fn_no_ext else fn_no_ext
            if is_book_name_match(fn_title, name):
                log(f"  [跳过] 《{name}》已存在")
                skipped += 1
                found = True
                break
        if not found:
            pending.append(name)

    log(f"待下载: {len(pending)} 本 | 已跳过: {skipped} 本")
    return pending


def stop_java(proc, config_changed):
    """关闭 Java 进程并恢复配置"""
    log("[清理] 关闭 Web 服务...")
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if config_changed:
        try:
            atexit.unregister(cleanup_outer)
        except Exception:
            pass
        restore_web_mode()
    log("[清理] 完成")


def cleanup_outer():
    restore_web_mode()
    log_file.close()


def main():
    """主入口"""
    log(f"auto_so_novel — SoNovel 批量下载 v4")
    log(f"书目文件: {BOOK_FILE}")

    books, source = load_book_list()
    log(f"书名数量: {len(books)} | 格式: {FORMAT}")
    for i, name in enumerate(books, 1):
        log(f"  {i}. {name}")

    # 检查已有文件
    pending_books = filter_existing_books(books)
    if not pending_books:
        log("所有书籍均已下载，无需操作")
        log_file.close()
        return

    # 清理残留 Java 进程
    log("[准备] 清理残留 Java 进程...")
    kill_java_processes()
    time.sleep(2)

    # 启用 WebUI
    state = {"proc": None, "config_changed": enable_web_mode()}

    if state["config_changed"]:
        atexit.register(cleanup_outer)

        def sig_handler(sig, frame):
            print("\n[中断] 正在清理...")
            stop_java(state["proc"], state["config_changed"])
            sys.exit(1)
        signal.signal(signal.SIGINT, sig_handler)

    if not check_port_available(7765):
        log("错误: 端口 7765 已被占用")
        stop_java(state["proc"], state["config_changed"])
        sys.exit(1)

    log("[启动] 启动 SoNovel Web 服务...")
    log(f"  Java 日志: {JAVA_LOG}")
    state["proc"] = start_web_server()

    client = SonovelClient()
    log("[等待] 服务就绪", nl=False)
    sys.stdout.flush()
    for _ in range(90):
        if not check_process_alive(state["proc"]):
            log(f"\n错误: Java 进程已崩溃")
            if os.path.exists(JAVA_LOG):
                with open(JAVA_LOG, encoding="utf-8") as f:
                    lines = f.readlines()[-20:]
                log("最后 20 行 Java 日志:")
                for l in lines:
                    log(f"  {l.rstrip()}")
            stop_java(state["proc"], state["config_changed"])
            sys.exit(1)
        if client.health_check():
            log(" ✓")
            break
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    else:
        log("\n错误: 启动超时 (90s)")
        stop_java(state["proc"], state["config_changed"])
        sys.exit(1)

    # 逐本下载
    success = 0
    fail = 0
    failed_books = []

    for name in pending_books:
        try:
            if download_one(client, name):
                success += 1
            else:
                fail += 1
                failed_books.append(name)
        except Exception as e:
            log(f"[异常] {name}: {e}")
            fail += 1
            failed_books.append(name)

    log(f"{'='*50}")
    log(f"完成! 成功: {success} | 失败: {fail}")
    if failed_books:
        log(f"失败列表:")
        for b in failed_books:
            log(f"  - {b}")
    log(f"文件目录: {os.path.join(SONOVEL_DIR, 'downloads')}")

    stop_java(state["proc"], state["config_changed"])


if __name__ == "__main__":
    main()
