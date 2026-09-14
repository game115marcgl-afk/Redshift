#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  redshift_control.py - Kontroler Redshift GTK z podziałem na karty
#  Dedykowany dla Linux Mint (Xfce)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import re
import os
import stat
import configparser

POLISH_CITIES = {
    "Białystok": ("53.13", "23.16"), "Bydgoszcz": ("53.12", "18.00"),
    "Gdańsk": ("54.35", "18.64"), "Gorzów Wielkopolski": ("52.73", "15.24"),
    "Katowice": ("50.26", "19.02"), "Kielce": ("50.87", "20.62"),
    "Kraków": ("50.06", "19.94"), "Lublin": ("51.24", "22.56"),
    "Łódź": ("51.76", "19.45"), "Olsztyn": ("53.77", "20.49"),
    "Opole": ("50.67", "17.92"), "Poznań": ("52.40", "16.92"),
    "Rzeszów": ("50.04", "21.99"), "Szczecin": ("53.42", "14.55"),
    "Toruń": ("53.01", "18.61"), "Warszawa": ("52.23", "21.01"),
    "Wrocław": ("51.10", "17.03"), "Zielona Góra": ("51.93", "15.50")
}

CONFIG_PATH = os.path.expanduser("~/.config/redshift/redshift.conf")
DESKTOP_DIR = os.path.expanduser("~/.local/share/applications")
DESKTOP_FILE_PATH = os.path.join(DESKTOP_DIR, "redshift-control.desktop")
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE_PATH = os.path.join(AUTOSTART_DIR, "redshift-control-autostart.desktop")


class RedshiftLogic:
    """Obsługa procesów, plików konfiguracyjnych i systemu."""
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path

    def install_desktop_entry(self):
        """Tworzy wpis .desktop w ~/.local/share/applications dla menu Minta."""
        try:
            script_path = os.path.abspath(__file__)
            current_stat = os.stat(script_path)
            os.chmod(script_path, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            os.makedirs(DESKTOP_DIR, exist_ok=True)
            content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Kontroler Redshift
Comment=Sterowanie temperaturą barwową ekranu
Exec=python3 "{script_path}"
Icon=redshift
Terminal=false
Categories=Settings;HardwareSettings;Utility;
Keywords=redshift;ekran;temperatura;noc;światło;filtr;
StartupNotify=true
"""
            with open(DESKTOP_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            return True, DESKTOP_FILE_PATH
        except Exception as e:
            return False, str(e)

    def is_autostart_enabled(self):
        return os.path.exists(AUTOSTART_FILE_PATH)

    def toggle_autostart(self, enable):
        try:
            if enable:
                os.makedirs(AUTOSTART_DIR, exist_ok=True)
                script_path = os.path.abspath(__file__)
                content = f"""[Desktop Entry]
Type=Application
Name=Redshift Kontroler Autostart
Exec=python3 "{script_path}" --auto-start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                with open(AUTOSTART_FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                if os.path.exists(AUTOSTART_FILE_PATH):
                    os.remove(AUTOSTART_FILE_PATH)
            return True
        except Exception as e:
            print(f"Błąd autostartu: {e}")
            return False

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config.read_file(f)
            return config
        except Exception as e:
            print(f"Błąd odczytu konfiguracji: {e}")
            return None

    def save_config(self, redshift_data, manual_data):
        config = configparser.ConfigParser()
        config['redshift'] = redshift_data
        config['manual'] = manual_data
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                configfile.write("; Konfiguracja wygenerowana przez Kontroler Redshift\n")
                config.write(configfile)
            return True, None
        except OSError as e:
            return False, str(e)

    def run_redshift(self, cmd, background=False):
        try:
            if background:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, None
        except Exception as e:
            return False, str(e)

    def kill_redshift(self):
        try:
            subprocess.run(["pkill", "-x", "redshift"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def kill_redshift_gtk(self):
        try:
            subprocess.run(["pkill", "-x", "redshift-gtk"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    @staticmethod
    def validate_float(value, min_val, max_val):
        try:
            val = float(value)
            return min_val <= val <= max_val
        except ValueError:
            return False

    @staticmethod
    def validate_int(value, min_val, max_val):
        try:
            val = int(value)
            return min_val <= val <= max_val
        except ValueError:
            return False


class RedshiftController(Gtk.Window):
    def __init__(self):
        super().__init__(title="Kontroler Redshift")
        self.set_border_width(12)
        self.set_default_size(500, 540)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.cities_data = POLISH_CITIES
        self.logic = RedshiftLogic()

        # Rejestracja w menu przy pierwszym uruchomieniu
        self.logic.install_desktop_entry()

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_vbox)

        # Kontener zakładek (Notebook)
        notebook = Gtk.Notebook()
        main_vbox.pack_start(notebook, True, True, 0)

        # Tworzenie poszczególnych kart
        notebook.append_page(self._create_auto_tab(), Gtk.Label(label=" 🕒 Tryb Auto "))
        notebook.append_page(self._create_manual_tab(), Gtk.Label(label=" 🎛️ Kontrola Ręczna "))
        notebook.append_page(self._create_config_tab(), Gtk.Label(label=" ⚙️ Konfiguracja "))

        # Wspólny dolny panel statusu i resetu
        self._create_bottom_status_bar(main_vbox)

        self.load_config_on_startup()
        self.check_and_update_status()

        # Sprawdzanie stanu w pętli co 2s
        GLib.timeout_add_seconds(2, self.check_and_update_status)

    # -------------------------------------------------------------
    # KARTA 1: TRYB AUTOMATYCZNY
    # -------------------------------------------------------------
    def _create_auto_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(12)

        # Ramka lokalizacji
        loc_frame = Gtk.Frame(label=" Lokalizacja ")
        vbox.pack_start(loc_frame, False, True, 0)
        grid_loc = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid_loc.set_border_width(8)
        loc_frame.add(grid_loc)

        grid_loc.attach(Gtk.Label(label="Miasto (Polska):"), 0, 0, 1, 1)
        self.combo_cities = Gtk.ComboBoxText()
        self.combo_cities.append_text("Wybierz z listy...")
        for city in sorted(self.cities_data.keys()):
            self.combo_cities.append_te
