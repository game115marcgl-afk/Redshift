#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  redshift_control.py - Kontroler Redshift GTK dla Polski (wersja z kartami)
#
#  Pierwotny autor: Copyright (C) 2025 Wasz Informatyk
#  Współautorzy / Rozwój: Społeczność Open Source (2025-2026)
#
#  Ten program jest wolnym oprogramowaniem; możesz go rozprowadzać dalej i/lub
#  modyfikować na warunkach Powszechnej Licencji Publicznej GNU, wydanej przez
#  Fundację Wolnego Oprogramowania; według wersji 3 tej Licencji lub (według
#  twojego wyboru) którejkolwiek późniejszej wersji.
#
#  Ten program rozpowszechniany jest z nadzieją, że będzie użyteczny – jednak
#  BEZ JAKIEJKOLWIEK GWARANCJI, nawet domyślnej gwarancji PRZYDATNOŚCI
#  HANDLOWEJ albo PRZYDATNOŚCI DO OKREŚLONYCH ZASTOSOWAŃ. W celu uzyskania
#  bliższych informacji sięgnij do Powszechnej Licencji Publicznej GNU.
#
#  Powinieneś otrzymać kopię Powszechnej Licencji Publicznej GNU wraz z tym
#  programem; jeśli nie – zobacz <https://www.gnu.org/licenses/>.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import re
import os
import sys
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
    """Obsługa procesów, plików konfiguracyjnych i integracji z systemem."""
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path

    def install_desktop_entry(self):
        """Tworzy wpis .desktop w ~/.local/share/applications dla menu Whisker / Xfce."""
        try:
            script_path = os.path.abspath(__file__)
            current_stat = os.stat(script_path)
            os.chmod(script_path, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            os.makedirs(DESKTOP_DIR, exist_ok=True)
            content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Kontroler Redshift
GenericName=Filtr światła niebieskiego
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

    def run_auto_from_config(self):
        config = self.load_config()
        if config and 'manual' in config:
            lat = config.get('manual', 'lat', fallback="52.23")
            lon = config.get('manual', 'lon', fallback="21.01")
            t_day = config.get('redshift', 'temp-day', fallback="6500")
            t_night = config.get('redshift', 'temp-night', fallback="4500")
            b_day = config.get('redshift', 'brightness-day', fallback="1.0")
            b_night = config.get('redshift', 'brightness-night', fallback="1.0")
        else:
            lat, lon = "52.23", "21.01"
            t_day, t_night = "6500", "4500"
            b_day, b_night = "1.0", "1.0"

        self.kill_redshift()
        cmd = ["redshift", "-l", f"{lat}:{lon}", "-t", f"{t_day}:{t_night}", "-b", f"{b_day}:{b_night}"]
        return self.run_redshift(cmd, background=True)

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
            self.combo_cities.append_text(city)
        self.combo_cities.set_active(0)
        self.combo_cities.connect("changed", self.on_city_changed)
        grid_loc.attach(self.combo_cities, 1, 0, 3, 1)

        grid_loc.attach(Gtk.Label(label="Szerokość (LAT):"), 0, 1, 1, 1)
        self.entry_lat = Gtk.Entry()
        grid_loc.attach(self.entry_lat, 1, 1, 3, 1)

        grid_loc.attach(Gtk.Label(label="Długość (LON):"), 0, 2, 1, 1)
        self.entry_lon = Gtk.Entry()
        grid_loc.attach(self.entry_lon, 1, 2, 3, 1)

        # Ramka parametrów dnia i nocy
        params_frame = Gtk.Frame(label=" Parametry przejścia Dzień / Noc ")
        vbox.pack_start(params_frame, False, True, 0)
        grid_params = Gtk.Grid(column_spacing=6, row_spacing=6)
        grid_params.set_border_width(8)
        params_frame.add(grid_params)

        self.entry_temp_day = self._create_adjustable_entry(grid_params, "Temp. dzień (K):", 0, "6500", -100, 100, False)
        self.entry_temp_night = self._create_adjustable_entry(grid_params, "Temp. noc (K):", 1, "4500", -100, 100, False)
        self.entry_bright_day = self._create_adjustable_entry(grid_params, "Jasność dzień:", 2, "1.0", -0.05, 0.05, True)
        self.entry_bright_night = self._create_adjustable_entry(grid_params, "Jasność noc:", 3, "1.0", -0.05, 0.05, True)

        btn_run_auto = Gtk.Button(label="▶ Uruchom tryb automatyczny")
        btn_run_auto.connect("clicked", self.on_set_location)
        vbox.pack_start(btn_run_auto, False, True, 4)

        return vbox

    def _create_manual_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(12)

        # Szybkie profile
        preset_frame = Gtk.Frame(label=" Szybkie Profile ")
        vbox.pack_start(preset_frame, False, True, 0)
        hbox_presets = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox_presets.set_border_width(8)
        preset_frame.add(hbox_presets)

        presets = [
            ("☀️ Dzień (6500K)", 6500, 1.0),
            ("🌙 Noc (3500K)", 3500, 0.85),
            ("📖 Czytanie (2700K)", 2700, 0.70),
            ("🎨 Pełne kolory", 6500, 1.0)
        ]
        for title, temp, bright in presets:
            btn = Gtk.Button(label=title)
            btn.connect("clicked", lambda w, t=temp, b=bright: self._apply_preset(t, b))
            hbox_presets.pack_start(btn, True, True, 0)

        # Suwaki regulacji
        sliders_frame = Gtk.Frame(label=" Regulacja Ręczna ")
        vbox.pack_start(sliders_frame, False, True, 0)
        grid_sliders = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid_sliders.set_border_width(8)
        sliders_frame.add(grid_sliders)

        self.scale_temp = self._create_scale(grid_sliders, "Temperatura (K):", 0, 6500, 1000, 9000, 100, 0)
        self.scale_bright = self._create_scale(grid_sliders, "Jasność:", 1, 1.0, 0.1, 1.0, 0.05, 2)
        self.scale_gamma_r = self._create_scale(grid_sliders, "Gamma R (Czerwony):", 2, 1.0, 0.1, 2.0, 0.01, 2)
        self.scale_gamma_g = self._create_scale(grid_sliders, "Gamma G (Zielony):", 3, 1.0, 0.1, 2.0, 0.01, 2)
        self.scale_gamma_b = self._create_scale(grid_sliders, "Gamma B (Niebieski):", 4, 1.0, 0.1, 2.0, 0.01, 2)

        btn_apply = Gtk.Button(label="✔ Zastosuj ustawienia suwaków")
        btn_apply.connect("clicked", self.on_apply_manual)
        vbox.pack_start(btn_apply, False, True, 0)

        return vbox

    def _create_config_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(12)

        file_frame = Gtk.Frame(label=" Plik Konfiguracyjny ")
        vbox.pack_start(file_frame, False, True, 0)
        vbox_file = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox_file.set_border_width(8)
        file_frame.add(vbox_file)

        lbl_path = Gtk.Label(label=f"Ścieżka: <tt>{CONFIG_PATH}</tt>", use_markup=True)
        lbl_path.set_xalign(0)
        vbox_file.pack_start(lbl_path, False, True, 0)

        hbox_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_save = Gtk.Button(label="💾 Zapisz bieżące ustawienia")
        btn_save.connect("clicked", self.on_save_config_clicked)
        btn_reload = Gtk.Button(label="🔄 Wczytaj z pliku")
        btn_reload.connect("clicked", lambda w: self.load_config_on_startup(show_dialog=True))
        hbox_btns.pack_start(btn_save, True, True, 0)
        hbox_btns.pack_start(btn_reload, True, True, 0)
        vbox_file.pack_start(hbox_btns, False, True, 0)

        sys_frame = Gtk.Frame(label=" Opcje Systemowe i Autostart ")
        vbox.pack_start(sys_frame, False, True, 0)
        vbox_sys = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox_sys.set_border_width(8)
        sys_frame.add(vbox_sys)

        self.check_autostart = Gtk.CheckButton(label="Uruchamiaj Redshift automatycznie przy logowaniu do systemu")
        self.check_autostart.set_active(self.logic.is_autostart_enabled())
        self.check_autostart.connect("toggled", self.on_autostart_toggled)
        vbox_sys.pack_start(self.check_autostart, False, True, 0)

        btn_desktop = Gtk.Button(label="📌 Zaktualizuj skrót w menu Whisker (Mint)")
        btn_desktop.connect("clicked", self.on_install_desktop_clicked)
        vbox_sys.pack_start(btn_desktop, False, True, 0)

        return vbox

    def _create_bottom_status_bar(self, parent_box):
        frame = Gtk.Frame(label=" Status ")
        parent_box.pack_start(frame, False, True, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(8)
        frame.add(vbox)

        self.status_label = Gtk.Label(label="Sprawdzanie statusu...")
        self.status_label.set_xalign(0.5)
        vbox.pack_start(self.status_label, False, True, 0)

        btn_reset = Gtk.Button(label="⛔ Wyłącz filtr / Resetuj kolory")
        btn_reset.get_style_context().add_class("destructive-action")
        btn_reset.connect("clicked", self.on_reset)
        vbox.pack_start(btn_reset, False, True, 0)

    def _create_adjustable_entry(self, grid, label, row, default_text, step_minus, step_plus, is_float):
        entry = Gtk.Entry()
        entry.set_text(default_text)
        btn_m = Gtk.Button(label="-")
        btn_p = Gtk.Button(label="+")
        btn_m.connect("clicked", lambda w: self._on_adjust_button_clicked(entry, step_minus, is_float))
        btn_p.connect("clicked", lambda w: self._on_adjust_button_clicked(entry, step_plus, is_float))
        grid.attach(Gtk.Label(label=label), 0, row, 1, 1)
        grid.attach(entry, 1, row, 1, 1)
        grid.attach(btn_m, 2, row, 1, 1)
        grid.attach(btn_p, 3, row, 1, 1)
        return entry

    def _create_scale(self, grid, label, row, value, lower, upper, step, digits):
        adj = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=step, page_increment=step*2, page_size=0)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.set_digits(digits)
        scale.set_hexpand(True)
        grid.attach(Gtk.Label(label=label), 0, row, 1, 1)
        grid.attach(scale, 1, row, 1, 1)
        return scale

    def _on_adjust_button_clicked(self, entry_widget, step, is_float=False):
        try:
            val = float(entry_widget.get_text()) if is_float else int(entry_widget.get_text())
            new_val = val + step
            if is_float:
                entry_widget.set_text(f"{max(0.1, min(1.0, new_val)):.2f}")
            else:
                entry_widget.set_text(str(max(1000, min(25000, new_val))))
        except ValueError:
            entry_widget.set_text("1.0" if is_float else "6500")

    def _apply_preset(self, temp, bright):
        self.scale_temp.set_value(temp)
        self.scale_bright.set_value(bright)
        self.scale_gamma_r.set_value(1.0)
        self.scale_gamma_g.set_value(1.0)
        self.scale_gamma_b.set_value(1.0)
        self.on_apply_manual(None)

    def load_config_on_startup(self, show_dialog=False):
        config = self.logic.load_config()
        if not config:
            if show_dialog:
                self.show_error_dialog("Nie znaleziono pliku konfiguracyjnego.")
            return
        if 'redshift' in config:
            self.entry_temp_day.set_text(config.get('redshift', 'temp-day', fallback='6500'))
            self.entry_temp_night.set_text(config.get('redshift', 'temp-night', fallback='4500'))
            self.entry_bright_day.set_text(config.get('redshift', 'brightness-day', fallback='1.0'))
            self.entry_bright_night.set_text(config.get('redshift', 'brightness-night', fallback='1.0'))
            gamma_str = config.get('redshift', 'gamma', fallback='1.0:1.0:1.0')
            try:
                r, g, b = map(float, gamma_str.split(':'))
                self.scale_gamma_r.set_value(r)
                self.scale_gamma_g.set_value(g)
                self.scale_gamma_b.set_value(b)
            except Exception:
                pass
        if 'manual' in config:
            self.entry_lat.set_text(config.get('manual', 'lat', fallback=''))
            self.entry_lon.set_text(config.get('manual', 'lon', fallback=''))

        if show_dialog:
            self.show_info_dialog("Sukces", "Pomyślnie załadowano ustawienia z pliku konfiguracyjnego.")

    def on_save_config_clicked(self, widget):
        redshift_data = {
            'temp-day': self.entry_temp_day.get_text(),
            'temp-night': self.entry_temp_night.get_text(),
            'brightness-day': self.entry_bright_day.get_text(),
            'brightness-night': self.entry_bright_night.get_text(),
            'gamma': f'{self.scale_gamma_r.get_value():.2f}:{self.scale_gamma_g.get_value():.2f}:{self.scale_gamma_b.get_value():.2f}',
            'location-provider': 'manual',
            'adjustment-method': 'randr'
        }
        manual_data = {
            'lat': self.entry_lat.get_text(),
            'lon': self.entry_lon.get_text()
        }
        success, error = self.logic.save_config(redshift_data, manual_data)
        if success:
            self.show_info_dialog("Zapisano!", f"Konfiguracja zapisana w:\n{CONFIG_PATH}")
        else:
            self.show_error_dialog(f"Błąd zapisu pliku: {error}")

    def on_apply_manual(self, widget):
        self.logic.kill_redshift()
        temp = int(self.scale_temp.get_value())
        bright = round(self.scale_bright.get_value(), 2)
        gamma_str = f"{self.scale_gamma_r.get_value():.2f}:{self.scale_gamma_g.get_value():.2f}:{self.scale_gamma_b.get_value():.2f}"

        command = ["redshift", "-P", "-O", str(temp), "-b", str(bright), "-g", gamma_str]
        GLib.timeout_add(150, lambda: self._exec_manual(command, temp, bright, gamma_str))

    def _exec_manual(self, cmd, temp, bright, gamma_str):
        ok, err = self.logic.run_redshift(cmd)
        if ok:
            self.status_label.set_markup(f"<b>Tryb ręczny aktywny:</b> {temp}K | Jasność: {bright} | Gamma: {gamma_str}")
        else:
            self.show_error_dialog(f"Błąd uruchamiania redshift: {err}")
        return False

    def on_set_location(self, widget):
        values = [
            self.entry_lat.get_text().strip(), self.entry_lon.get_text().strip(),
            self.entry_temp_day.get_text().strip(), self.entry_temp_night.get_text().strip(),
            self.entry_bright_day.get_text().strip(), self.entry_bright_night.get_text().strip()
        ]
        if not all(values):
            self.show_error_dialog("Wszystkie pola trybu auto muszą być uzupełnione.")
            return
        lat, lon, t_day, t_night, b_day, b_night = values

        self.logic.kill_redshift()
        cmd = ["redshift", "-l", f"{lat}:{lon}", "-t", f"{t_day}:{t_night}", "-b", f"{b_day}:{b_night}"]
        self.logic.run_redshift(cmd, background=True)
        GLib.timeout_add(300, self.check_and_update_status)

    def on_reset(self, widget):
        self.logic.kill_redshift()
        self.logic.run_redshift(["redshift", "-x"])
        self.scale_temp.set_value(6500)
        self.scale_bright.set_value(1.0)
        self.scale_gamma_r.set_value(1.0)
        self.scale_gamma_g.set_value(1.0)
        self.scale_gamma_b.set_value(1.0)
        GLib.timeout_add(200, self.check_and_update_status)

    def check_and_update_status(self):
        try:
            result = subprocess.run(["pgrep", "-a", "-x", "redshift"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().splitlines()
                cmd_line = lines[0]
                pid = cmd_line.split()[0]
                loc_match = re.search(r'-l\s+([\d.-]+):([\d.-]+)', cmd_line)
                temp_match = re.search(r'-t\s+(\d+):(\d+)', cmd_line)
                bright_match = re.search(r'-b\s+([\d.]+):([\d.]+)', cmd_line)
                if loc_match and temp_match and bright_match:
                    lat, lon = loc_match.groups()
                    t_day, t_night = temp_match.groups()
                    b_day, b_night = bright_match.groups()
                    self.status_label.set_markup(
                        f"<b>Tryb Auto (PID: {pid})</b> | Poz: {lat}, {lon} | Temp: {t_day}K/{t_night}K | Jasność: {b_day}/{b_night}"
                    )
                else:
                    self.status_label.set_markup(f"<b>Redshift aktywny (PID: {pid})</b>: <tt>{cmd_line}</tt>")
            else:
                self.status_label.set_text("Redshift nie jest uruchomiony.")
        except Exception as e:
            self.status_label.set_text(f"Błąd sprawdzania statusu: {e}")
        return True

    def on_city_changed(self, widget):
        coords = self.cities_data.get(widget.get_active_text())
        if coords:
            self.entry_lat.set_text(coords[0])
            self.entry_lon.set_text(coords[1])

    def on_autostart_toggled(self, widget):
        self.logic.toggle_autostart(widget.get_active())

    def on_install_desktop_clicked(self, widget):
        ok, res = self.logic.install_desktop_entry()
        if ok:
            self.show_info_dialog("Skrót gotowy", f"Zaktualizowano skrót w menu:\n{res}")
        else:
            self.show_error_dialog(f"Nie udało się zaktualizować skrótu:\n{res}")

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text="Błąd"
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto-start":
        logic = RedshiftLogic()
        logic.run_auto_from_config()
        sys.exit(0)

    RedshiftLogic().kill_redshift_gtk()
    win = RedshiftController()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
