# Linux Performance Switcher

A simple Python GUI application for Linux systems with NVIDIA GPUs to easily switch between performance profiles and monitor core sensors in real-time.

This tool is designed for gamers, AI/ML developers, and power users who need to quickly toggle between a power-saving state and a maximum-performance state without complex terminal commands.



---

## Features

* **Simple 3-Button GUI:** No complex commands needed.
* **Live Sensor Monitoring:** Real-time display of GPU/CPU temperature, GPU power draw, and the current CPU governor.
* **Three Performance Profiles:**
    * **AI Mode:** Sets CPU and GPU to maximum performance for compute-heavy tasks.
    * **Desktop Mode:** Sets the CPU to "performance" for a snappy UI, while leaving the GPU in its normal adaptive mode.
    * **Power-Save Mode:** Returns the system to a power-saving state.
* **Automatic GPU Power Detection:** Automatically finds your GPU's maximum power limit for optimal performance in AI Mode.
* **Secure:** Uses `pkexec` to graphically request root permissions only when a button is pressed, ensuring commands are run safely.

---

## How It Works (The Modes Explained)

This application gives you control over your system's performance with three distinct modes:

### 1. AI Mode On

This is the **maximum performance** setting.

* **CPU:** Sets the CPU governor to `performance`. This tells the CPU to run at its highest possible frequency, minimizing processing latency.
* **GPU:** Sets the NVIDIA GPU's "PowerMizer" mode to `Prefer Maximum Performance`. It also unlocks the GPU's power limit to the maximum wattage it supports. This is ideal for tasks like gaming, video rendering, or running local AI models.

### 2. Desktop Mode On

This mode is optimized for a **fast and responsive user interface**.

* **CPU:** Sets the CPU governor to `performance` for a snappy desktop experience.
* **GPU:** Sets the NVIDIA GPU's "PowerMizer" mode to `Adaptive`. The GPU will only ramp up its clock speeds when a 3D application is running, saving power and reducing heat during normal desktop use.

### 3. Power-Save Mode On

This is the **default, battery-friendly** mode.

* **CPU:** Sets the CPU governor to `powersave` (or lets the default system manager take over), which allows the CPU to use lower clock speeds to conserve energy.
* **GPU:** Sets the NVIDIA GPU's "PowerMizer" mode to `Adaptive`, same as in Desktop Mode.

---

## Installation

### Dependencies

Before running, you need to ensure a few common system tools are installed.

* **Python 3 & Tkinter:**
    * **Arch / EndeavourOS:** `sudo pacman -S python tk`
    * **Debian / Ubuntu / Mint:** `sudo apt update && sudo apt install python3 python3-tk`
    * **Fedora:** `sudo dnf install python3 tkinter`

* **NVIDIA Drivers & Tools:** You must have the proprietary NVIDIA drivers installed. `nvidia-smi` and `nvidia-settings` are included with the standard driver package.

* **CPU Power Utility (`cpupower`)**:
    * **Arch / EndeavourOS:** `sudo pacman -S linux-tools`
    * **Debian / Ubuntu / Mint:** `sudo apt install linux-tools-common linux-tools-generic`
    * **Fedora:** `sudo dnf install kernel-tools`

* **Polkit / `pkexec`:** This is included by default on virtually all modern desktop environments (KDE, GNOME, XFCE, etc.). If you are using a minimal window manager, you may need to install a polkit agent (e.g., `polkit-kde-agent`).

### Instructions

1.  Clone this repository:
    ```bash
    git clone [https://github.com/mohaaw/Linux_Performance_Switcher.git](https://github.com/mohaaw/Linux_Performance_Switcher.git)
    cd Linux_Performance_Switcher
    ```

2.  Make the script executable:
    ```bash
    chmod +x linux_performance_switcher.py
    ```

3.  Run the application:
    ```bash
    ./linux_performance_switcher.py
    ```
    **Important:** Do **not** run the script with `sudo`. It is designed to ask for your password with a graphical pop-up when you click a button.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/mohaaw/Linux_Performance_Switcher/blob/main/LICENSE) file for details.
