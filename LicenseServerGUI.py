import tkinter as tk
from tkinter import messagebox
import subprocess
import ctypes
import os
import sys
import argparse

SERVEI_AUTODESK = "AutodeskLicenseServer"
SERVEI_ZOO = "McNeelZoo8"
RUTA_ZOO_ADMIN = r"C:\Program Files (x86)\Zoo 8\ZooAdmin.Wpf.exe"

def ruta_recurs(nom_arxiu):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nom_arxiu)
    return os.path.join(os.path.abspath("."), nom_arxiu)

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def executar_comanda_sc(comanda, servei):
    try:
        resultat = subprocess.run(
            ["sc", comanda, servei],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return resultat.stdout + resultat.stderr
    except Exception as e:
        return str(e)


def lmgrd_en_execucio():
    try:
        resultat = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "lmgrd.exe" in resultat.stdout.lower()
    except Exception:
        return False

def iniciar_servei(servei): return executar_comanda_sc("start", servei)
def aturar_servei(servei): return executar_comanda_sc("stop", servei)
def reiniciar_servei(servei):
    aturar_servei(servei)
    return iniciar_servei(servei)

def veure_estat_terminal():
    print("== Estat dels serveis ==")
    print("\u2192 Autodesk:")
    print(executar_comanda_sc("query", SERVEI_AUTODESK))
    print("\u2192 Zoo:")
    print(executar_comanda_sc("query", SERVEI_ZOO))

def obrir_zoo_admin():
    try:
        os.startfile(RUTA_ZOO_ADMIN)
    except Exception as e:
        messagebox.showerror("Error obrint Zoo", f"No s'ha pogut obrir ZooAdmin:\n{e}")

def mostrar_info():
    missatge = (
        "GESTOR DEL SERVEI DE LLICÈNCIES\n"
        "──────────────────────────────────────\n"
        "Aquesta aplicació et permet controlar els serveis de llicències d'Autodesk i Rhino (Zoo).\n\n"

        "FUNCIONALITAT PRINCIPAL:\n"
        " - Iniciar, aturar o reiniciar el servei de llicències d'Autodesk (lmgrd.exe)\n"
        " - Control directe del servei de Rhino Zoo (McNeelZoo8)\n"
        " - L'estat del servei es comprova via 'sc' i 'tasklist'\n"
        " - Botó per obrir l'administrador gràfic del Zoo (ZooAdmin.Wpf.exe)\n"
        " - Suport complet per a ús per línia d'ordres\n\n"

        "SERVEIS GESTIONATS:\n"
        f" - AutodeskLicenseServer (via NSSM amb lmgrd.exe)\n"
        f" - McNeelZoo8 (servei oficial de Rhino Zoo 8)\n\n"

        "COMPROVACIÓ D'ESTAT:\n"
        " - Si el servei Autodesk està aturat però el procés lmgrd.exe està actiu → es mostra un avís\n"
        " - Zoo es gestiona directament amb comandes SC\n\n"

        "RUTA ADMINISTRADOR ZOO:\n"
        f" - {RUTA_ZOO_ADMIN}\n\n"

        "EXECUCIÓ PER LÍNIA D'ORDRES:\n"
        " - Aquesta aplicació permet executar accions sense mostrar la interfície gràfica:\n"
        "     > python gestor_serveis.py --start-zoo\n"
        "     > python gestor_serveis.py --restart-autodesk\n"
        "     > python gestor_serveis.py --status\n\n"

        "PERMISOS:\n"
        " - L'aplicació necessita executar-se com a administrador per interactuar amb els serveis\n\n"
        
        "LLEGENDA D'ESTATS:\n"
        " - ⬤  Servei actiu\n"
        " - ○  Servei aturat\n"
        " - ◐  Procés actiu, però el servei no\n"
        " - ?   Estat desconegut\n" 
    
    )
    messagebox.showinfo("Informaci\u00f3", missatge)

def arrencar_gui():
    def veure_estat():
        finestra.after(300, actualitzar_estat)

    def actualitzar_estat():
        servei_autodesk = executar_comanda_sc("query", SERVEI_AUTODESK)
        servei_zoo = executar_comanda_sc("query", SERVEI_ZOO)
        lmgrd_actiu = lmgrd_en_execucio()

        # Autodesk
        if "RUNNING" in servei_autodesk:
            simbol_autodesk = "⬤"; color_autodesk = "green"; text_autodesk = "Autodesk: ACTIU"
        elif lmgrd_actiu:
            simbol_autodesk = "◐"; color_autodesk = "orange"; text_autodesk = "Autodesk: Proc\u00e9s actiu sense servei"
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

        # Refresc cada 5 segons
        finestra.after(5000, veure_estat)

    global finestra
    finestra = tk.Tk()
    finestra.title("Gestor de serveis de llic\u00e8ncies")

    icona_path = ruta_recurs("LicenseServerIcon.ico")
    if os.path.exists(icona_path):
        finestra.iconbitmap(icona_path)

    finestra.geometry("400x400")
    finestra.resizable(False, False)

    boto_info = tk.Button(finestra, text="ℹ", font=("Arial", 10, "bold"), width=2, command=mostrar_info)
    boto_info.place(x=365, y=5)

    global label_autodesk, label_zoo
    label_autodesk = tk.Label(finestra, font=("Segoe UI", 13), justify="left")
    label_autodesk.pack(pady=(20, 5))

    label_zoo = tk.Label(finestra, font=("Segoe UI", 13), justify="left")
    label_zoo.pack(pady=5)

    tk.Button(finestra, text="Iniciar Autodesk", width=20, command=lambda: [iniciar_servei(SERVEI_AUTODESK), veure_estat()]).pack(pady=3)
    tk.Button(finestra, text="Aturar Autodesk", width=20, command=lambda: [aturar_servei(SERVEI_AUTODESK), veure_estat()]).pack(pady=3)
    tk.Button(finestra, text="Reiniciar Autodesk", width=20, command=lambda: [reiniciar_servei(SERVEI_AUTODESK), veure_estat()]).pack(pady=3)

    tk.Button(finestra, text="Iniciar Zoo", width=20, command=lambda: [iniciar_servei(SERVEI_ZOO), veure_estat()]).pack(pady=3)
    tk.Button(finestra, text="Aturar Zoo", width=20, command=lambda: [aturar_servei(SERVEI_ZOO), veure_estat()]).pack(pady=3)
    tk.Button(finestra, text="Reiniciar Zoo", width=20, command=lambda: [reiniciar_servei(SERVEI_ZOO), veure_estat()]).pack(pady=3)

    tk.Button(finestra, text="Obrir Zoo Admin", width=20, command=obrir_zoo_admin).pack(pady=12)

    if not es_admin():
        messagebox.showwarning("Advert\u00e8ncia", "Aquest programa necessita permisos d'administrador per funcionar correctament.")

    veure_estat()
    finestra.mainloop()

parser = argparse.ArgumentParser(description="Gestor serveis Autodesk i Zoo")
parser.add_argument("--start-zoo", action="store_true")
parser.add_argument("--stop-zoo", action="store_true")
parser.add_argument("--restart-zoo", action="store_true")
parser.add_argument("--start-autodesk", action="store_true")
parser.add_argument("--stop-autodesk", action="store_true")
parser.add_argument("--restart-autodesk", action="store_true")
parser.add_argument("--status", action="store_true")
parser.add_argument("--info", action="store_true")
args = parser.parse_args()

if len(sys.argv) == 1:
    arrencar_gui()
else:
    if args.start_zoo: print(iniciar_servei(SERVEI_ZOO))
    if args.stop_zoo: print(aturar_servei(SERVEI_ZOO))
    if args.restart_zoo: print(reiniciar_servei(SERVEI_ZOO))
    if args.start_autodesk: print(iniciar_servei(SERVEI_AUTODESK))
    if args.stop_autodesk: print(aturar_servei(SERVEI_AUTODESK))
    if args.restart_autodesk: print(reiniciar_servei(SERVEI_AUTODESK))
    if args.status: veure_estat_terminal()
    if args.info: mostrar_info()
