from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy import * 
import os


video_link = YouTube(user_link,on_progress_callback=on_progress)

user_res=(input("input your preferred res: "))
new_res=user_res + "p"

resultions=[
    "2160p",
    "1440p",
    "1080p",
    "720p",
    "480p",
    "360p",
    "240p",
    "144p"
]

video_streams = (
        video_link.streams.filter(file_extension="mp4", only_video=True)
        .order_by("resolution")
        .desc())

available_resolutions = {
    stream.resolution
    for stream in video_streams
    if stream.resolution
}
matching_resolutions = [
    resolution
    for resolution in resultions
    if resolution in available_resolutions
]

print(available_resolutions)
print(matching_resolutions)

if new_res in available_resolutions:
    selected_resolution = new_res
else:
    selected_resolution = max(
        available_resolutions,
        key=lambda resolution: int(resolution.removesuffix("p")),
    )
        
print(selected_resolution)

selected_video_streams = video_streams.filter(res=selected_resolution)


#print(video_streams)
#selected_video_streams = video_streams.filter(res=newuser)
#audio_streams=(
    #video_link.streams.filter(only_audio=True).order_by("abr").desc().first()
    #)
#video_streams=video_streams.first()
#video_download=video_streams.download(filename="video.mp4")
#audio_download=audio_streams.download(filename="audio.mp4")




