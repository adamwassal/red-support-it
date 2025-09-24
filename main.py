import socket
from getmac import get_mac_address
from time import strftime
import os
import sys
import platform
import pyautogui
import customtkinter as ctk
from PIL import Image
import psutil
import cpuinfo
import subprocess
import json


# ========== GPU detection ==========
def get_gpus():
    gpus = []

    # NVIDIA via pynvml
    try:
        from pynvml import (
            nvmlInit,
            nvmlDeviceGetCount,
            nvmlDeviceGetHandleByIndex,
            nvmlDeviceGetName,
            nvmlDeviceGetMemoryInfo,
            nvmlShutdown,
        )

        nvmlInit()
        count = nvmlDeviceGetCount()
        for i in range(count):
            h = nvmlDeviceGetHandleByIndex(i)
            name = nvmlDeviceGetName(h)
            if isinstance(name, bytes):
                name = name.decode()
            mem = nvmlDeviceGetMemoryInfo(h)
            gpus.append(
                {
                    "vendor": "NVIDIA",
                    "model": name,
                    "memory_mib": mem.total // (1024**2),
                }
            )
        nvmlShutdown()
        if gpus:
            return gpus
    except Exception:
        pass

    # Windows WMI
    if platform.system() == "Windows":
        try:
            import wmi

            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                name = getattr(gpu, "Name", "Unknown")
                ram = getattr(gpu, "AdapterRAM", 0)
                mem_mib = int(ram) // (1024**2) if ram else None
                gpus.append(
                    {
                        "vendor": getattr(gpu, "AdapterCompatibility", "Unknown"),
                        "model": name,
                        "memory_mib": mem_mib,
                    }
                )
            if gpus:
                return gpus
        except Exception:
            pass

    # macOS system_profiler
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType", "-json"], text=True
            )
            data = json.loads(out)
            displays = data.get("SPDisplaysDataType", [])
            for d in displays:
                name = d.get("sppci_model", d.get("_name", "Unknown"))
                vram = d.get("spdisplays_vram", None)  # e.g. "1536 MB"
                mem_mib = None
                if vram:
                    digits = "".join(ch for ch in vram if (ch.isdigit() or ch == "."))
                    try:
                        mem_mib = int(float(digits))
                    except:
                        mem_mib = None
                gpus.append(
                    {
                        "vendor": d.get("sppci_vendor", "Apple"),
                        "model": name,
                        "memory_mib": mem_mib,
                    }
                )
            if gpus:
                return gpus
        except Exception:
            pass

    # Linux lspci
    if platform.system() == "Linux":
        try:
            out = subprocess.check_output(["lspci", "-nnk"], text=True)
            lines = out.splitlines()
            for line in lines:
                if ("VGA compatible controller" in line) or ("3D controller" in line):
                    parts = line.split(":", 2)
                    model = parts[2].strip() if len(parts) >= 3 else line.strip()
                    gpus.append({"vendor": None, "model": model, "memory_mib": None})
            if gpus:
                return gpus
        except Exception:
            pass

    # fallback
    if not gpus:
        gpus.append({"vendor": None, "model": "Unknown GPU", "memory_mib": None})

    return gpus


# ========== helper: resource_path ==========
def resource_path(relative_path: str):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ================== إعداد الـ theme ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ================== الشبكة ==================
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    user = socket.gethostname()
    mac_address = get_mac_address()
    info = cpuinfo.get_cpu_info()
    ip = s.getsockname()[0]
    partitions = psutil.disk_partitions()
    gpus = get_gpus()

    gateway = "Unknown"
    gws = psutil.net_if_addrs()
    if gws:
        net_stats = psutil.net_if_stats()
        for iface, addrs in gws.items():
            if iface in net_stats and net_stats[iface].isup:
                gateway = ip.rsplit(".", 1)[0] + ".1"
                break
except OSError:
    print("please check your connection!")
    user = mac_address = gateway = ip = info = "Check your connection!"
    gpus = [{"model": "Unknown GPU", "memory_mib": None}]


# ================== Screenshot ==================
def screenshot_tk_window(window, output_filename="window_screenshot.png"):
    try:
        window.update_idletasks()
        x = window.winfo_rootx()
        y = window.winfo_rooty()
        w = window.winfo_width()
        h = window.winfo_height()

        if w <= 0 or h <= 0:
            print("Invalid window size for screenshot!")
            return

        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        screenshot.save(output_filename)

        if platform.system() == "Windows":
            os.startfile(output_filename)
        elif platform.system() == "Darwin":
            os.system(f"open {output_filename}")
        else:
            os.system(f"xdg-open {output_filename}")

        print(f"Screenshot saved as {output_filename}")
    except Exception as e:
        print(f"Error: {e}")


# ====== الصف 2: Disk ======
if platform.system() == "Windows":
    system_partition = os.environ["SystemDrive"] + "\\"
else:
    system_partition = "/"

usage = psutil.disk_usage(system_partition)


def format_gpu_model(raw_model: str) -> str:
    if not raw_model:
        return "Unknown GPU"

    model = raw_model

    # شيل "Intel Corporation"
    model = model.replace("Intel Corporation", "Intel")

    # شيل الأكواد بين [] والـ (rev ...)
    import re

    model = re.sub(r"\[.*?\]", "", model)  # يمسح [8086:5917]
    model = re.sub(r"\(rev.*?\)", "", model)  # يمسح (rev 07)

    # شيل المسافات الزايدة
    model = " ".join(model.split())

    return model


# ================== Create Report ==================
def create_file():
    output_filename = "report.txt"
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write("=============================================\n")
        file.write("         💻  SYSTEM INFORMATION REPORT 💻\n")
        file.write("=============================================\n\n")

        # Computer Info
        file.write(f"Computer Name : {user}\n")
        file.write(f"Processor      : {info['brand_raw']}\n")
        file.write(
            f"Memory         : {round(psutil.virtual_memory().total / (1024**3))} GB\n"
        )

        gpu_model = gpus[0].get("model", "Unknown")
        gpu_mem = gpus[0].get("memory_mib")
        gpu_mem_gb = (gpu_mem // 1024) if gpu_mem else "N/A"

        file.write(f"Graphics       : {gpu_model} ({gpu_mem_gb} GB)\n\n")

        # Disk Info
        file.write("----------- Storage -----------\n")
        file.write(f"Disk Capacity  : {usage.total // (1024**3)} GB\n")
        file.write(
            f"Used / Free    : {usage.used // (1024**3)} GB / {usage.free // (1024**3)} GB\n\n"
        )

        # Network Info
        file.write("----------- Network -----------\n")
        file.write(f"IP Address     : {ip}\n")
        file.write(f"Gateway        : {gateway}\n")
        file.write(f"MAC Address    : {mac_address}\n")

        file.write("\n=============================================\n")
        file.write("          📑 End of Report 📑\n")
        file.write("=============================================\n")

    print(f"Report saved as {output_filename}")

    if platform.system() == "Windows":
        os.startfile(output_filename)
    elif platform.system() == "Darwin":
        os.system(f"open '{output_filename}'")
    else:
        os.system(f"xdg-open '{output_filename}'")


# ================== UI ==================
win = ctk.CTk()
win.geometry("800x600")
win.title("Red Support IT")

# ====== Logo ======
try:
    logo_img = ctk.CTkImage(
        light_image=Image.open(resource_path("logo.png")), size=(300, 120)
    )
    logo_label = ctk.CTkLabel(win, image=logo_img, text="")
    logo_label.pack(pady=10)
except Exception as e:
    print("Logo error:", e)

# ====== الوقت ======
time_label = ctk.CTkLabel(win, font=ctk.CTkFont(size=18, weight="bold"))
time_label.pack(pady=10)


def upd_time():
    string = strftime("%I:%M:%S %p")
    time_label.configure(text=string)
    time_label.after(1000, upd_time)


# ====== بيانات الجهاز ======
info_frame = ctk.CTkFrame(win, corner_radius=10)
info_frame.pack(pady=20, padx=10, fill="x")

for i in range(2):
    info_frame.grid_columnconfigure(i, weight=1)


def add_info_grid(
    title,
    value,
    row,
    col,
    text_color="white",
    title_bg="gray20",
    value_bg="black",
    colspan=1,
):
    card = ctk.CTkFrame(
        info_frame,
        corner_radius=8,
        fg_color="gray15",
    )
    card.grid(row=row, column=col, padx=10, pady=5, sticky="ew", columnspan=colspan)

    card.grid_columnconfigure(1, weight=1)

    label_title = ctk.CTkLabel(
        card,
        text=title,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color=title_bg,
        corner_radius=6,
        padx=10,
        pady=5,
    )
    label_title.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    label_value = ctk.CTkLabel(
        card,
        text=value,
        font=ctk.CTkFont(size=14),
        text_color=text_color,
        fg_color=value_bg,
        corner_radius=6,
        padx=10,
        pady=5,
    )
    label_value.grid(row=0, column=1, sticky="ew", padx=5, pady=5)


# ====== الصف 0: Computer - Processor ======
add_info_grid("Computer:", user, 0, 0, "cyan")
add_info_grid("Processor:", info["brand_raw"], 0, 1, "cyan")

# ====== الصف 1: Memory - Graphics ======
add_info_grid(
    "Memory:", f"{round(psutil.virtual_memory().total / (1024**3))} GB RAM", 1, 0, "red"
)
print(gpus)
gpu_model_raw = gpus[0].get("model", "Unknown")
gpu_model = format_gpu_model(gpu_model_raw)

gpu_mem = gpus[0].get("memory_mib")

if gpu_mem and gpu_mem > 0:
    gpu_mem_str = f"{gpu_mem // 1024} GB"
else:
    # Intel / AMD iGPU غالباً بياخد من الرام
    total_ram_gb = round(psutil.virtual_memory().total / (1024**3))
    gpu_mem_str = f"Shared ({total_ram_gb} GB RAM)"


add_info_grid("Graphics:", f"{gpu_model} / {gpu_mem_str}", 1, 1, "orange")

# ====== الصف 2: Disk ======
add_info_grid("Disk:", f"{usage.total // (1024**3)} GB", 2, 0, "cyan")
add_info_grid(
    "Used/Free:",
    f"{usage.used // (1024**3)} GB / {usage.free // (1024**3)} GB",
    2,
    1,
    "yellow",
)

# ====== الصف 3: IP - Gateway ======
add_info_grid("IP Address:", ip, 3, 0, "orange")
add_info_grid("Gateway:", gateway, 3, 1, "yellow")

# ====== الصف 4: MAC Address ======
mac_card = ctk.CTkFrame(info_frame, corner_radius=10, fg_color="gray15")
mac_card.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

mac_label = ctk.CTkLabel(
    mac_card,
    text=f"MAC Address: {mac_address}",
    font=ctk.CTkFont(size=15, weight="bold"),
    text_color="lightgreen",
    fg_color="black",
    corner_radius=6,
    padx=10,
    pady=8,
)
mac_label.pack(padx=10, pady=10, expand=True)

# ====== Buttons ======
button_frame = ctk.CTkFrame(win, corner_radius=10)
button_frame.pack(pady=20)

btn1 = ctk.CTkButton(
    button_frame,
    text="📸 Screenshot",
    command=lambda: screenshot_tk_window(win, "reportScreenshot.png"),
    width=150,
)
btn1.pack(side="left", padx=10, pady=10)

btn2 = ctk.CTkButton(
    button_frame,
    text="📝 Create Report",
    command=create_file,
    width=150,
)
btn2.pack(side="left", padx=10, pady=10)

upd_time()
win.mainloop()
s.close()
