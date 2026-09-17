import tkinter as tk
import threading
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from io import BytesIO
from urllib.request import urlopen

from PIL import Image, ImageTk

import youtube_handling


video_streams = None
video = None
thumbnail_image = None



def save_video():
    if video is None or video_streams is None:
        return

    only_audio = check_audio.get() == 1
    if not only_audio and not resolution_menu.get():
        return

    output_path = asksaveasfilename(
        filetypes=[("MP4 audio" if only_audio else "MP4 video", "*.mp4")],
        defaultextension=".mp4",
        title="Save audio as" if only_audio else "Save video as",
    )
    if not output_path:
        return

    save_video_file.config(state="disabled")
    threading.Thread(
        target=download_in_background,
        args=(output_path, resolution_menu.get(), only_audio),
        daemon=True,
    ).start()


def update_download_progress(stage, fraction):
    fraction = max(0, min(1, fraction))
    root.after(0, lambda: progress_bar.config(value=fraction * 100))
    root.after(0, lambda: progress_label.config(text=f"{stage}: {fraction:.0%}"))


def pytube_progress(stream, chunk, bytes_remaining):
    total = getattr(stream, "filesize", None) or getattr(stream, "filesize_approx", 0)
    if not total:
        return

    downloaded = total - bytes_remaining
    is_audio = (
        getattr(stream, "includes_audio_track", False)
        and not getattr(stream, "includes_video_track", False)
    )
    update_download_progress("Audio" if is_audio else "Video", downloaded / total)


def download_in_background(output_path, resolution, only_audio):
    try:
        if only_audio:
            youtube_handling.download_audio(video, output_path)
        else:
            youtube_handling.download_video(
                video,
                video_streams,
                resolution,
                output_path,
            )

            import write_file
            write_file.combine_video_audio(output_path, update_download_progress)
        root.after(0, lambda: progress_label.config(text="Finished"))
    except Exception as error:
        root.after(0, lambda: progress_label.config(text=f"Error: {error}"))
    finally:
        root.after(0, lambda: save_video_file.config(state="normal"))

def get_input_text():
    global video, video_streams, thumbnail_image

    youtube_link_input = youtube_link_.get("1.0", "end-1c").strip()
    if not youtube_link_input:
        return

    video, video_streams, available_resolutions = youtube_handling.get_video_res_info(
        youtube_link_input,
        pytube_progress,
    )
    title = video.title
    thumbnail_url = video.thumbnail_url
    title_label.config(text=title)

    with urlopen(thumbnail_url) as response:
        thumbnail = Image.open(BytesIO(response.read()))
    thumbnail.thumbnail((480, 270))
    thumbnail_image = ImageTk.PhotoImage(thumbnail)
    thumbnail_label.config(image=thumbnail_image)

    resolution_menu["values"] = available_resolutions
    if available_resolutions:
        resolution_menu.current(0)
        resolution_menu.config(state="readonly")

root = tk.Tk()
root.geometry("700x500")
root.title("Test")
root.resizable(False, False)
check_audio = tk.IntVar(master=root, value=0)


label= tk.Label(root, text="YouTube Downloader")
label.config(font=("Helvetica", 14, "bold"))
label.pack()

youtube_link_text = tk.Label(root, text="Indtast dit link her")
youtube_link_text.pack()

audio_checkbox = tk.Checkbutton(
    root,
    text="Only audio",
    variable=check_audio,
    onvalue=1,
    offvalue=0,
)
audio_checkbox.pack()

youtube_link_ = tk.Text(root,height=1, width=40)
youtube_link_.pack()

send_link = tk.Button(root, text="Use link", command=get_input_text)
send_link .pack()

resolution_menu = ttk.Combobox(root, state="disabled")
resolution_menu.pack()

title_label = tk.Label(root, text="")
title_label.pack()

thumbnail_label = tk.Label(root)
thumbnail_label.pack()

save_video_file=tk.Button(root, text="Save video as", command=save_video)
save_video_file.pack()

progress_bar = ttk.Progressbar(root, length=300, mode="determinate")
progress_bar.pack(pady=20)

progress_label = tk.Label(root, text="")
progress_label.pack()

root.mainloop()

