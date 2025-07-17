"""
Gestor de serveis de llicències Autodesk (via NSSM) i McNeel Zoo 8
Amb suport de configuració externa mitjançant fitxer INI.

Aquest fitxer substitueix les constants codificades per valors llegits de
un "config.ini" situat al mateix directori que l'script (per defecte), o bé
passat via paràmetre `--config <ruta>`.

Si el fitxer de configuració no existeix, es crearà automàticament un fitxer
mínim amb valors per defecte (vegeu DEFAULT_CONFIG_INI més avall) i es mostrarà
un avís.

=======================================
 ESTRUCTURA DEL CONFIG.INI (exemple)
=======================================

[Autodesk]
# Nom del servei Windows que gestiona NSSM (lmgrd.exe)
service_name = AutodeskLicenseServer
# Nom dels processos que s'han de considerar "Autodesk FlexLM"
process_names = lmgrd.exe, adskflex.exe
# Directori de treball on resideixen els binaris / fitxer .lic
working_dir = C:\\Autodesk
# Ruta completa a l'executable lmgrd.exe (informatiu; no necessari per sc)
lmgrd_path = C:\\Autodesk\\lmgrd.exe
# Ruta completa al fitxer de llicència
license_file = C:\\Autodesk\\SERVER1-AULES00155d06fb06-2024.lic
# Ruta del log escrit per lmgrd/adskflex (el que veurem al GUI)
log_file = C:\\Autodesk\\logs\\AutodeskLicenseLog.log
# Arguments (per referència / info; no usats directament quan s'invoca sc start)
launch_args = -z -c "%(license_file)s" -l "%(log_file)s"

[Zoo]
service_name = McNeelZoo8
admin_exe = C:\\Program Files (x86)\\Zoo 8\\ZooAdmin.Wpf.exe

[UI]
# Interval refresc estat en mil·lisegons
refresh_ms = 5000
# Dimensions finestra principal (amplexalt)
window_size = 400x350
# Mostrar avís "te jodes" (1=si,0=no)
show_te_jodes = 1

[CLI]
# Habilita accions CLI encara que no siguis administrador (1=si,0=no)
allow_non_admin_cli = 1

"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import ctypes
import os
import sys
import argparse
import configparser
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuració per defecte que s'escriurà si no existeix config.ini
# Nota: fem servir percent-formatting style de configparser per poder referenciar
# valors (p. ex. %(license_file)s a launch_args).
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_INI = """[Autodesk]
service_name = AutodeskLicenseServer
process_names = lmgrd.exe, adskflex.exe
working_dir = C:\\Autodesk
lmgrd_path = C:\\Autodesk\\lmgrd.exe
license_file = C:\\Autodesk\\SERVER1-AULES00155d06fb06-2024.lic
log_file = C:\\Autodesk\\logs\\AutodeskLicenseLog.log
launch_args = -z -c %(license_file)s -l %(log_file)s

[Zoo]
service_name = McNeelZoo8
admin_exe = C:\\Program Files (x86)\\Zoo 8\\ZooAdmin.Wpf.exe

[UI]
refresh_ms = 5000
window_size = 400x350
show_te_jodes = 1

[CLI]
allow_non_admin_cli = 1
"""

# Globals carregats des del fitxer de configuració (s'omplen a load_config)
CFG = {}

# Ruta global de la finestra principal Tk (definida a arrencar_gui)
finestra = None
label_autodesk = None
label_zoo = None


def ruta_recurs(nom_arxiu: str) -> str:
    """Retorna la ruta absoluta a un recurs empaquetat o al directori actual."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nom_arxiu)
    return os.path.join(os.path.abspath("."), nom_arxiu)


def es_admin() -> bool:
    """Retorna True si el procés té privilegis d'administrador."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # pragma: no cover - entorns no Windows
        return False


def load_config(path: str | os.PathLike | None = None) -> dict:
    """Carrega el fitxer INI i retorna un diccionari amb valors normalitzats.

    Si no existeix, crea un fitxer per defecte.
    """
    if path is None:
        # per defecte, mateix directori que l'script empaquetat/executable
        base_dir = Path(get_base_dir())
        path = base_dir / "config.ini"
    else:
        path = Path(path)

    if not path.exists():
        # crear-lo amb valors per defecte
        try:
            path.write_text(DEFAULT_CONFIG_INI, encoding="utf-8")
            print(f"[AVÍS] No s'ha trobat config.ini. S'ha creat un fitxer per defecte a: {path}")
        except Exception as e:
            print(f"[ERROR] No s'ha pogut crear config.ini per defecte: {e}")

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.optionxform = str  # mantenir majúscules si cal (però no crític)
    try:
        config.read(path, encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Error llegint config.ini: {e}")

    # Lectura seccions amb valors per defecte si falten
    autodesk = config["Autodesk"] if "Autodesk" in config else {}
    zoo = config["Zoo"] if "Zoo" in config else {}
    ui = config["UI"] if "UI" in config else {}
    cli = config["CLI"] if "CLI" in config else {}

    # Normalització
    process_names = autodesk.get("process_names", "lmgrd.exe,adskflex.exe")
    process_list = [p.strip() for p in process_names.split(",") if p.strip()]

    refresh_ms = int(ui.get("refresh_ms", "5000"))
    window_size = ui.get("window_size", "400x350")
    show_te_jodes = ui.getboolean("show_te_jodes", fallback=True)
    allow_non_admin_cli = cli.getboolean("allow_non_admin_cli", fallback=True)

    d = {
        "config_path": str(path),
        "Autodesk": {
            "service_name": autodesk.get("service_name", "AutodeskLicenseServer"),
            "process_names": process_list,
            "working_dir": autodesk.get("working_dir", r"C:\\Autodesk"),
            "lmgrd_path": autodesk.get("lmgrd_path", r"C:\\Autodesk\\lmgrd.exe"),
            "license_file": autodesk.get("license_file", r"C:\\Autodesk\\SERVER1.lic"),
            "log_file": autodesk.get("log_file", r"C:\\Autodesk\\logs\\AutodeskLicenseLog.log"),
            "launch_args": autodesk.get("launch_args", ""),
        },
        "Zoo": {
            "service_name": zoo.get("service_name", "McNeelZoo8"),
            "admin_exe": zoo.get("admin_exe", r"C:\\Program Files (x86)\\Zoo 8\\ZooAdmin.Wpf.exe"),
        },
        "UI": {
            "refresh_ms": refresh_ms,
            "window_size": window_size,
            "show_te_jodes": show_te_jodes,
        },
        "CLI": {
            "allow_non_admin_cli": allow_non_admin_cli,
        },
    }
    return d


def get_base_dir() -> str:
    """Directori on resideix l'executable (PyInstaller) o el script."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(sys.argv[0]))


# ---------------------------------------------------------------------------
# Funcions d'interacció amb serveis / processos
# ---------------------------------------------------------------------------

def executar_comanda_sc(comanda: str, servei: str) -> str:
    """Executa `sc <comanda> <servei>` i retorna stdout+stderr."""
    try:
        resultat = subprocess.run(
            ["sc", comanda, servei],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        return (resultat.stdout or "") + (resultat.stderr or "")
    except Exception as e:  # pragma: no cover - entorns no Windows
        return str(e)


def check_process_status(process_names: list[str]) -> list[str]:
    """Retorna la llista de processos (dels donats) que estan actius."""
    actius = []
    for nom_proc in process_names:
        # Utilitzem tasklist + findstr /I <proc> (mateix enfoc que l'script original)
        resultat = subprocess.run(
            f'tasklist | findstr /I {nom_proc}',
            capture_output=True,
            text=True,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if resultat.stdout.strip():
            actius.append(nom_proc)
    return actius


def kill_processes(process_names: list[str]) -> bool | str:
    """Mata qualsevol procés de la llista que estigui actiu.

    Retorna True si s'ha matat algun procés; False si no n'hi havia; o un string d'error.
    """
    actius = check_process_status(process_names)
    if not actius:
        return False
    for proc in actius:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:  # pragma: no cover
            return str(e)
    return True


def lmgrd_en_execucio() -> bool:
    """Comprova si *lmgrd.exe* apareix al tasklist (ignora maj/min)."""
    try:
        resultat = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return "lmgrd.exe" in resultat.stdout.lower()
    except Exception:  # pragma: no cover
        return False


def iniciar_servei(servei: str) -> str:
    return executar_comanda_sc("start", servei)


def aturar_servei(servei: str, autodesk: bool = False) -> str:
    """Atura un servei. Si és Autodesk, també mata processos orfes (lmgrd, etc.)."""
    resultat = executar_comanda_sc("stop", servei)
    if autodesk:
        kill_processes(CFG["Autodesk"]["process_names"])
    return resultat


def reiniciar_servei(servei: str, autodesk: bool = False) -> str:
    aturar_servei(servei, autodesk=autodesk)
    return iniciar_servei(servei)


# ---------------------------------------------------------------------------
# Funcions de sortida per terminal (mode CLI)
# ---------------------------------------------------------------------------

def veure_estat_terminal() -> None:
    autodesk_srv = CFG["Autodesk"]["service_name"]
    zoo_srv = CFG["Zoo"]["service_name"]
    log_file = CFG["Autodesk"]["log_file"]

    print("== Estat dels serveis ==")
    print("→ Autodesk:")
    print(executar_comanda_sc("query", autodesk_srv))
    print("→ Zoo:")
    print(executar_comanda_sc("query", zoo_srv))

    # Tail del log d'Autodesk en una consola PowerShell separada
    if os.path.exists(log_file):
        subprocess.Popen([
            "powershell", "-NoExit",
            f"Get-Content '{log_file}' -Wait"
        ])
    else:
        print(f"[AVÍS] No s'ha trobat el log Autodesk: {log_file}")

    ruta_zoo_admin = CFG["Zoo"]["admin_exe"]
    if os.path.exists(ruta_zoo_admin):
        subprocess.Popen(ruta_zoo_admin)
    else:
        print("No s'ha trobat ZooAdmin")


# ---------------------------------------------------------------------------
# GUI: diàlegs auxiliars
# ---------------------------------------------------------------------------

def obrir_zoo_admin():
    ruta = CFG["Zoo"]["admin_exe"]
    try:
        os.startfile(ruta)  # type: ignore[attr-defined]
    except Exception as e:  # pragma: no cover - entorn no Windows
        messagebox.showerror("Error obrint Zoo", f"No s'ha pogut obrir ZooAdmin:\n{e}")


def mostrar_info():
    a = CFG["Autodesk"]
    z = CFG["Zoo"]
    ui = CFG["UI"]

    missatge = (
        "GESTOR DEL SERVEI DE LLICÈNCIES\n"
        "──────────────────────────────────────\n"
        "Aquesta aplicació et permet controlar els serveis de llicències d'Autodesk i Rhino (Zoo).\n\n"
        "FUNCIONALITAT PRINCIPAL:\n"
        " - Iniciar, aturar o reiniciar el servei de llicències d'Autodesk (lmgrd.exe)\n"
        " - Control directe del servei de Rhino Zoo\n"
        " - L'estat del servei es comprova via 'sc' i 'tasklist'\n"
        " - Botó per obrir el log d'Autodesk (Get-Content -Wait)\n"
        " - Botó per obrir l'administrador gràfic del Zoo\n"
        " - Suport complet per a ús per línia d'ordres\n\n"
        "SERVEIS GESTIONATS:\n"
        f" - {a['service_name']} (via NSSM amb lmgrd.exe)\n"
        f" - {z['service_name']} (servei oficial de Rhino Zoo 8)\n\n"
        "COMPROVACIÓ D'ESTAT:\n"
        " - Si Autodesk està aturat però el procés lmgrd.exe està actiu → avís\n"
        " - Zoo es gestiona directament amb comandes SC\n\n"
        "RUTES (de config.ini):\n"
        f" - lmgrd_path: {a['lmgrd_path']}\n"
        f" - license_file: {a['license_file']}\n"
        f" - log_file: {a['log_file']}\n"
        f" - Zoo Admin: {z['admin_exe']}\n\n"
        "EXECUCIÓ PER LÍNIA D'ORDRES (flags):\n"
        "     > LicenseServerGUI.exe --start-zoo\n"
        "     > LicenseServerGUI.exe --restart-autodesk\n"
        "     > LicenseServerGUI.exe --status\n\n"
        "PERMISOS:\n"
        " - Necessari executar com a administrador per interactuar amb serveis\n\n"
        "LLEGENDA D'ESTATS:\n"
        " - ⬤  Servei actiu\n"
        " - ○  Servei aturat\n"
        " - ◐  Procés actiu, però el servei no\n"
        " - ?  Estat desconegut\n\n"
    )
    if ui.get("show_te_jodes", True):
        missatge += "Si no et funciona te jodes XD\n                                     - Quim"

    messagebox.showinfo("Informació", missatge)


def obrir_log():
    log_path = CFG["Autodesk"]["log_file"]
    if not os.path.exists(log_path):
        messagebox.showerror("Error", f"No s'ha trobat el fitxer de log:\n{log_path}")
        return

    finestra_log = tk.Toplevel(finestra)
    finestra_log.title("Log d'Autodesk")
    icona_path = ruta_recurs("LicenseServerIcon.ico")
    if os.path.exists(icona_path):
        finestra_log.iconbitmap(icona_path)
    finestra_log.geometry("800x400")

    text_log = tk.Text(finestra_log, wrap="none", font=("Consolas", 9))
    text_log.pack(fill="both", expand=True)

    scrollbar_y = tk.Scrollbar(finestra_log, command=text_log.yview)
    scrollbar_y.pack(side="right", fill="y")
    text_log.config(yscrollcommand=scrollbar_y.set)

    def actualitzar_log():
        try:
            ps_proc = subprocess.Popen(
                ["powershell", "-Command", f"Get-Content -Path '{log_path}' -Wait"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            def llegir_log():
                for linia in ps_proc.stdout:  # type: ignore[union-attr]
                    text_log.insert("end", linia)
                    text_log.see("end")
                if ps_proc.stdout:
                    ps_proc.stdout.close()

            # Thread de lectura per no bloquejar la GUI
            import threading
            threading.Thread(target=llegir_log, daemon=True).start()

        except Exception as e:  # pragma: no cover
            messagebox.showerror("Error log", f"No s'ha pogut obrir el log:\n{e}")

    actualitzar_log()


# ---------------------------------------------------------------------------
# GUI principal
# ---------------------------------------------------------------------------

def arrencar_gui():
    global finestra, label_autodesk, label_zoo

    autodesk_srv = CFG["Autodesk"]["service_name"]
    zoo_srv = CFG["Zoo"]["service_name"]
    refresh_ms = CFG["UI"]["refresh_ms"]
    win_size = CFG["UI"]["window_size"]

    def veure_estat():
        finestra.after(300, actualitzar_estat)

    def actualitzar_estat():
        servei_autodesk = executar_comanda_sc("query", autodesk_srv)
        servei_zoo = executar_comanda_sc("query", zoo_srv)
        lmgrd_actiu = lmgrd_en_execucio()

        # Autodesk
        if "RUNNING" in servei_autodesk:
            simbol_autodesk = "⬤"; color_autodesk = "green"; text_autodesk = "Autodesk: ACTIU"
        elif lmgrd_actiu:
            simbol_autodesk = "◐"; color_autodesk = "orange"; text_autodesk = "Autodesk: Procés actiu sense servei"
        elif "STOPPED" in servei_autodesk:
            simbol_autodesk = "○"; color_autodesk = "red"; text_autodesk = "Autodesk: ATURAT"
        else:
            simbol_autodesk = "?"; color_autodesk = "gray"; text_autodesk = "Autodesk: DESCONEGUT"

        label_autodesk.config(text=f"{text_autodesk} {simbol_autodesk}", fg=color_autodesk)

        # Zoo
        if "RUNNING" in servei_zoo:
            simbol_zoo = "⬤"; color_zoo = "green"; text_zoo = "Zoo: ACTIU"
        elif "STOPPED" in servei_zoo:
            simbol_zoo = "○"; color_zoo = "red"; text_zoo = "Zoo: ATURAT"
        else:
            simbol_zoo = "?"; color_zoo = "gray"; text_zoo = "Zoo: DESCONEGUT"

        label_zoo.config(text=f"{text_zoo} {simbol_zoo}", fg=color_zoo)

        # Refresc periòdic
        finestra.after(refresh_ms, veure_estat)

    finestra = tk.Tk()
    finestra.title("Gestor de serveis de llicències")

    icona_path = ruta_recurs("LicenseServerIcon.ico")
    if os.path.exists(icona_path):
        finestra.iconbitmap(icona_path)

    finestra.geometry(win_size)
    finestra.resizable(False, False)

    boto_info = tk.Button(finestra, text="ℹ", font=("Arial", 10, "bold"), width=2, command=mostrar_info)
    boto_info.place(x=365, y=5)  # posició fixa adaptada a 400x350; no crític

    boto_log_autodesk = tk.Button(finestra, text="Log\nAutodesk", font=("Arial", 9, "bold"), width=8, height=2, command=obrir_log)
    boto_log_autodesk.place(x=325, y=40)

    boto_log_zoo = tk.Button(finestra, text="Zoo Admin", font=("Arial", 9, "bold"), width=8, height=2, command=obrir_zoo_admin)
    boto_log_zoo.place(x=325, y=88)

    label_autodesk = tk.Label(finestra, font=("Segoe UI", 13), justify="left")
    label_autodesk.pack(pady=(20, 5))

    label_zoo = tk.Label(finestra, font=("Segoe UI", 13), justify="left")
    label_zoo.pack(pady=5)

    tk.Button(
        finestra, text="Iniciar Autodesk", width=20,
        command=lambda: [iniciar_servei(autodesk_srv), veure_estat()]
    ).pack(pady=3)

    tk.Button(
        finestra, text="Aturar Autodesk", width=20,
        command=lambda: [aturar_servei(autodesk_srv, autodesk=True), veure_estat()]
    ).pack(pady=3)

    tk.Button(
        finestra, text="Reiniciar Autodesk", width=20,
        command=lambda: [reiniciar_servei(autodesk_srv, autodesk=True), veure_estat()]
    ).pack(pady=3)

    tk.Button(
        finestra, text="Iniciar Zoo", width=20,
        command=lambda: [iniciar_servei(zoo_srv), veure_estat()]
    ).pack(pady=3)

    tk.Button(
        finestra, text="Aturar Zoo", width=20,
        command=lambda: [aturar_servei(zoo_srv), veure_estat()]
    ).pack(pady=3)

    tk.Button(
        finestra, text="Reiniciar Zoo", width=20,
        command=lambda: [reiniciar_servei(zoo_srv), veure_estat()]
    ).pack(pady=3)

    if not es_admin():
        messagebox.showwarning(
            "Advertència",
            "Aquest programa necessita permisos d'administrador per funcionar correctament."
        )

    veure_estat()
    finestra.mainloop()


# ---------------------------------------------------------------------------
# Funció principal (CLI + GUI)
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gestor serveis Autodesk i Zoo")
    parser.add_argument("--config", help="Ruta alternativa a config.ini", default=None)
    parser.add_argument("--start-zoo", action="store_true")
    parser.add_argument("--stop-zoo", action="store_true")
    parser.add_argument("--restart-zoo", action="store_true")
    parser.add_argument("--start-autodesk", action="store_true")
    parser.add_argument("--stop-autodesk", action="store_true")
    parser.add_argument("--restart-autodesk", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--info", action="store_true")
    return parser.parse_args()


def main():
    global CFG
    args = parse_args()
    CFG = load_config(args.config)

    autodesk_srv = CFG["Autodesk"]["service_name"]
    zoo_srv = CFG["Zoo"]["service_name"]

    # Si no hi ha flags, arrencar GUI
    if len(sys.argv) == 1 or (
        not any([
            args.start_zoo, args.stop_zoo, args.restart_zoo,
            args.start_autodesk, args.stop_autodesk, args.restart_autodesk,
            args.status, args.info,
        ])
    ):
        arrencar_gui()
        return

    # Mode CLI
    if not es_admin() and not CFG["CLI"]["allow_non_admin_cli"]:
        print("[ERROR] Cal executar com a administrador per a accions CLI.")
        return

    if args.start_zoo:
        print(iniciar_servei(zoo_srv))
    if args.stop_zoo:
        print(aturar_servei(zoo_srv))
    if args.restart_zoo:
        print(reiniciar_servei(zoo_srv))

    if args.start_autodesk:
        print(iniciar_servei(autodesk_srv))
    if args.stop_autodesk:
        print(aturar_servei(autodesk_srv, autodesk=True))
    if args.restart_autodesk:
        print(reiniciar_servei(autodesk_srv, autodesk=True))

    if args.status:
        veure_estat_terminal()
    if args.info:
        # en mode CLI la finestra messagebox no és útil → print
        mostrar_info_cli()


def mostrar_info_cli():
    """Versió text de mostrar_info() per a mode consola."""
    a = CFG["Autodesk"]
    z = CFG["Zoo"]
    print("GESTOR DEL SERVEI DE LLICÈNCIES")
    print("──────────────────────────────────────")
    print("SERVEIS GESTIONATS:")
    print(f" - {a['service_name']} (Autodesk NSSM)")
    print(f" - {z['service_name']} (McNeel Zoo 8)")
    print("RUTES:")
    print(f"   lmgrd_path: {a['lmgrd_path']}")
    print(f"   license_file: {a['license_file']}")
    print(f"   log_file: {a['log_file']}")
    print(f"   Zoo Admin: {z['admin_exe']}")


if __name__ == "__main__":
    main()
