import os

from pytubefix import YouTube
from pytubefix.cli import on_progress


def get_video_streams(user_link, user_res=None):
    video_link = YouTube(user_link, on_progress_callback=on_progress)
    resolutions = [
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
        .desc()
    )

    available_resolutions = {
        stream.resolution
        for stream in video_streams
        if stream.resolution
    }
    matching_resolutions = [
        resolution
        for resolution in resolutions
        if resolution in available_resolutions
    ]

    requested_resolution = f"{user_res}p" if user_res else None
    if requested_resolution in available_resolutions:
        selected_resolution = requested_resolution
    else:
        selected_resolution = max(
            available_resolutions,
            key=lambda resolution: int(resolution.removesuffix("p")),
        )

    print(f"Available resolutions: {matching_resolutions}")
    return video_streams.filter(res=selected_resolution)
from pytubefix import YouTube
from pytubefix.cli import on_progress


def get_video_res_info(user_link, progress_callback=None):
    video = YouTube(
        user_link,
        on_progress_callback=progress_callback or on_progress,
    )
    video_streams = (
        video.streams
        .filter(file_extension="mp4", only_video=True)
        .order_by("resolution")
        .desc()
    )

    available_resolutions = sorted(
        {
            stream.resolution
            for stream in video_streams
            if stream.resolution
        },
        key=lambda resolution: int(resolution.removesuffix("p")),
        reverse=True,
    )

    return video, video_streams, available_resolutions


def get_video_stream(video_streams, resolution):
    return video_streams.filter(res=resolution).first()


def download_video(video, video_streams, resolution, output_path, progress_callback=None):
    video_stream = get_video_stream(video_streams, resolution)
    if video_stream is None:
        raise ValueError(f"No video stream found for resolution {resolution}")

    video_stream.download(
        output_path="YouTuber Downloader\\Temp files",
        filename="video.mp4",
    )
    download_audio(video, progress_callback=progress_callback)
    return output_path


def download_audio(video, output_path=None, progress_callback=None):
    audio_stream = (
        video.streams
        .filter(only_audio=True, file_extension="mp4")
        .order_by("abr")
        .desc()
        .first()
    )
    if audio_stream is None:
        raise ValueError("No audio stream found")

    if output_path:
        return audio_stream.download(
            output_path=os.path.dirname(output_path) or ".",
            filename=os.path.basename(output_path),
        )

    return audio_stream.download(
        output_path="YouTuber Downloader\\Temp files",
        filename="audio.mp4",
    )


def video_info(user_link):
    video=YouTube(user_link)
    title=video.title
    thumbnail=video.thumbnail_url
    return title, thumbnail

    





