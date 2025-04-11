# -----------------------------------------
# Fichier : app.py
# -----------------------------------------
import os
import json
import feedparser
from flask import Flask, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Chargement du fichier JSON contenant la configuration des médias
with open('media_data.json', 'r', encoding='utf-8') as f:
    MEDIA_INFO = json.load(f)

# Dictionnaire pour stocker les vidéos récupérées pour chaque média
VIDEOS_BY_MEDIA = {}

def fetch_videos_for_all_medias():
    """
    Récupère les vidéos via les flux RSS de chaque média.
    Stocke le résultat dans VIDEOS_BY_MEDIA sous forme de listes triées par date décroissante.
    """
    global VIDEOS_BY_MEDIA
    VIDEOS_BY_MEDIA = {}

    for media_name, info in MEDIA_INFO.items():
        flux_url = info.get('flux')
        if flux_url:
            feed = feedparser.parse(flux_url)
            media_videos = []
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                published_parsed = entry.published_parsed
                if published_parsed:
                    published_date = datetime(*published_parsed[:6])
                else:
                    published_date = datetime.now()
                
                # Extraction de l'ID de la vidéo pour générer la miniature
                video_id = None
                if "watch?v=" in link:
                    video_id = link.split("watch?v=")[1]
                
                thumbnail_url = None
                if video_id:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                
                video_data = {
                    "title": title,
                    "link": link,
                    "published": published_date,
                    "thumbnail": thumbnail_url
                }
                media_videos.append(video_data)
            
            # Tri des vidéos par date décroissante
            media_videos.sort(key=lambda x: x["published"], reverse=True)
            VIDEOS_BY_MEDIA[media_name] = media_videos

# Premier chargement des flux vidéos
fetch_videos_for_all_medias()

@app.context_processor
def inject_sidebar_data():
    """
    Fournit à tous les templates la liste des médias triés alphabétiquement 
    et leurs 5 dernières vidéos, afin d'afficher une barre latérale uniforme sur toutes les pages.
    """
    media_names_sorted = sorted(MEDIA_INFO.keys())
    last_5_by_media = {}
    for media_name in media_names_sorted:
        last_5_by_media[media_name] = VIDEOS_BY_MEDIA.get(media_name, [])[:5]
    return dict(media_names_sorted=media_names_sorted, last_5_by_media=last_5_by_media)

@app.route('/')
def home():
    """
    Page d'accueil :
    - Affiche les 12 dernières vidéos (tous médias confondus) en grille.
    - Affiche les vidéos par orientation (Gauche, Centre, Droite, Autres) en 4 colonnes.
    """
    all_videos = []
    for media_name, videos in VIDEOS_BY_MEDIA.items():
        orientation = MEDIA_INFO[media_name]["orientation"]
        for vid in videos:
            all_videos.append({
                "media_name": media_name,
                "orientation": orientation,
                "title": vid["title"],
                "link": vid["link"],
                "published": vid["published"],
                "thumbnail": vid["thumbnail"]
            })
    
    # Tri global par date décroissante
    all_videos.sort(key=lambda x: x["published"], reverse=True)
    
    # Sélection des 12 dernières vidéos
    last_12_videos = all_videos[:12]
    
    # Regroupement en 10 vidéos max par orientation
    videos_by_orientation = {
        "Gauche": [],
        "Centre": [],
        "Droite": [],
        "Autres": []
    }
    for vid in all_videos:
        ori = vid["orientation"]
        if ori in videos_by_orientation:
            videos_by_orientation[ori].append(vid)
        else:
            videos_by_orientation["Autres"].append(vid)
    
    for ori in videos_by_orientation:
        videos_by_orientation[ori] = videos_by_orientation[ori][:10]
    
    return render_template('index.html',
                           last_12_videos=last_12_videos,
                           videos_by_orientation=videos_by_orientation)

@app.route('/media/<media_name>')
def media_page(media_name):
    """
    Page spécifique à un média.
    Affiche ses informations détaillées et la liste complète de ses vidéos.
    """
    info = MEDIA_INFO.get(media_name, {})
    orientation = info.get("orientation", "Inconnu")
    pdg = info.get("pdg", "Inconnu")
    description = info.get("description", "")
    interets = info.get("interets_economiques", "")
    media_videos = VIDEOS_BY_MEDIA.get(media_name, [])
    
    return render_template('media.html',
                           media_name=media_name,
                           orientation=orientation,
                           pdg=pdg,
                           description=description,
                           interets_economiques=interets,
                           media_videos=media_videos)

@app.route('/refresh')
def refresh_feeds():
    """
    Permet de rafraîchir manuellement les flux RSS.
    """
    fetch_videos_for_all_medias()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
