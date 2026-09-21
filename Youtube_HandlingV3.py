from pytubefix import YouTube
from moviepy import AudioFileClip
from pathlib import Path

TEMP_DIR = Path(__file__).resolve().parent / "YouTuber Downloader" / "Temp files"

#Set yt(our main variable) to None, so we can use "user_link", from MainV2 as our link.
yt=None
def load_video(user_link):
    global yt
    yt = YouTube(user_link)

#We find the avaliable resolutions, the very bottom "key=lambda" function, makes sure its ints so we can actually sort through it
#otherwise Python defaults to a string, meaning our "highest number" would always be 720p, this ensures that we get the actual highest number
def get_available_resolutions():
    video_streams = yt.streams.filter(
        file_extension="mp4", only_video=True
    )
    return sorted(
        {
            stream.resolution
            for stream in video_streams
            if stream.resolution
        },
        key=lambda resolution: int(resolution.removesuffix("p")),
        reverse=True,
    )


#We match the user resolution (which we get the from the dropdown menu in MainV2) to the avaliable resolutions and
#set it as our used resolution. If for some reason it doesn't exist, we default to the max avaliable resolution. 
def get_resolution(user_res=""):
    video_streams =yt.streams.filter(file_extension="mp4", only_video=True).order_by('resolution').desc()

    available_resolutions = {
        stream.resolution
        for stream in video_streams
        if stream.resolution
    }
    #This down here is effectively just a failsafe, it should ALWAYS be avliable as we use the same list for the dropdown menu.
    requested_resolution = user_res or None
    if requested_resolution not in available_resolutions:
        selected_resolution=max(available_resolutions, key=lambda resolution: int(resolution.removesuffix("p")))
    else:
        selected_resolution=requested_resolution
    return video_streams.filter(res=selected_resolution).first()

#We get the highest quality audio stream, we only get that one as audio is so small we might as well just use the best we can.
def get_audio():
    audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
    return audio_stream

#Pretty simple, we just get the various video details.
def get_video_info():
    title=yt.title
    thumbnail=yt.thumbnail_url
    channel=yt.author
    length=yt.length
    return title, thumbnail, channel, length


#We download the video stream with the resolution we set earlier. And if for some reason, some how that res doesn't exist, we throw an error code.
def download_video(user_resolution):
    video_stream = get_resolution(user_resolution)
    if video_stream is None:
        raise ValueError(f"No video stream found for {user_resolution}")
    #We download it to a temp folder so Moviepy can process it later
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return video_stream.download(
        output_path=str(TEMP_DIR),
        filename="video.mp4",
    )
#Same down here, we download our audio stream and send it to a temp folder.
def download_audio(audio_format="m4a", output_path=None):
    audio_stream = get_audio()
    if audio_stream is None:
        raise ValueError("No audio stream found")

    if output_path is None:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return audio_stream.download(
            output_path=str(TEMP_DIR),
            filename="audio.mp4",
        )
    #From here and down its just to choose what audio format you want to use as the user if you just want the audio.
    if audio_format == "m4a":
        output_path = Path(output_path)
        return audio_stream.download(
            output_path=str(output_path.parent),
            filename=output_path.name,
        )

    temporary_audio_path = audio_stream.download(
        output_path=str(TEMP_DIR),
        filename="audio.mp4",
    )
    audio_clip = AudioFileClip(temporary_audio_path)
    try:
        audio_clip.write_audiofile(output_path)
    finally:
        audio_clip.close()
        Path(temporary_audio_path).unlink()

    return output_path
    