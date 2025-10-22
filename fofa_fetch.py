import os
import re
import requests
import time
import concurrent.futures
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=Ym9keT0iaXB0di9saXZlL3poX2NuLmpzIiAmJiBzd": "ip.txt",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
IPTV_FILE = "IPTV.txt"

# CCTV频道映射
CCTV_CHANNELS = {
    "CCTV1-综合": "0001_1",
    "CCTV2-财经": "0002_1",
    "CCTV3-综艺": "0003_1",
    "CCTV4-中文国际": "0004_1",
    "CCTV5-体育": "0005_1",
    "CCTV6-电影": "0006_1",
    # 可继续添加
}

# 卫视频道示例
SAT_CHANNELS = {
    "湖南卫视": "hnws_1",
    "浙江卫视": "zjws_1",
    "东方卫视": "dfws_1",
    "北京卫视": "bjws_1",
}

# ===============================
# 计数逻辑
def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE).read().strip())
        except:
            return 0
    return 0

def save_run_count(count):
    open(COUNTER_FILE, "w").write(str(count))

def check_and_clear_files_by_run_count():
    os.makedirs(IP_DIR, exist_ok=True)
    count = get_run_count() + 1
    if count >= 73:
        print(f"🧹 第 {count} 次运行，清空 {IP_DIR} 下所有 .txt 文件")
        for f in os.listdir(IP_DIR):
            if f.endswith(".txt"):
                os.remove(os.path.join(IP_DIR, f))
        save_run_count(1)
        return "w", 1
    else:
        save_run_count(count)
        return "a", count

# ===============================
# 获取 FOFA IP
def fetch_ips():
    all_ips = set()
    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
            all_ips.update(u.strip() for u in urls_all)
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)
    return all_ips

# ===============================
# 保存 IP 文件
def save_ips(all_ips):
    mode, run_count = check_and_clear_files_by_run_count()
    path = os.path.join(IP_DIR, "all_ips.txt")
    with open(path, mode, encoding="utf-8") as f:
        for ip_port in sorted(all_ips):
            f.write(ip_port + "\n")
    print(f"{path} 已{'覆盖' if mode=='w' else '追加'}写入 {len(all_ips)} 个 IP")
    return run_count

# ===============================
# 生成 IPTV.txt（多线程）
def generate_iptv():
    print("🔔 生成 IPTV.txt（多线程） ...")
    ip_file = os.path.join(IP_DIR, "all_ips.txt")
    if not os.path.exists(ip_file):
        print("⚠️ IP文件不存在，跳过")
        return

    with open(ip_file, encoding="utf-8") as f:
        ip_list = [x.strip() for x in f if x.strip()]

    all_lines = []

    def check_ip_channel(ip_port, name, code):
        url = f"http://{ip_port}/tsfile/live/{code}.m3u8"
        try:
            r = requests.head(url, timeout=5)
            if r.status_code == 200:
                return f"{name},{url}${ip_port}"
        except:
            return None

    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for ip_port in ip_list:
            for name, code in {**CCTV_CHANNELS, **SAT_CHANNELS}.items():
                tasks.append(executor.submit(check_ip_channel, ip_port, name, code))
        for future in concurrent.futures.as_completed(tasks):
            res = future.result()
            if res:
                all_lines.append(res)

    # 去重
    seen = set()
    valid_lines = []
    for line in all_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in seen:
            seen.add(url_part)
            valid_lines.append(line)

    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "https://kakaxi-1.asia/LOGO/Disclaimer.mp4"

    with open(IPTV_FILE, "w", encoding="utf-8") as f:
        f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
        f.write("更新时间,#genre#\n")
        f.write(f"{beijing_now},{disclaimer_url}\n\n")

        # CCTV频道
        f.write("央视频道,#genre#\n")
        for line in valid_lines:
            if line.split(",", 1)[0].startswith("CCTV"):
                f.write(line + "\n")
        f.write("\n")

        # 卫视频道
        f.write("卫视频道,#genre#\n")
        for line in valid_lines:
            if not line.split(",", 1)[0].startswith("CCTV"):
                f.write(line + "\n")
    print(f"🎯 IPTV.txt 生成完成，共 {len(valid_lines)} 条频道")

# ===============================
# GitHub 推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    os.system("git add 计数.txt")
    os.system("git add ip/*.txt || true")
    os.system("git add IPTV.txt || true")
    os.system('git commit -m "自动更新：计数、IP文件、IPTV.txt" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo '⚠️ 推送失败'")

# ===============================
# 主执行逻辑
if __name__ == "__main__":
    all_ips = fetch_ips()
    run_count = save_ips(all_ips)
    # 只有特定运行次数生成 IPTV
    if run_count in [12, 24, 36, 48, 60, 72]:
        generate_iptv()
    push_all_files()
