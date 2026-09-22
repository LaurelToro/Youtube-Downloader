from moviepy import AudioFileClip, VideoFileClip
from pathlib import Path

TEMP_DIR = Path(__file__).resolve().parent / "YouTuber Downloader" / "Temp files"


def combine_video_audio(output_path):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = TEMP_DIR / "video.mp4"
    audio_path = TEMP_DIR / "audio.mp4"
    temporary_audio_path = TEMP_DIR / "combined-audio.m4a"

    clip = VideoFileClip(str(video_path))
    audio_clip = AudioFileClip(str(audio_path))
    video_with_audio = clip.with_audio(audio_clip)
    try:
        video_with_audio.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(temporary_audio_path),
            remove_temp=True,
            logger=None,
        )
    finally:
        video_with_audio.close()
        audio_clip.close()
        clip.close()
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        temporary_audio_path.unlink(missing_ok=True)