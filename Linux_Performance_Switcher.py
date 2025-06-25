#!/usr/bin/env python3

import tkinter as tk
from tkinter import font, messagebox
import subprocess
import re
import os
import shutil
from pathlib import Path

# --- Configuration & Styling ---
APP_TITLE = "Linux Performance Switcher"
WINDOW_GEOMETRY = "420x480"
BG_COLOR = "#2e3440"
FG_COLOR = "#d8dee9"
BTN_BG_COLOR = "#4c566a"
BTN_FG_COLOR = "#eceff4"
BTN_ACTIVE_BG = "#5e81ac"
QUIT_BTN_BG = "#bf616a"
SUCCESS_COLOR = "#a3be8c"
ERROR_COLOR = "#bf616a"
WARN_COLOR = "#ebcb8b"
INFO_COLOR = "#88c0d0"
SENSOR_LABEL_COLOR = "#e5e9f0"

class PerformanceSwitcherApp(tk.Tk):
    """
    A simple Tkinter GUI to switch between system performance modes and monitor sensors.
    Designed for NVIDIA Optimus laptops.
    """
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        self.title_font = font.Font(family="Cantarell", size=16, weight="bold")
        self.info_font = font.Font(family="Cantarell", size=11, weight="bold")
        self.button_font = font.Font(family="Cantarell", size=12)
        self.status_font = font.Font(family="Cantarell", size=10)
        
        self.max_power_limit = None
        self.cpu_temp_path = self._find_cpu_temp_path()

        if not self.check_dependencies():
            self.destroy()
            return
            
        self._create_widgets()
        self.display_power_limit()
        self.update_sensor_readings()

    def check_dependencies(self):
        """Checks if required command-line tools are installed."""
        dependencies = ['pkexec', 'nvidia-smi', 'nvidia-settings', 'cpupower']
        missing = [dep for dep in dependencies if shutil.which(dep) is None]

        if missing:
            error_msg = (f"Missing required dependencies:\n\n{', '.join(missing)}\n\n"
                         "Please install them and try again.\nSee the project's README for installation instructions.")
            messagebox.showerror("Dependency Error", error_msg)
            return False
        return True

    def _run_command_block(self, command_block_str):
        """Executes a string of shell commands as a single block using pkexec."""
        try:
            display = os.environ.get('DISPLAY')
            xauthority = os.environ.get('XAUTHORITY')
            if not display:
                self.update_status("Error: DISPLAY environment variable not found.", is_error=True)
                return None
            
            final_shell_cmd = f"export DISPLAY={display}; "
            if xauthority and os.path.exists(xauthority):
                final_shell_cmd += f"export XAUTHORITY={xauthority}; "
            
            final_shell_cmd += command_block_str
            full_command = ['pkexec', 'sh', '-c', final_shell_cmd]
            subprocess.run(full_command, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            self.update_status(f"Command block failed.\nError: {e.stderr.strip()}", is_error=True)
            print(f"Command block failed.\nError: {e.stderr.strip()}")
            return None
        except FileNotFoundError:
            self.update_status("Error: 'pkexec' not found. Please ensure Polkit is running.", is_error=True)
            return None

    def _get_max_power_limit(self):
        """Queries nvidia-smi to find the GPU's maximum supported power limit."""
        if self.max_power_limit is not None:
            return self.max_power_limit
        try:
            result = subprocess.run(['nvidia-smi', '-q', '-d', 'POWER'], capture_output=True, text=True, check=True)
            match = re.search(r"Max Power Limit\s+:\s+([\d\.]+) W", result.stdout)
            if match:
                self.max_power_limit = int(float(match.group(1)))
                return self.max_power_limit
            return None
        except (Exception):
            return None
            
    def display_power_limit(self):
        """Gets the power limit and updates the info label."""
        limit = self._get_max_power_limit()
        if limit:
            self.power_info_label.config(text=f"Max GPU Power Limit: {limit}W")
        else:
            self.power_info_label.config(text="Max GPU Power: Not Found", fg=WARN_COLOR)
            
    def _find_cpu_temp_path(self):
        """Finds the correct file to read the CPU temperature using a multi-stage search."""
        base_hwmon_path = Path('/sys/class/hwmon')
        if not base_hwmon_path.exists():
            print("Warning: /sys/class/hwmon directory not found.")
            return None
        
        # Stage 1: Search for known CPU thermal drivers
        try:
            for sensor_dir in base_hwmon_path.glob('hwmon*'):
                name_file = sensor_dir / 'name'
                if name_file.exists() and name_file.read_text().strip() in ['coretemp', 'k10temp']:
                    for temp_input in sorted(sensor_dir.glob('temp*_input')):
                        print(f"Found CPU temp file via driver name: {temp_input}")
                        return temp_input
        except Exception as e:
            print(f"Error during primary CPU temp search: {e}")

        # Stage 2: Fallback search for any plausible temperature sensor not belonging to nvidia
        try:
            for temp_input in base_hwmon_path.rglob('temp*_input'):
                name_file = temp_input.parent / 'name'
                if name_file.exists():
                    if 'nvidia' in name_file.read_text().strip():
                        continue # Skip nvidia sensors
                # Check if it gives a sane reading to qualify as a CPU temp
                try:
                    temp_val = int(temp_input.read_text().strip()) / 1000
                    if 10 < temp_val < 120: # Plausibility check
                        print(f"Found plausible CPU temp file via fallback: {temp_input}")
                        return temp_input
                except (ValueError, IOError):
                    continue # Not a valid integer file, skip
        except Exception as e:
            print(f"Error during fallback CPU temp search: {e}")
            
        print("Warning: Could not find a valid CPU temperature sensor file.")
        return None

    def _get_gpu_stats(self):
        """Gets GPU temperature and power draw from nvidia-smi."""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu,power.draw', '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True)
            temp, power = result.stdout.strip().split(',')
            return f"{temp.strip()}°C", f"{power.strip()}W"
        except (Exception):
            return "N/A", "N/A"

    def _get_cpu_temp(self):
        """Reads CPU temperature from the system file."""
        if self.cpu_temp_path:
            try:
                temp_str = self.cpu_temp_path.read_text().strip()
                return f"{int(temp_str) / 1000:.1f}°C"
            except (Exception):
                return "N/A"
        return "N/A"

    def _get_cpu_governor(self):
        """Reads the current CPU governor."""
        try:
            return Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor').read_text().strip()
        except (Exception):
            return "N/A"

    def update_sensor_readings(self):
        """Updates all sensor labels and schedules the next update."""
        gpu_temp, gpu_power = self._get_gpu_stats()
        cpu_temp = self._get_cpu_temp()
        cpu_gov = self._get_cpu_governor()

        self.gpu_temp_value.config(text=gpu_temp)
        self.gpu_power_value.config(text=gpu_power)
        self.cpu_temp_value.config(text=cpu_temp)
        self.cpu_gov_value.config(text=cpu_gov)
        
        self.after(2000, self.update_sensor_readings)

    def set_ai_mode(self):
        self.update_status("Setting AI Mode...", is_error=False, color=FG_COLOR)
        if self.max_power_limit is None:
             self.update_status("Error: Max Power Limit not found.", is_error=True)
             return
        command_block = (f"cpupower frequency-set -g performance && nvidia-smi -pm 1 && nvidia-smi -pl {self.max_power_limit} && nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=1'")
        if self._run_command_block(command_block):
            self.update_status("✅ AI Performance Mode is ON.", is_error=False)

    def set_desktop_mode(self):
        self.update_status("Setting Responsive Desktop Mode...", is_error=False, color=FG_COLOR)
        command_block = ("cpupower frequency-set -g performance && nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=2' && nvidia-smi -pm 0")
        if self._run_command_block(command_block):
            self.update_status("✅ Responsive Desktop Mode is ON.", is_error=False)

    def set_powersave_mode(self):
        self.update_status("Setting Power-Save Mode...", is_error=False, color=FG_COLOR)
        command_block = ("cpupower frequency-set -g powersave && nvidia-smi -pm 0 && nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=2'")
        if self._run_command_block(command_block):
            self.update_status("✅ Power-Save Mode is ON.", is_error=False)

    def update_status(self, text, is_error=False, color=None):
        self.status_label.config(text=text, fg=color if color else (ERROR_COLOR if is_error else SUCCESS_COLOR))
        self.update_idletasks()

    def _create_widgets(self):
        title_label = tk.Label(self, text=APP_TITLE, font=self.title_font, bg=BG_COLOR, fg=FG_COLOR)
        title_label.pack(pady=(15, 5))
        
        self.power_info_label = tk.Label(self, text="Detecting GPU Info...", font=self.info_font, bg=BG_COLOR, fg=INFO_COLOR)
        self.power_info_label.pack(pady=(0, 15))

        sensor_frame = tk.Frame(self, bg=BG_COLOR)
        sensor_frame.pack(pady=10, padx=10)
        for i in range(4): sensor_frame.grid_columnconfigure(i, weight=1)

        tk.Label(sensor_frame, text="GPU Temp:", font=self.info_font, bg=BG_COLOR, fg=SENSOR_LABEL_COLOR).grid(row=0, column=0, sticky='w', padx=5)
        self.gpu_temp_value = tk.Label(sensor_frame, text="--", font=self.info_font, bg=BG_COLOR, fg=INFO_COLOR)
        self.gpu_temp_value.grid(row=0, column=1, sticky='w')
        tk.Label(sensor_frame, text="GPU Power:", font=self.info_font, bg=BG_COLOR, fg=SENSOR_LABEL_COLOR).grid(row=1, column=0, sticky='w', padx=5)
        self.gpu_power_value = tk.Label(sensor_frame, text="--", font=self.info_font, bg=BG_COLOR, fg=INFO_COLOR)
        self.gpu_power_value.grid(row=1, column=1, sticky='w')

        tk.Label(sensor_frame, text="CPU Temp:", font=self.info_font, bg=BG_COLOR, fg=SENSOR_LABEL_COLOR).grid(row=0, column=2, sticky='w', padx=5)
        self.cpu_temp_value = tk.Label(sensor_frame, text="--", font=self.info_font, bg=BG_COLOR, fg=INFO_COLOR)
        self.cpu_temp_value.grid(row=0, column=3, sticky='w')
        tk.Label(sensor_frame, text="CPU Governor:", font=self.info_font, bg=BG_COLOR, fg=SENSOR_LABEL_COLOR).grid(row=1, column=2, sticky='w', padx=5)
        self.cpu_gov_value = tk.Label(sensor_frame, text="--", font=self.info_font, bg=BG_COLOR, fg=INFO_COLOR)
        self.cpu_gov_value.grid(row=1, column=3, sticky='w')

        button_frame = tk.Frame(self, bg=BG_COLOR)
        button_frame.pack(pady=10, padx=20, fill='x')

        ai_button = tk.Button(button_frame, text="AI Mode On", font=self.button_font, bg=BTN_BG_COLOR, fg=BTN_FG_COLOR, activebackground=BTN_ACTIVE_BG, command=self.set_ai_mode)
        ai_button.pack(pady=5, fill='x')
        desktop_button = tk.Button(button_frame, text="Desktop Mode On", font=self.button_font, bg=BTN_BG_COLOR, fg=BTN_FG_COLOR, activebackground=BTN_ACTIVE_BG, command=self.set_desktop_mode)
        desktop_button.pack(pady=5, fill='x')
        powersave_button = tk.Button(button_frame, text="Power-Save Mode On", font=self.button_font, bg=BTN_BG_COLOR, fg=BTN_FG_COLOR, activebackground=BTN_ACTIVE_BG, command=self.set_powersave_mode)
        powersave_button.pack(pady=5, fill='x')

        self.status_label = tk.Label(self, text="Select a mode to begin", font=self.status_font, bg=BG_COLOR, fg=FG_COLOR, wraplength=380)
        self.status_label.pack(pady=10)
        
        quit_button = tk.Button(self, text="Quit", font=self.button_font, bg=QUIT_BTN_BG, fg=BTN_FG_COLOR, activebackground=ERROR_COLOR, command=self.destroy)
        quit_button.pack(pady=(0, 15), padx=20, fill='x')

if __name__ == "__main__":
    if os.geteuid() == 0:
        messagebox.showerror("Error", "Please do not run this script with sudo.\nIt will ask for root permissions graphically when needed.")
        exit(1)
        
    app = PerformanceSwitcherApp()
    app.mainloop()

