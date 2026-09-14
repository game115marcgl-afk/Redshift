# Kontroler Redshift GTK (Edycja Polska)

Graficzny panel kontrolny (GUI) w **Pythonie 3** i **GTK 3** do zarządzania narzędziem **Redshift** (filtr światła niebieskiego i regulacja temperatury barwowej ekranu).

Zaprojektowany ze szczególnym uwzględnieniem środowiska graficznego **Xfce w Linux Mint**, wyposażony w przejrzysty interfejs z podziałem na karty oraz listę współrzędnych 18 polskich miast wojewódzkich.

---

## 🌟 Główne Funkcje

* 🕒 **Karta Trybu Automatycznego:**
  * Wybór z listy 18 polskich miast lub wpisanie własnych współrzędnych geograficznych (LAT / LON).
  * Regulacja temperatury barwowej (K) oraz jasności osobno dla dnia i nocy za pomocą przycisków `+` / `-`.
* 🎛️ **Karta Kontroli Ręcznej & Profile:**
  * Szybkie presety jednym kliknięciem: *Dzień (6500K)*, *Noc (3500K)*, *Czytanie (2700K)*, *Pełne kolory*.
  * Suwaki do ręcznej korekty temperatury, ogólnej jasności oraz balansu składowych kolorów Gamma (RGB).
* ⚙️ **Karta Konfiguracji & Systemu:**
  * Zapisywanie i odczyt konfiguracji z pliku `~/.config/redshift/redshift.conf`.
  * Przełącznik autostartu (automatyczne uruchamianie filtra po zalogowaniu do systemu).
  * Automatyczna integracja z menu Whisker / aplikacjami w systemie (`.desktop`).
* 📊 **Monitor stanu na żywo:**
  * Stały pasek na dole okna informujący o działającym procesie Redshift, aktywnych parametrach oraz przycisk szybkiego wyłączenia filtra.

---

## 📦 Wymagania systemowe

Program wymaga systemu operacyjnego Linux z serwerem X11 (np. **Linux Mint Xfce**, Ubuntu, Debian) oraz zainstalowanych pakietów:

```bash
sudo apt update
sudo apt install redshift python3-gi gir1.2-gtk-3.0 procps
