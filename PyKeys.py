import subprocess
import sys
import os
import ctypes
import customtkinter as ctk
from PIL import Image, ImageDraw
from tkinter import filedialog
from pathlib import Path

# config du theme
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("green") 

# algo des clés SSH
ALGORITHMS = {
    "ECDSA (521 bits)": {"type": "ecdsa", "bits": "521"},
    "ed25519": {"type": "ed25519", "bits": None},
    "RSA (4096 bits)": {"type": "rsa", "bits": "4096"}
}

# Utilitaires
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def make_rounded_image(pil_img, radius=12):
    pil_img = pil_img.convert("RGBA")
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), pil_img.size], radius=radius, fill=255)
    pil_img.putalpha(mask)
    return pil_img

# ico dans la barre des tâches
try:
    myappid = 'innlog_ssh_manager'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Application Principale
app = ctk.CTk()
app.title("PyKeys")

try:
    icon_path = resource_path("ssh.ico")
    app.iconbitmap(icon_path)
except Exception:
    pass

# logo innlog
try:
    logo_file = resource_path("innlog.png")
    pil_image = Image.open(logo_file)
    pil_image_rounded = make_rounded_image(pil_image, radius=70)
    logo_image = ctk.CTkImage(light_image=pil_image_rounded, dark_image=pil_image_rounded, size=(270, 80))
    lbl_logo = ctk.CTkLabel(app, image=logo_image, text="")
    lbl_logo.pack(pady=(10, 5))
except Exception:
    pass

# Changement d'onglet
def switch_mode(mode):
    if mode == "Générer une clé":
        frame_send.pack_forget()
        frame_gen.pack(fill="both", expand=True)
        app.geometry("450x410")
    else:
        frame_gen.pack_forget()
        frame_send.pack(fill="both", expand=True)
        app.geometry("500x590")

mode_selector = ctk.CTkSegmentedButton(
    app,
    values=["Générer une clé", "Envoyer une clé"],
    command=switch_mode,
    font=("Segoe UI", 12, "bold"),
    selected_color="#2fa572",
    selected_hover_color="#1e7e53"
)
mode_selector.pack(padx=25, pady=(0, 10))

# VUE 1 : génération de clés SSH
frame_gen = ctk.CTkFrame(app, fg_color="transparent")

def show_gen_status(message, color="red"):
    lbl_gen_status.configure(text=message, text_color=color)

def toggle_passphrase_entry():
    if var_use_passphrase.get():
        entry_passphrase.pack(padx=25, pady=(0, 5), before=lbl_gen_status)
        app.geometry("450x480")
    else:
        entry_passphrase.pack_forget()
        entry_passphrase.delete(0, 'end')
        app.geometry("450x450")

def process_key_generation(force_overwrite=False):
    key_name = entry_key_name.get().strip()
    selected_algo = combo_algo.get()

    frame_confirm.pack_forget()
    show_gen_status("")

    if not key_name:
        show_gen_status("Veuillez entrer un nom pour la clé.", "#f87171")
        return

    passphrase = ""
    if var_use_passphrase.get():
        passphrase = entry_passphrase.get()
        if not passphrase:
            show_gen_status("Veuillez entrer une passphrase.", "#f87171")
            return

    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)
    key_path = ssh_dir / key_name

    if key_path.exists() and not force_overwrite:
        show_gen_status(f"Une clé '{key_name}' existe déjà.", "#fbbf24")
        frame_confirm.pack(padx=25, pady=(0, 5), before=lbl_gen_status)
        return

    algo_config = ALGORITHMS[selected_algo]
    cmd = ["ssh-keygen", "-t", algo_config["type"]]
    if algo_config["bits"]:
        cmd.extend(["-b", algo_config["bits"]])
        
    cmd.extend(["-f", str(key_path), "-N", passphrase])

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        show_gen_status("Clé générée avec succès !", "#4ade80")
        entry_key_name.delete(0, 'end')
        entry_passphrase.delete(0, 'end')
        var_use_passphrase.set(False)
        toggle_passphrase_entry()

    except FileNotFoundError:
        show_gen_status("Erreur : commande 'ssh-keygen' introuvable.", "#f87171")
    except subprocess.CalledProcessError as e:
        show_gen_status(f"Erreur : {e.stderr.strip()}", "#f87171")

def cancel_overwrite():
    frame_confirm.pack_forget()
    show_gen_status("")

# formulaire
lbl_algo = ctk.CTkLabel(frame_gen, text="Algorithme de chiffrement :", font=("Segoe UI", 12, "bold"))
lbl_algo.pack(anchor="w", padx=25, pady=(5, 2))

combo_algo = ctk.CTkComboBox(frame_gen, values=list(ALGORITHMS.keys()), width=400, state="readonly")
combo_algo.set(list(ALGORITHMS.keys())[0])
combo_algo.pack(padx=25, pady=(0, 10))

lbl_key_name = ctk.CTkLabel(frame_gen, text="Nom de la clé :", font=("Segoe UI", 12, "bold"))
lbl_key_name.pack(anchor="w", padx=25, pady=(2, 2))

entry_key_name = ctk.CTkEntry(frame_gen, width=400)
entry_key_name.pack(padx=25, pady=(0, 10))

var_use_passphrase = ctk.BooleanVar(value=False)
chk_passphrase = ctk.CTkCheckBox(
    frame_gen, 
    text="Protéger la clé avec une passphrase", 
    variable=var_use_passphrase,
    command=toggle_passphrase_entry,
    font=("Segoe UI", 12)
)
chk_passphrase.pack(anchor="w", padx=25, pady=(5, 10))

entry_passphrase = ctk.CTkEntry(
    frame_gen, 
    width=400, 
    placeholder_text="Entrez votre passphrase",
    show="*"
)

frame_confirm = ctk.CTkFrame(frame_gen, fg_color="transparent")
lbl_confirm = ctk.CTkLabel(frame_confirm, text="Voulez-vous la remplacer ?", font=("Segoe UI", 11))
lbl_confirm.pack(side="left", padx=(0, 10))

btn_yes = ctk.CTkButton(frame_confirm, text="Remplacer", width=90, height=28, fg_color="#e11d48", hover_color="#be123c", command=lambda: process_key_generation(force_overwrite=True))
btn_yes.pack(side="left", padx=5)

btn_no = ctk.CTkButton(frame_confirm, text="Annuler", width=80, height=28, fg_color="gray", command=cancel_overwrite)
btn_no.pack(side="left", padx=5)

lbl_gen_status = ctk.CTkLabel(frame_gen, text="", font=("Segoe UI", 11, "bold"), wraplength=400)
lbl_gen_status.pack(pady=(0, 5))

btn_generate = ctk.CTkButton(
    frame_gen, 
    text="Générer la paire de clés SSH", 
    command=lambda: process_key_generation(force_overwrite=False), 
    width=400,
    height=40,
    font=("Segoe UI", 13, "bold")
)
btn_generate.pack(padx=25, pady=(0, 15))


# VUE 2 : envoi de clés SSH sur le serveur distant
frame_send = ctk.CTkFrame(app, fg_color="transparent")

def show_send_status(message, color="red"):
    lbl_send_status.configure(text=message, text_color=color)

# fenetre pour choisir sa clé
def browse_pub_key():
    initial_dir = Path.home() / ".ssh"
    if not initial_dir.exists():
        initial_dir = Path.home()
        
    filename = filedialog.askopenfilename(
        initialdir=initial_dir,
        title="Sélectionner la clé publique",
        filetypes=(("Clés publiques SSH", "*.pub"), ("Tous les fichiers", "*.*"))
    )
    if filename:
        entry_key_path.delete(0, 'end')
        entry_key_path.insert(0, filename)
        show_send_status("")

def deploy_key():
    show_send_status("")
    btn_deploy.configure(state="disabled", text="Déploiement en cours...")
    app.update()

    pub_key_path = entry_key_path.get().strip()
    login = entry_login.get().strip()
    ip = entry_ip.get().strip()
    port = entry_port.get().strip() or "22"

    if not pub_key_path or not Path(pub_key_path).exists():
        show_send_status("Erreur : Fichier de clé publique invalide.", "#f87171")
        return finalize_deploy()
    if not login:
        show_send_status("Erreur : Login serveur manquant.", "#f87171")
        return finalize_deploy()
    if not ip:
        show_send_status("Erreur : IP serveur manquante.", "#f87171")
        return finalize_deploy()

    server_command = (
        "mkdir -p ~/.ssh && "
        "cat >> ~/.ssh/authorized_keys && "
        "chmod 700 ~/.ssh && "
        "chmod 600 ~/.ssh/authorized_keys"
    )
    
    ssh_cmd = f"ssh -p {port} {login}@{ip}"
    full_cmd = f'type "{pub_key_path}" | {ssh_cmd} "{server_command}"'

    try:
        subprocess.run(
            ["powershell", "-Command", full_cmd],
            capture_output=True,
            text=True,
            check=True
        )
        show_send_status("Clé déployée avec succès !", "#4ade80")
        
    except FileNotFoundError:
        show_send_status("Erreur : PowerShell ou SSH introuvable.", "#f87171")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip()
        if "Permission denied" in error_msg:
             show_send_status("Erreur : Authentification échouée (vérifier mdp/clé).", "#f87171")
        elif "Could not resolve hostname" in error_msg:
             show_send_status("Erreur : Impossible de joindre l'IP/Hostname.", "#f87171")
        else:
             show_send_status("Erreur lors du déploiement.", "#f87171")
        print(f"Détails de l'erreur:\n{error_msg}")
    finally:
        finalize_deploy()

def finalize_deploy():
    btn_deploy.configure(state="normal", text="Envoyer la clé SSH")

# formulaire
lbl_key = ctk.CTkLabel(frame_send, text="1. Choisir la clé publique à envoyer :", font=("Segoe UI", 13, "bold"))
lbl_key.pack(anchor="w", padx=25, pady=(4, 2))

sub_frame_key = ctk.CTkFrame(frame_send, fg_color="transparent")
sub_frame_key.pack(fill="x", padx=25, pady=(0, 4))

entry_key_path = ctk.CTkEntry(sub_frame_key, width=330)
entry_key_path.pack(side="left", padx=(0, 10))

btn_browse = ctk.CTkButton(sub_frame_key, text="Parcourir...", width=90, command=browse_pub_key)
btn_browse.pack(side="left")

lbl_serv = ctk.CTkLabel(frame_send, text="2. Configuration du serveur distant :", font=("Segoe UI", 13, "bold"))
lbl_serv.pack(anchor="w", padx=25, pady=(4, 2))

sub_frame_serv = ctk.CTkFrame(frame_send, fg_color="transparent")
sub_frame_serv.pack(fill="x", padx=25, pady=(0, 4))

lbl_login = ctk.CTkLabel(sub_frame_serv, text="Login :", font=("Segoe UI", 11))
lbl_login.pack(anchor="w", pady=(0, 0))
entry_login = ctk.CTkEntry(sub_frame_serv, width=450)
entry_login.pack(pady=(0, 4))

lbl_ip = ctk.CTkLabel(sub_frame_serv, text="IP ou Hostname :", font=("Segoe UI", 11))
lbl_ip.pack(anchor="w", pady=(0, 0))
entry_ip = ctk.CTkEntry(sub_frame_serv, width=450)
entry_ip.pack(pady=(0, 4))

lbl_port = ctk.CTkLabel(sub_frame_serv, text="Port :", font=("Segoe UI", 11))
lbl_port.pack(anchor="w", pady=(0, 0))
entry_port = ctk.CTkEntry(sub_frame_serv, width=450)
entry_port.pack(pady=(0, 4))

send_info_text = (
    "Informations importantes :\n"
    "• Pour envoyer la clé, l'utilitaire vous demandera le mot de passe du serveur.\n"
    "• Pour les serveurs avec login/mdp DÉSACTIVÉ en SSH :\n"
    "Un fichier config n'est pas obligatoire, la commande ssh {login}@{IP} suffira.\n"
    "• Pour les serveurs avec login/mdp ACTIVÉ :\n"
    "Un fichier config (alias/chemin clé privée) est FORTEMENT recommandé."
)

lbl_send_info = ctk.CTkLabel(
    frame_send, 
    text=send_info_text, 
    font=("Segoe UI", 11), 
    text_color="#9ca3af", 
    wraplength=440, 
    justify="left", 
    anchor="w"
)
lbl_send_info.pack(padx=25, pady=(2, 2), fill="x")

lbl_send_status = ctk.CTkLabel(frame_send, text="", font=("Segoe UI", 12, "bold"), wraplength=450)
lbl_send_status.pack(pady=(2, 2))

btn_deploy = ctk.CTkButton(
    frame_send, 
    text="Envoyer la clé SSH", 
    command=deploy_key, 
    width=450,
    height=42,
    font=("Segoe UI", 14, "bold")
)
btn_deploy.pack(padx=25, pady=(2, 10))

mode_selector.set("Générer une clé")
switch_mode("Générer une clé")

app.resizable(False, False)
app.mainloop()