#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fofa_search_onepage.py
使用已有 qbase64 查询 FOFA，仅抓取第一页结果，并保存 ip 到 fofa-ip.txt
"""

import requests
import base64

# ========== 配置区 ==========
EMAIL = "lcsn15801@163.com"      # FOFA 邮箱
KEY = "22239dc8660961e8b2fb7b9ebe6aee26"  # FOFA API Key

# FOFA 搜索语句
SEARCH_QUERY = 'body="iptv/live/zh_cn.js" && status_code="200" && country="CN"'

# 将搜索语句转换成 Base64（FOFA API 要求）
QBASE64 = base64.b64encode(SEARCH_QUERY.encode()).decode()

PAGE_SIZE = 1000        # 每页返回条数
OUTPUT_FILE = "fofa-ip.txt"
API_URL = "https://fofa.info/api/v1/search/all"
# ============================

def fetch_first_page():
    """抓取 FOFA 查询第一页结果"""
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
    """从 FOFA 返回结果中提取 IP"""
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
    print("开始查询 FOFA（仅第一页）")
    try:
        data = fetch_first_page()
        results = data.get("results") or data.get("data") or []
        if not results:
            print("未找到任何结果")
            return

        ips = extract_ips(results)
        if ips:
            sorted_ips = sorted(
                ips,
                key=lambda x: tuple(int(p) if p.isdigit() else 0 for p in x.split(".")[:4])
            )
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
