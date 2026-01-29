from mcp.server.fastmcp import FastMCP
import subprocess
import os
import sys


# 初始化 FastMCP
mcp = FastMCP("ForensicToolbox")

# 設定工具目錄路徑 (假設工具放在同級目錄的 Sysinternals Suite 中)
# 也可以根據實際環境調整
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE_DIR, "Sysinternals Suite")

def run_sysinternals_tool(tool_name, args):
    """通用函式：執行 Sysinternals 工具並處理路徑"""
    # 確保使用絕對路徑，解決路徑中包含空格 (如 'Sysinternals Suite') 的問題
    tool_path = os.path.abspath(os.path.join(TOOLS_DIR, tool_name))
    
    # 如果工具目錄找不到，嘗試直接執行 (依賴 PATH)，這時就只用工具名稱
    if not os.path.exists(tool_path):
        tool_path = tool_name

    try:
        # 使用 subprocess 時，tool_path 即使有空格 (如 "C:\Path With Spaces\tool.exe") 
        # Python 也會自動處理，不需要額外的引號
        cmd = [tool_path, "-accepteula"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error executing {tool_name} (Path: {tool_path}): {str(e)}"

@mcp.tool()
def collect_autoruns():
    """採集 Windows 啟動項資訊 (使用 autorunsc.exe)"""
    return run_sysinternals_tool("autorunsc.exe", ["-a", "*", "-m"])

@mcp.tool()
def list_running_processes():
    """使用 PowerShell 獲取詳細的執行中進程列表，包含路徑與公司資訊"""
    # 強制設定 PowerShell 輸出編碼為 UTF8，避免中文亂碼
    # 同時過濾掉沒有 Path 的進程（通常是系統核心進程），減少資料量並提高準確度
    ps_command = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Get-Process | Where-Object { $_.Path -ne $null } | "
        "Select-Object Name, Id, Path, Company, Description | ConvertTo-Json"
    )
    try:
        # 使用 powershell.exe 並明確指定編碼
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode != 0:
            return f"PowerShell Error: {result.stderr}"
        return result.stdout if result.stdout else "[]"

    except Exception as e:
        return f"Error listing processes: {str(e)}"



@mcp.tool()
def check_file_signatures(file_path: str):
    """檢查指定檔案的數位簽章 (使用 sigcheck.exe)"""
    return run_sysinternals_tool("sigcheck.exe", [ "-a", "-h", "-i", file_path  ])

@mcp.tool()
def list_network_connections():
    """獲取目前的網路連線狀態 (使用 tcpvcon.exe)"""
    return run_sysinternals_tool("tcpvcon.exe", ["-a", " -c"])

@mcp.tool()
def list_loaded_dlls(process_identifier: str):
    """
    獲取指定進程載入的 DLL 模組 (使用 Listdlls.exe)
    Args:
        process_identifier: 進程名稱 (如 "notepad.exe") 或 PID。
    """
    return run_sysinternals_tool("listdlls.exe", [process_identifier])

if __name__ == "__main__":
    mcp.run()
