import subprocess
import os

rar_path = r"c:\Users\wade\Documents\taxi\2.北京市出租车数据\2.T_drive 轨迹数据.rar"
extract_path = r"c:\Users\wade\Documents\taxi\2.北京市出租车数据"
seven_zip = r"C:\Program Files\7-Zip\7z.exe"

try:
    print("正在解压 RAR 文件...")
    cmd = [seven_zip, "x", rar_path, f"-o{extract_path}", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("\n" + result.stdout)
        print("\n解压完成!")
    else:
        print("\n解压失败:")
        print(result.stderr)
except FileNotFoundError:
    print("错误: 找不到 7-Zip 安装程序")
    print("请确认 7-Zip 已安装到: C:\Program Files\7-Zip\7z.exe")
except Exception as e:
    print(f"错误: {e}")
