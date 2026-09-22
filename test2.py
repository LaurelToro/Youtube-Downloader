from pytubefix import Playlist
from pytubefix.cli import on_progress

url = input("url here >")

pl = Playlist(url)

for video in pl.videos:
    print(video.title)
