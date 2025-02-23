#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import imageio
import numpy as np
from PIL import Image


ASCII_CHARS = "@%#*+=-:. "

# ---------------------- FONCTIONS DE CONVERSION ---------------------------
def redimensionner_image(image, largeur_target, hauteur_target=None):
    """
    Redimensionne l'image.
    Si hauteur_target est None, la hauteur est calculée pour conserver le ratio.
    Sinon, on redimensionne exactement à (largeur_target, hauteur_target).
    """
    if largeur_target is None and hauteur_target is None:
        return image
    if largeur_target is not None and hauteur_target is not None:
        return image.resize((largeur_target, hauteur_target))
    if largeur_target is not None:
        ratio = image.height / image.width
        return image.resize((largeur_target, int(largeur_target * ratio)))
    ratio = image.width / image.height
    return image.resize((int(hauteur_target * ratio), hauteur_target))
def convertir_en_niveaux_de_gris(image):
    """Convertit l'image en niveaux de gris."""
    return image.convert("L")
def conversion_pixels_ascii(image):
    """
    Convertit une image (en niveaux de gris) en texte ASCII (sans couleur).
    """
    arr = np.array(image)
    indices = (arr / 255 * (len(ASCII_CHARS) - 1)).astype(int)
    lignes = []
    for ligne in indices:
        ligne_txt = "".join(ASCII_CHARS[p] for p in ligne)
        lignes.append(ligne_txt)
    return "\n".join(lignes)
def conversion_pixels_ascii_couleur(image):
    """
    Convertit une image en texte ASCII avec couleur.
    Chaque caractère est coloré via une séquence ANSI correspondant à la couleur du pixel.
    """
    arr = np.array(image)
    lignes = []
    for ligne in arr:
        ligne_txt = ""
        for pixel in ligne:
            r, g, b = pixel[:3]
            # Calcul d'une luminosité pondérée pour choisir le caractère
            luminosite = int(0.2989 * r + 0.5870 * g + 0.1140 * b)
            index = int(luminosite / 255 * (len(ASCII_CHARS) - 1))
            caractere = ASCII_CHARS[index]
            ligne_txt += f"\033[38;2;{r};{g};{b}m{caractere}\033[0m"
        lignes.append(ligne_txt)
    return "\n".join(lignes)
def frame_to_ascii(frame, largeur, hauteur, couleur):
    """
    Convertit une frame en ASCII avec ou sans couleur.
    """
    if not isinstance(frame, Image.Image):
        frame = Image.fromarray(frame)
    frame = redimensionner_image(frame, largeur, hauteur)
    if couleur:
        return conversion_pixels_ascii_couleur(frame)
    else:
        gris = convertir_en_niveaux_de_gris(frame)
        return conversion_pixels_ascii(gris)
def conversion_image_ascii(chemin_image, largeur, hauteur, couleur):
    """
    Ouvre l'image depuis chemin_image, la convertit en ASCII et retourne le texte.
    Pour éviter les problèmes de transparence ou de palette, on convertit en RGB.
    """
    try:
        img = Image.open(chemin_image)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    except Exception as e:
        raise Exception("Erreur lors de l'ouverture de l'image : " + str(e))
    return frame_to_ascii(img, largeur, hauteur, couleur)
# ------------------- FONCTIONS AUDIO ET AFFICHAGE EN CMD ------------------
def jouer_audio(chemin_video):
    """
    Lance ffplay pour lire l'audio du fichier vidéo en arrière-plan.
    Utilise shell=True pour que Windows trouve ffplay via le PATH.
    """
    try:
        commande = f'ffplay -nodisp -autoexit "{chemin_video}"'
        subprocess.Popen(commande, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("Erreur lors de la lecture de l'audio :", e)
def lire_video_ascii_cmd(chemin_video, largeur, hauteur, couleur, fps):
    """
    Lit la vidéo MP4, convertit chaque frame en ASCII et affiche directement dans le terminal.
    L'audio est lancé en parallèle avec ffplay.
    """
    delay = 1.0 / fps
    threading.Thread(target=jouer_audio, args=(chemin_video,), daemon=True).start()
    try:
        lecteur = imageio.get_reader(chemin_video, "ffmpeg")
        for frame in lecteur:
            ascii_frame = frame_to_ascii(frame, largeur, hauteur, couleur)
            os.system("cls")  # Efface l'écran
            print(ascii_frame)  # Affiche la frame ASCII
            time.sleep(delay)
    except Exception as e:
        print("Erreur lors du traitement de la vidéo :", e)
# --------------------------- INTERFACE GRAPHIQUE ---------------------------
root = tk.Tk()
root.title("Convertisseur ASCII")
root.configure(bg="#2E2E2E")
# Styles pour l'interface
police_label = ("Helvetica", 11, "bold")
police_entry = ("Helvetica", 11)
# --- Section Fichier d'entrée ---
cadre_entree = tk.Frame(root, bg="#2E2E2E")
cadre_entree.pack(pady=10, padx=10, fill="x")
tk.Label(cadre_entree, text="Fichier d'entrée :", fg="white", bg="#2E2E2E", font=police_label).pack(side="left", padx=5)
entree_fichier = tk.Entry(cadre_entree, width=50, font=police_entry)
entree_fichier.pack(side="left", padx=5)
btn_parcourir = tk.Button(cadre_entree, text="Parcourir", font=police_label,
                          command=lambda: (entree_fichier.delete(0, tk.END),
                                           entree_fichier.insert(0, filedialog.askopenfilename(filetypes=[("Images & Vidéos", "*.jpg;*.png;*.mp4")]))))
btn_parcourir.pack(side="left", padx=5)
# --- Section Options ---
cadre_options = tk.Frame(root, bg="#2E2E2E")
cadre_options.pack(pady=10, padx=10, fill="x")
# Option Couleur
var_couleur = tk.BooleanVar(value=False)
chk_couleur = tk.Checkbutton(cadre_options, text="Couleur", variable=var_couleur,
                              fg="white", bg="#2E2E2E", font=police_label, activebackground="#2E2E2E",
                              selectcolor="#4CAF50")  # Couleur de fond du bouton lorsqu'il est sélectionné
chk_couleur.grid(row=0, column=0, padx=5, pady=5, sticky="w")
# Largeur
tk.Label(cadre_options, text="Largeur :", fg="white", bg="#2E2E2E", font=police_label).grid(row=0, column=1, padx=5, pady=5, sticky="w")
entree_largeur = tk.Entry(cadre_options, width=6, font=police_entry)
entree_largeur.insert(0, "100")
entree_largeur.grid(row=0, column=2, padx=5, pady=5, sticky="w")
# Hauteur (optionnelle)
tk.Label(cadre_options, text="Hauteur (optionnel) :", fg="white", bg="#2E2E2E", font=police_label).grid(row=0, column=3, padx=5, pady=5, sticky="w")
entree_hauteur = tk.Entry(cadre_options, width=6, font=police_entry)
entree_hauteur.insert(0, "")
entree_hauteur.grid(row=0, column=4, padx=5, pady=5, sticky="w")
# FPS pour vidéo
tk.Label(cadre_options, text="FPS (vidéo) :", fg="white", bg="#2E2E2E", font=police_label).grid(row=0, column=5, padx=5, pady=5, sticky="w")
entree_fps = tk.Entry(cadre_options, width=6, font=police_entry)
entree_fps.insert(0, "10")
entree_fps.grid(row=0, column=6, padx=5, pady=5, sticky="w")
# --- Bouton de conversion ---
def lancer_conversion():
    chemin = entree_fichier.get().strip()
    if not chemin:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier d'entrée.")
        return
    try:
        largeur = int(entree_largeur.get())
    except:
        largeur = 100
    hauteur_text = entree_hauteur.get().strip()
    hauteur = int(hauteur_text) if hauteur_text.isdigit() else largeur
    couleur = var_couleur.get()  # Récupère l'état du bouton "Couleur"
    try:
        fps = int(entree_fps.get())
    except:
        fps = 10
    extension = os.path.splitext(chemin)[1].lower()
    if extension in [".jpg", ".png"]:
        ascii_art = conversion_image_ascii(chemin, largeur, hauteur, couleur)
        os.system("cls")  # Efface l'écran
        print(ascii_art)  # Affiche l'image ASCII
    elif extension == ".mp4":
        threading.Thread(target=lire_video_ascii_cmd, args=(chemin, largeur, hauteur, couleur, fps), daemon=True).start()
    else:
        messagebox.showerror("Erreur", "Format non supporté.")
btn_convertir = tk.Button(root, text="Convertir et Jouer", font=police_label, command=lancer_conversion, bg="#4CAF50", fg="white")
btn_convertir.pack(pady=15)
root.mainloop()