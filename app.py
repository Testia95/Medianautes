# -----------------------------------------
# Fichier : app.py
# -----------------------------------------
import os
import json
import feedparser
from flask import Flask, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Charger le fichier JSON contenant la configuration des médias
with open('media_data.json', 'r', encoding='utf-8') as f:
    MEDIA_INFO = json.load(f)

# Dictionnaire pour stocker les vidéos récupérées pour chaque média
VIDEOS_BY_MEDIA = {}

def fetch_videos_for_all_medias():
    """
    Récupère les vidéos via les flux RSS YouTube de chaque média.
    Pour chaque média, on construit une liste de vidéos (titre, lien, date, miniature),
    triée par date décroissante.
    """
    global VIDEOS_BY_MEDIA
    VIDEOS_BY_MEDIA = {}

    for media_name, info in MEDIA_INFO.items():
        flux_url = info.get('flux')
        if flux_url:
            feed = feedparser.parse(flux_url)
            media_videos = []
            for entry in feed.entries:
                video_title = entry.title
                video_link = entry.link
                published_parsed = entry.published_parsed
                if published_parsed:
                    published_date = datetime(*published_parsed[:6])
                else:
                    published_date = datetime.now()
                
                video_id = None
                if "watch?v=" in video_link:
                    video_id = video_link.split("watch?v=")[1]
                
                thumbnail_url = None
                if video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

                video_data = {
                    "title": video_title,
                    "link": video_link,
                    "published": published_date,
                    "thumbnail": thumbnail_url
                }
                media_videos.append(video_data)
            media_videos.sort(key=lambda x: x["published"], reverse=True)
            VIDEOS_BY_MEDIA[media_name] = media_videos

# Appel initial pour remplir VIDEOS_BY_MEDIA
fetch_videos_for_all_medias()

# Context Processor pour rendre disponibles dans tous les templates
@app.context_processor
def inject_sidebar_data():
    """
    Injecte dans chaque template la liste triée des médias et pour chacun les 5 dernières vidéos.
    Ceci permet d'afficher une barre latérale uniforme sur toutes les pages.
    """
    media_names_sorted = sorted(MEDIA_INFO.keys())
    last_5_by_media = {}
    for media_name in media_names_sorted:
        media_videos = VIDEOS_BY_MEDIA.get(media_name, [])
        last_5_by_media[media_name] = media_videos[:5]
    return dict(media_names_sorted=media_names_sorted, last_5_by_media=last_5_by_media)

@app.route('/')
def home():
    """
    Page d'accueil :
    - Affiche les 12 dernières vidéos (tous médias confondus)
    - Affiche 10 dernières vidéos par orientation (Gauche, Centre, Droite, Autres)
    La barre latérale (déployable) est affichée depuis le template de base.
    """
    all_videos = []
    for media_name, videos in VIDEOS_BY_MEDIA.items():
        for video in videos:
            all_videos.append({
                "media_name": media_name,
                "title": video["title"],
                "link": video["link"],
                "published": video["published"],
                "thumbnail": video["thumbnail"],
                "orientation": MEDIA_INFO[media_name]["orientation"]
            })
    all_videos.sort(key=lambda x: x["published"], reverse=True)
    last_12_videos = all_videos[:12]

    videos_by_orientation = {"Gauche": [], "Centre": [], "Droite": [], "Autres": []}
    for vid in all_videos:
        orientation = vid["orientation"]
        if orientation in videos_by_orientation:
            videos_by_orientation[orientation].append(vid)
        else:
            videos_by_orientation["Autres"].append(vid)
    for orientation in videos_by_orientation:
        videos_by_orientation[orientation] = videos_by_orientation[orientation][:10]

    return render_template('index.html',
                           last_12_videos=last_12_videos,
                           videos_by_orientation=videos_by_orientation)

@app.route('/media/<media_name>')
def media_page(media_name):
    """
    Page spécifique à un média.
    Affiche les informations détaillées (orientation, PDG, description, intérêts économiques)
    et la liste complète (ou en partie) des vidéos du média.
    La barre latérale reste identique à celle définie dans le template de base.
    """
    info = MEDIA_INFO.get(media_name, {})
    orientation = info.get("orientation", "Inconnu")
    pdg = info.get("pdg", "Inconnu")
    description = info.get("description", "")
    interets_eco = info.get("interets_economiques", "")
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
    Route pour rafraîchir manuellement les flux RSS.
    """
    fetch_videos_for_all_medias()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
