import os
from datetime import datetime, timezone, timedelta

IP_DIR = "ip"     # 存放 IP 文件
RTP_DIR = "rtp"   # 存放 RTP 文件
OUTPUT_FILE = "IPTV.txt"

def extract_province_operator(filename):
    """从文件名提取省份和运营商，如 广东电信.txt -> 广东,电信"""
    name = filename.replace(".txt", "")
    if "电信" in name:
        return name.replace("电信", ""), "电信"
    elif "联通" in name:
        return name.replace("联通", ""), "联通"
    elif "移动" in name:
        return name.replace("移动", ""), "移动"
    else:
        return name, "未知"

def combine_ip_rtp(ip_dir, rtp_dir, output_file):
    combined_lines = []

    # 遍历 IP 文件夹
    for ip_file in os.listdir(ip_dir):
        if not ip_file.endswith(".txt"):
            continue

        ip_path = os.path.join(ip_dir, ip_file)
        rtp_path = os.path.join(rtp_dir, ip_file)  # 假设同名

        if not os.path.exists(rtp_path):
            print(f"⚠️ RTP 文件不存在: {rtp_path}, 跳过")
            continue

        province, operator = extract_province_operator(ip_file)

        # 读取 IP 和 RTP 内容
        with open(ip_path, encoding="utf-8") as f_ip:
            ip_list = [x.strip() for x in f_ip if x.strip()]

        with open(rtp_path, encoding="utf-8") as f_rtp:
            rtp_list = [x.strip() for x in f_rtp if x.strip()]

        # 组合
        for ip in ip_list:
            for rtp_line in rtp_list:
                if "," not in rtp_line:
                    continue
                ch_name, rtp_url = rtp_line.split(",", 1)
                combined_lines.append({
                    "channel": ch_name,
                    "url": f"http://{ip}{rtp_url}",
                    "province": province,
                    "operator": operator
                })

    # 写入 IPTV 风格文件
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
        f.write("更新时间,#genre#\n")
        f.write(f"{beijing_now},https://kakaxi-1.asia/LOGO/Disclaimer.mp4\n\n")

        # 分频道写入
        channels_sorted = sorted(combined_lines, key=lambda x: x["channel"])
        current_channel = None
        for item in channels_sorted:
            if item["channel"] != current_channel:
                current_channel = item["channel"]
                f.write(f"{current_channel},#genre#\n")
            f.write(f"{item['channel']},{item['url']}${item['province']}{item['operator']}\n")
        f.write("\n")

    print(f"✅ IPTV 文件生成完成，共 {len(combined_lines)} 条记录，输出到 {output_file}")

if __name__ == "__main__":
    combine_ip_rtp(IP_DIR, RTP_DIR, OUTPUT_FILE)
