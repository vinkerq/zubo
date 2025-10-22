#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fofa_search_onepage.py
使用已有 qbase64 查询 FOFA，仅抓取第一页结果，并保存 ip 到 fofa-ip.txt
"""

import os
import requests
import sys

# ========== 配置区 ==========
EMAIL = os.environ.get("FOFA_EMAIL", "")  # FOFA 邮箱
KEY = os.environ.get("FOFA_KEY", "")      # FOFA API Key

# 已经 base64 编码好的查询
QBASE64 = "Ym9keT0iaXB0di9saXZlL3poX2NuLmpzIiAmJiBzdGF0dXNfY29kZT0iMjAwIiAmJiBjb3VudHJ5PSJDTiI="

PAGE_SIZE = 1000        # 每页返回条数（可根据账户权限调整）
OUTPUT_FILE = "fofa-ip.txt"
# ============================

API_URL = "https://fofa.info/api/v1/search/all"

def check_credentials():
    if not EMAIL or not KEY:
        print("错误：未设置 FOFA_EMAIL 或 FOFA_KEY（环境变量）。")
        sys.exit(1)

def fetch_first_page():
    params = {
        "email": EMAIL,
        "key": KEY,
        "qbase64": QBASE64,
        "page": 1,
        "size": PAGE_SIZE,
        "fields": "ip"
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_ips(results) -> set:
    ips = set()
    for item in results:
        if isinstance(item, (list, tuple)) and len(item) > 0:
            candidate = item[0]
        else:
            candidate = item
        if isinstance(candidate, str):
            s = candidate.strip()
            if s and "." in s and 7 <= len(s) <= 45:
                ips.add(s)
    return ips

def main():
    check_credentials()
    print("开始查询 FOFA（仅第一页）")
    try:
        data = fetch_first_page()
        results = data.get("results") or data.get("data") or []
        if not results:
            print("未找到任何结果")
            return

        ips = extract_ips(results)
        if ips:
            sorted_ips = sorted(ips, key=lambda x: tuple(int(p) if p.isdigit() else 0 for p in x.split(".")[:4]))
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for ip in sorted_ips:
                    f.write(ip + "\n")
            print(f"完成。共写入 {len(sorted_ips)} 个 IP 到文件: {OUTPUT_FILE}")
        else:
            print("未找到任何 IP。")

    except requests.HTTPError as e:
        print("\nHTTPError:", e)
        if e.response is not None:
            print("响应内容：", e.response.text[:1000])
    except Exception as e:
        print("\n出错：", str(e))

if __name__ == "__main__":
    main()