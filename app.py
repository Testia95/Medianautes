# -----------------------------------------
# Fichier : app.py
# -----------------------------------------
import os
import json
import feedparser
from flask import Flask, render_template, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Chargement des infos médias
with open('media_data.json', 'r', encoding='utf-8') as f:
    MEDIA_INFO = json.load(f)

# Dictionnaire contenant les vidéos récupérées pour chaque média
VIDEOS_BY_MEDIA = {}

def fetch_videos_for_all_medias():
    """
    Récupère les vidéos de chaque média via feedparser.
    Stocke le résultat dans VIDEOS_BY_MEDIA sous forme de listes triées par date.
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

                # Convertir published_parsed en datetime pour faciliter le tri
                if published_parsed:
                    published_date = datetime(*published_parsed[:6])
                else:
                    published_date = datetime.now()

                # Extraire l'ID vidéo pour la miniature
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
            
            # Tri par date décroissante
            media_videos.sort(key=lambda x: x["published"], reverse=True)
            VIDEOS_BY_MEDIA[media_name] = media_videos

# Premier remplissage
fetch_videos_for_all_medias()

@app.context_processor
def inject_sidebar_
