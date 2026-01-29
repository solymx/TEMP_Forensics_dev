from mcp.server.fastmcp import FastMCP
import subprocess, os, json, time

mcp = FastMCP("RegistryForensics")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE_DIR, "tools", "zimmerman")
OUTPUT_BASE = os.path.join(BASE_DIR, "output")

def _run(tool_name: str, args: list[str]) -> dict:
    tool_path = os.path.abspath(os.path.join(TOOLS_DIR, tool_name))
    if not os.path.exists(tool_path):
        return {"ok": False, "error": f"Tool not found: {tool_path}"}

    cmd = [tool_path] + args
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],  # 避免回傳爆量
        "stderr": p.stderr[-4000:],
        "cmd": cmd,
    }

def _new_case_dir(case_name: str | None = None) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = case_name or f"case-{ts}"
    out_dir = os.path.join(OUTPUT_BASE, name)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

@mcp.tool()
def parse_amcache(amcache_hve_path: str, case_name: str = ""):
    """
    解析 amcache.hve -> CSV
    需求：tools/zimmerman/AmcacheParser.exe
    """
    out_dir = _new_case_dir(case_name or "amcache")
    out_csv_dir = os.path.join(out_dir, "amcache")
    os.makedirs(out_csv_dir, exist_ok=True)

    r = _run("AmcacheParser.exe", ["-f", amcache_hve_path, "--csv", out_csv_dir])
    return {
        "tool": "AmcacheParser",
        "out_dir": out_csv_dir,
        "result": r,
        "hint": "CSV 通常會在 out_dir 下，多個檔案（依 artifact 分類）"
    }

@mcp.tool()
def parse_registry_with_recmd(hives_dir: str, case_name: str = "", batch_file: str = ""):
    """
    RECmd 批次解析 hive 目錄 -> CSV
    需求：tools/zimmerman/RECmd.exe
    """
    out_dir = _new_case_dir(case_name or "recmd")
    out_csv_dir = os.path.join(out_dir, "recmd")
    os.makedirs(out_csv_dir, exist_ok=True)

    args = ["-d", hives_dir, "--csv", out_csv_dir]
    if batch_file:
        args += ["--bn", batch_file]  # 依你的 batch 設定調整參數（Zimmerman 支援不同模式）
    r = _run("RECmd.exe", args)

    return {
        "tool": "RECmd",
        "out_dir": out_csv_dir,
        "result": r,
        "hint": "把 out_dir 內 CSV 打包/上傳，AI 可做 persistence 與時間線分析"
    }

if __name__ == "__main__":
    mcp.run()
