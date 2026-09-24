from pytubefix import YouTube
from pathlib import Path
from datetime import timedelta

TEMP_DIR = Path(__file__).resolve().parent / "YouTuber Downloader" / "Temp files"

yt=None

def load_video(user_link, oauth_verifier=None, use_oauth=True):
    global yt
    yt = YouTube(
        user_link,
        use_oauth=use_oauth,
        allow_oauth_cache=use_oauth,
        oauth_verifier=oauth_verifier if use_oauth else None,
    )


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

def get_resolution(user_res=""):
    video_streams = yt.streams.filter(
        file_extension="mp4",
        only_video=True,
    ).order_by("resolution").desc()

    available_resolutions = {
        stream.resolution
        for stream in video_streams
        if stream.resolution
    }

    if not available_resolutions:
        return None

    if user_res not in available_resolutions:
        user_res = max(
            available_resolutions,
            key=lambda resolution: int(resolution.removesuffix("p")),
        )

    return video_streams.filter(res=user_res).first()

def get_audio():
    audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
    return audio_stream

def get_audio_streams():
    unique_streams = {}

    for stream in yt.streams.filter(only_audio=True):
        key = (stream.subtype, stream.abr)
        if key not in unique_streams:
            unique_streams[key] = stream

    return sorted(
        unique_streams.values(),
        key=lambda stream: float(stream.abr.rstrip("kbps")),
        reverse=True,
    )

def get_video_info(yt):
    thumbnail = yt.thumbnail_url
    title = yt.title
    channel = yt.author
    length = yt.length
    length = str(timedelta(seconds=length))
    return title, channel, length, thumbnail

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

def download_audio(audio_format="m4a", output_path=None):
    audio_stream = get_audio()
    if audio_stream is None:
        raise ValueError("No audio stream found")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return audio_stream.download(
        output_path=str(TEMP_DIR),
        filename="audio.mp4",
    )

def download_selected_audio(audio_stream, output_path):
    return audio_stream.download(
        output_path=str(Path(output_path).parent),
        filename=Path(output_path).name,
    )