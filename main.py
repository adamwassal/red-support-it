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
import pyopencl as cl


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
    gpus = []

    for plat in cl.get_platforms():
        for dev in plat.get_devices():
            infogpu = {
                "platform": plat.name,
                "vendor": dev.vendor,
                "model": dev.name,
                "driver": dev.driver_version,
                "global_mem_mib": dev.global_mem_size // (1024**2),
            }
            gpus.append(infogpu)

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


# # ====== الصف 2: Disk ======
if platform.system() == "Windows":
    system_partition = os.environ["SystemDrive"] + "\\"
else:
    system_partition = "/"

usage = psutil.disk_usage(system_partition)


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
        file.write(
            f"Graphics       : {gpus[0]['model']}  "
            f"({int(gpus[0]['global_mem_mib'] / 1024)} GB)\n\n"
        )

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

    # Open file depending on OS
    if platform.system() == "Windows":
        os.startfile(output_filename)
    elif platform.system() == "Darwin":
        os.system(f"open '{output_filename}'")
    else:
        os.system(f"xdg-open '{output_filename}'")


# add_info_grid("Processor:", info["brand_raw"], 0, 1, "cyan")

# add_info_grid(
#     "Memory:", f"{round(psutil.virtual_memory().total / (1024**3))} GB", 1, 0, "red"
# )
#     add_info_grid("Graphics:", f"{gpus[0]["model"]}  /  {int(gpus[0]['global_mem_mib'] / 1024)}GB", 1, 1, "orange")


# add_info_grid("Disk:", f"{usage.total // (1024**3)} GB", 2, 0, "cyan")
# add_info_grid(
#     "Used/Free:",
#     f"{usage.used // (1024**3)} GB / {usage.free // (1024**3)} GB",
#     2,
#     1,
#     "yellow",
# )

# add_info_grid("IP Address:", ip, 3, 0, "orange")
# add_info_grid("Gateway:", gateway, 3, 1, "yellow")

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
    # ====== Card frame ======
    card = ctk.CTkFrame(
        info_frame,
        corner_radius=8,
        fg_color="gray15",  # الخلفية العامة للبطاقة
    )
    card.grid(row=row, column=col, padx=10, pady=5, sticky="ew", columnspan=colspan)

    card.grid_columnconfigure(1, weight=1)  # يخلي القيمة تتمدد

    # ===== العنوان =====
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

    # ===== القيمة =====
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
    "Memory:", f"{round(psutil.virtual_memory().total / (1024**3))} GB", 1, 0, "red"
)
if gpus:
    add_info_grid(
        "Graphics:",
        f"{gpus[0]['model']}  /  {int(gpus[0]['global_mem_mib'] / 1024)}GB",
        1,
        1,
        "orange",
    )

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

# ====== الصف 4: MAC Address (وسط) ======
# ===== MAC Address Card =====
mac_card = ctk.CTkFrame(
    info_frame,
    corner_radius=10,
    fg_color="gray15",  # خلفية الكارد
)
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
mac_label.pack(padx=10, pady=10, expand=True)  # يحطه في النص


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
