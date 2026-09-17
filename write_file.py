import os
from moviepy import AudioFileClip, VideoFileClip
from proglog import ProgressBarLogger


class MoviePyProgressLogger(ProgressBarLogger):
	def __init__(self, progress_callback):
		super().__init__()
		self.progress_callback = progress_callback

	def bars_callback(self, bar, attr, value, old_value=None):
		if attr != "index":
			return

		bar_data = self.bars.get(bar, {})
		total = bar_data.get("total")
		if total:
			self.progress_callback("Combining", value / total)


def combine_video_audio(output_path, progress_callback=None):
	clip = VideoFileClip("YouTuber Downloader\\Temp files\\video.mp4")
	audioclip = AudioFileClip("YouTuber Downloader\\Temp files\\audio.mp4")
	videoclip = clip.with_audio(audioclip)

	try:
		logger = MoviePyProgressLogger(progress_callback) if progress_callback else None
		videoclip.write_videofile(output_path, logger=logger)
	finally:
		videoclip.close()
		audioclip.close()
		clip.close()
		os.remove("YouTuber Downloader\\Temp files\\video.mp4")
		os.remove("YouTuber Downloader\\Temp files\\audio.mp4")