from moviepy import *
import os


clip = VideoFileClip("video.mp4")

audioclip = AudioFileClip("audio.mp4")

videoclip = clip.with_audio(audioclip)

videoclip.write_videofile("finished_video.mp4")
videoclip.close
os.remove("video.mp4")
os.remove("audio.mp4")