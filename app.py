# -----------------------------------------
# Fichier : app.py
# -----------------------------------------
import os
import json
import feedparser
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Chargement du JSON contenant les infos sur les médias
with open('media_data.json', 'r', encoding='utf-8') as f:
    MEDIA_INFO = json.load(f)

# Cette variable contiendra la liste actualisée des vidéos 
# provenant de tous les flux.
# Nous allons construire une structure de données de la forme :
# {
#   "Blast": [ { titre, lien, date, ... }, ... ],
#   "LeMédia": [ { ... }, ... ],
#   ...
# }
VIDEOS_BY_MEDIA = {}

def fetch_videos_for_all_medias():
    """
    Fonction pour récupérer les vidéos de chaque média 
    via leur flux RSS YouTube.
    Renseigne VIDEOS_BY_MEDIA avec la liste des vidéos de chaque média
    triées par date de publication (décroissant).
    """
    global VIDEOS_BY_MEDIA
    VIDEOS_BY_MEDIA = {}

    # On parcourt tous les médias définis dans MEDIA_INFO
    for media_name, info in MEDIA_INFO.items():
        flux_url = info.get('flux')
        if flux_url:
            feed = feedparser.parse(flux_url)

            # Liste pour stocker les vidéos du média courant
            media_videos = []
            
            for entry in feed.entries:
                # Récupération des informations essentielles
                video_title = entry.title
                video_link = entry.link
                published_parsed = entry.published_parsed  # struct_time
                if published_parsed:
                    # Convertir en objet datetime pour faciliter les tris
                    published_date = datetime(*published_parsed[:6])
                else:
                    # S'il n'y a pas de date publiée, on prend la date actuelle (choix arbitraire)
                    published_date = datetime.now()
                
                # Récupération de l'ID vidéo à partir du lien
                # Sur un flux YouTube, le lien ressemble à "https://www.youtube.com/watch?v=XYZ..."
                # On peut l'extraire si nécessaire pour construire une miniature
                # Mais on peut aussi se contenter de l'URL générée par YT
                video_id = None
                if "watch?v=" in video_link:
                    video_id = video_link.split("watch?v=")[1]
                
                # Construction de l'URL miniature (thumbnail) si nécessaire
                # YouTube thumbnail : "https://img.youtube.com/vi/<VIDEO_ID>/hqdefault.jpg"
                thumbnail_url = None
                if video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

                # On crée un dictionnaire représentant la vidéo
                video_data = {
                    "title": video_title,
                    "link": video_link,
                    "published": published_date,
                    "thumbnail": thumbnail_url
                }
                # On ajoute la vidéo à la liste
                media_videos.append(video_data)
            
            # On trie la liste en ordre décroissant de date
            media_videos.sort(key=lambda x: x["published"], reverse=True)
            
            # On enregistre la liste dans VIDEOS_BY_MEDIA
            VIDEOS_BY_MEDIA[media_name] = media_videos

# Appel initial pour remplir la liste des vidéos au lancement
fetch_videos_for_all_medias()

@app.route('/')
def home():
    """
    Page d'accueil.
    - 12 dernières vidéos tous médias confondus (classées par date)
    - 10 dernières vidéos par orientation (Gauche, Centre, Droite, Autres)
    - Barre latérale : liste alphabétique des médias 
                      + 5 dernières vidéos de chaque média
    """
    # Construction d'une liste de toutes les vidéos tous médias confondus
    all_videos = []
    for media_name, videos in VIDEOS_BY_MEDIA.items():
        for video in videos:
            # On ajoute dans l'objet la référence au media_name 
            # (pour l'identifier plus tard si besoin)
            all_videos.append({
                "media_name": media_name,
                "title": video["title"],
                "link": video["link"],
                "published": video["published"],
                "thumbnail": video["thumbnail"],
                "orientation": MEDIA_INFO[media_name]["orientation"]
            })
    
    # Tri par date de publication décroissante
    all_videos.sort(key=lambda x: x["published"], reverse=True)

    # Sélection des 12 dernières vidéos tous médias confondus
    last_12_videos = all_videos[:12]

    # Maintenant, on veut récupérer 10 dernières vidéos par orientation
    # On crée un dictionnaire par orientation
    videos_by_orientation = {
        "Gauche": [],
        "Centre": [],
        "Droite": [],
        "Autres": []
    }
    for vid in all_videos:
        orientation = vid["orientation"]
        if orientation in videos_by_orientation:
            videos_by_orientation[orientation].append(vid)
        else:
            videos_by_orientation["Autres"].append(vid)  # fallback si non reconnu

    # On limite chaque orientation aux 10 dernières vidéos
    for orientation in videos_by_orientation:
        videos_by_orientation[orientation] = videos_by_orientation[orientation][:10]

    # Construction de la liste de médias par ordre alphabétique
    media_names_sorted = sorted(MEDIA_INFO.keys())

    # Pour la barre latérale, on veut aussi les 5 dernières vidéos de chaque média
    last_5_by_media = {}
    for media_name in media_names_sorted:
        # Récupérer les 5 premières vidéos dans VIDEOS_BY_MEDIA[media_name]
        # si elles existent
        media_videos = VIDEOS_BY_MEDIA.get(media_name, [])
        last_5_by_media[media_name] = media_videos[:5]
    
    return render_template('index.html',
                           last_12_videos=last_12_videos,
                           videos_by_orientation=videos_by_orientation,
                           media_names_sorted=media_names_sorted,
                           last_5_by_media=last_5_by_media)

@app.route('/media/<media_name>')
def media_page(media_name):
    """
    Page spécifique à un média.
    Affiche le background, l'orientation, le PDG, etc. 
    + Toutes les vidéos (ou un sous-ensemble) de ce média.
    """
    # Informations du média
    info = MEDIA_INFO.get(media_name, {})
    orientation = info.get("orientation", "Inconnu")
    pdg = info.get("pdg", "Inconnu")
    description = info.get("description", "")
    interets_eco = info.get("interets_economiques", "")

    # Liste complète (ou en partie) des vidéos du média
    media_videos = VIDEOS_BY_MEDIA.get(media_name, [])

    return render_template('media.html',
                           media_name=media_name,
                           orientation=orientation,
                           pdg=pdg,
                           description=description,
                           interets_economiques=interets_eco,
                           media_videos=media_videos)

@app.route('/refresh')
def refresh_feeds():
    """
    Route permettant de rafraîchir manuellement les flux (par ex. via un lien).
    """
    fetch_videos_for_all_medias()
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Lancement de l'appli Flask en mode debug
    # Sur Render, la configuration se fera différemment, 
    # mais en local on peut faire :
    app.run(debug=True, host='0.0.0.0', port=5000)
