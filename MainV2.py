"""Tkinter user interface for loading and downloading YouTube videos."""

import tkinter as tk
import re
import threading
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from datetime import timedelta
from io import BytesIO
from urllib.request import urlopen
from PIL import Image, ImageTk
import Youtube_HandlingV2 as youtube_handler
import Write_FileV2 as file_writer

# Shared state used by worker threads, GUI callbacks, and displayed widgets.
thumbnail_image = None
video_title = ""


def get_youtube_link():
    """Validate the URL field and start loading video metadata in a worker."""
    # Read the Text widget without including its trailing newline.
    user_link = youtube_link.get("1.0", "end-1c").strip()
    if not user_link:
        return

    # Prevent duplicate requests while the current video is being inspected.
    submit_btn.config(state="disabled")
    download_button.config(state="disabled")
    status_label.config(text="Loading video details...")

    # Network work must stay off the Tkinter thread so the window remains responsive.
    threading.Thread(
        target=load_video_in_background,
        args=(user_link,),
        daemon=True,
    ).start()


def load_video_in_background(user_link):
    """Fetch metadata, thumbnail, and available resolutions off the GUI thread."""
    try:
        # Load the YouTube object before requesting its metadata and streams.
        youtube_handler.load_video(user_link)
        title, thumbnail_url, channel, length, published = (
            youtube_handler.get_video_info()
        )

        # Download and resize the thumbnail before handing it back to Tkinter.
        with urlopen(thumbnail_url) as response:
            thumbnail = Image.open(BytesIO(response.read()))
        thumbnail.thumbnail((240, 135))
        available_resolutions = youtube_handler.get_available_resolutions()

        # GUI widgets may only be updated on Tkinter's main thread.
        root.after(
            0,
            lambda: show_video_details(
                title,
                thumbnail,
                channel,
                length,
                published,
                available_resolutions,
            ),
        )
    except Exception as error:
        # Convert worker failures into a safe GUI-thread callback.
        root.after(0, lambda error=error: finish_loading(error))


def show_video_details(title, thumbnail, channel, length, published, resolutions):
    """Populate the preview area and enable valid download choices."""
    global thumbnail_image, video_title

    # Keep the title for the save dialog and update the visible metadata.
    video_title = title
    title_label.config(text=title)
    channel_label.config(text=f"Channel: {channel}")
    duration_label.config(text=f"Duration: {timedelta(seconds=length)}")
    published_label.config(text=f"Uploaded: {published:%Y-%m-%d}")

    # Tkinter needs both GUI-thread creation and a retained image reference.
    thumbnail_image = ImageTk.PhotoImage(thumbnail)
    thumbnail_label.config(image=thumbnail_image)

    # A video without resolutions cannot be downloaded in video mode.
    resolution_menu["values"] = resolutions
    if resolutions:
        resolution_menu.current(0)
        resolution_menu.config(state="readonly")
        download_button.config(state="normal")
        check_resolution_warning()

    finish_loading()


def finish_loading(error=None):
    """Restore the controls after metadata loading succeeds or fails."""
    submit_btn.config(state="normal")
    if error:
        status_label.config(text=f"Could not load video: {error}")
    else:
        status_label.config(text="Video ready")


def toggle_audio_mode():
    """Switch between video-resolution and audio-format controls."""
    if audio_only.get():
        # Audio-only downloads do not need a video resolution.
        resolution_menu.config(state="disabled")
        audio_format_menu.config(state="readonly")
        download_button.config(text="Download audio")
        warning_label.config(text="")
    else:
        # Restore video controls when audio-only mode is unchecked.
        audio_format_menu.config(state="disabled")
        if resolution_menu["values"]:
            resolution_menu.config(state="readonly")
        download_button.config(text="Download selected video")
        check_resolution_warning()


def check_resolution_warning(event=None):
    """Show a warning when video processing may be especially CPU intensive."""
    resolution = resolution_menu.get()
    if not resolution or audio_only.get():
        warning_label.config(text="")
        return

    # Resolution labels are stored as strings such as "1080p".
    resolution_value = int(resolution.removesuffix("p"))
    if resolution_value > 1080:
        warning_label.config(
            text=(
                "This program is CPU intensive. Downloads above 1080p "
                "may slow down your PC while processing."
            )
        )
    else:
        warning_label.config(text="")

def download_selected_video():
    """Open the save dialog and start the selected download in a worker."""
    if audio_only.get():
        # Audio mode uses the chosen output format and does not require merging.
        audio_format = audio_format_menu.get()
        if not audio_format:
            return

        # Remove characters that Windows does not allow in filenames.
        safe_title = re.sub(r'[<>:"/\\|?*]', "_", video_title).strip()
        safe_title = safe_title or "audio"
        output_path = asksaveasfilename(
            title="Save audio as",
            initialfile=f"{safe_title}.{audio_format}",
            defaultextension=f".{audio_format}",
            filetypes=[(f"{audio_format.upper()} audio", f"*.{audio_format}")],
        )
        if not output_path:
            return

        start_download("Downloading audio...")
        threading.Thread(
            target=download_audio_in_background,
            args=(audio_format, output_path),
            daemon=True,
        ).start()
        return

    resolution = resolution_menu.get()
    if not resolution:
        return

    # Video downloads always use an MP4 output file.
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", video_title).strip()
    safe_title = safe_title or "video"

    output_path = asksaveasfilename(
        title="Save video as",
        initialfile=f"{safe_title}.mp4",
        defaultextension=".mp4",
        filetypes=[("MP4 video", "*.mp4")],
    )
    if not output_path:
        return
    start_download("Downloading video and audio...")
    threading.Thread(
        target=download_video_in_background,
        args=(resolution, output_path),
        daemon=True,
    ).start()


def start_download(message):
    """Disable conflicting controls and show the current operation."""
    download_button.config(state="disabled")
    submit_btn.config(state="disabled")
    status_label.config(text=message)


def download_audio_in_background(audio_format, output_path):
    """Download audio and report the result back on the GUI thread."""
    try:
        youtube_handler.download_audio(audio_format, output_path)
        root.after(0, lambda: finish_download("Audio download complete"))
    except Exception as error:
        # Keep exceptions from a worker thread from terminating the application.
        root.after(0, lambda error=error: finish_download(f"Download failed: {error}"))


def download_video_in_background(resolution, output_path):
    """Download video and audio, then combine them into the selected output file."""
    try:
        # MoviePy needs separate temporary video and audio files before merging.
        youtube_handler.download_video(resolution)
        youtube_handler.download_audio()
        root.after(0, lambda: status_label.config(text="Combining video and audio..."))
        file_writer.combine_video_audio(output_path)
        root.after(0, lambda: finish_download("Download complete"))
    except Exception as error:
        # Route download and merge errors back to the main event loop.
        root.after(0, lambda error=error: finish_download(f"Download failed: {error}"))


def finish_download(message):
    """Restore controls and show the result of the download."""
    download_button.config(state="normal")
    submit_btn.config(state="normal")
    status_label.config(text=message)


# ---------------------------------------------------------------------------
# Window and visual styling
# ---------------------------------------------------------------------------
# Create the root window before defining widgets and callbacks that use it.
root = tk.Tk()
root.geometry("760x760")
root.title("YouTube Downloader")
root.resizable(True, True)
root.minsize(700, 700)

# Centralize the colors so the entire interface uses one visual palette.
BACKGROUND = "#f3f0ea"
SURFACE = "#ffffff"
TEXT = "#202124"
MUTED = "#6b6f76"
ACCENT = "#d14b35"
ACCENT_ACTIVE = "#b83d2a"
BORDER = "#e4e0d8"

root.configure(bg=BACKGROUND)

# Put the remaining interface inside this canvas so content can extend below the window.
scroll_canvas = tk.Canvas(root, bg=BACKGROUND, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=scroll_canvas.yview)
scrollable_frame = ttk.Frame(scroll_canvas)
scrollable_window = scroll_canvas.create_window(
    (0, 0), window=scrollable_frame, anchor="nw"
)

# Recalculate the scrollable area whenever widgets change the content height.
scrollable_frame.bind(
    "<Configure>",
    lambda event: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
)
# Keep the content width aligned with the visible canvas width.
scroll_canvas.bind(
    "<Configure>",
    lambda event: scroll_canvas.itemconfigure(scrollable_window, width=event.width),
)
scroll_canvas.configure(yscrollcommand=scrollbar.set)
scroll_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
# Support the standard Windows mouse wheel gesture in addition to the scrollbar.
root.bind_all(
    "<MouseWheel>",
    lambda event: scroll_canvas.yview_scroll(-int(event.delta / 120), "units"),
)

# Use ttk's clam theme so controls share a consistent appearance across systems.
style = ttk.Style(root)
style.theme_use("clam")
style.configure("TFrame", background=BACKGROUND)
style.configure("Surface.TFrame", background=SURFACE)
style.configure(
    "Title.TLabel",
    background=BACKGROUND,
    foreground=TEXT,
    font=("Segoe UI", 25, "bold"),
)
style.configure(
    "Subtitle.TLabel",
    background=BACKGROUND,
    foreground=MUTED,
    font=("Segoe UI", 10),
)
style.configure(
    "Section.TLabel",
    background=SURFACE,
    foreground=TEXT,
    font=("Segoe UI", 10, "bold"),
)
style.configure(
    "Primary.TButton",
    background=ACCENT,
    foreground="#ffffff",
    font=("Segoe UI", 10, "bold"),
    padding=(18, 9),
    borderwidth=0,
)
style.map("Primary.TButton", background=[("active", ACCENT_ACTIVE)])
style.configure(
    "TCombobox",
    fieldbackground="#fafafa",
    background="#fafafa",
    foreground=TEXT,
    padding=6,
)

# ---------------------------------------------------------------------------
# Header and URL input
# ---------------------------------------------------------------------------
# Show the application name and a short description at the top of the form.
header = ttk.Frame(scrollable_frame)
header.pack(fill="x", padx=42, pady=(30, 18))
ttk.Label(header, text="YouTube Downloader", style="Title.TLabel").pack(anchor="w")
ttk.Label(
    header,
    text="Download any YouTube video as an MP4 file, or just the audio!",
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(4, 0))

# Group the URL field and its submit button on a white surface.
input_panel = ttk.Frame(scrollable_frame, style="Surface.TFrame", padding=20)
input_panel.pack(fill="x", padx=42)
ttk.Label(input_panel, text="Video URL", style="Section.TLabel").pack(anchor="w")

# Use a Text widget so the input can be read with Tkinter's text range API.
youtube_link = tk.Text(
    input_panel,
    height=1,
    font=("Segoe UI", 10),
    relief="flat",
    bd=0,
    bg="#fafafa",
    fg=TEXT,
    insertbackground=TEXT,
    padx=9,
    pady=8,
)
youtube_link.pack(fill="x", pady=(8, 12))

# Start metadata loading when the user submits the URL.
submit_btn = ttk.Button(
    input_panel,
    text="Load video",
    command=get_youtube_link,
    style="Primary.TButton",
)
submit_btn.pack(anchor="e")

# ---------------------------------------------------------------------------
# Video preview and metadata
# ---------------------------------------------------------------------------
# This panel is filled after the background metadata request succeeds.
details_frame = ttk.Frame(scrollable_frame, style="Surface.TFrame", padding=20)
details_frame.pack(fill="x", padx=42, pady=18)

# Reserve space for the downloaded thumbnail.
thumbnail_label = tk.Label(details_frame, bg=SURFACE)
thumbnail_label.grid(row=0, column=0, rowspan=4, padx=(0, 18))

# Keep text metadata aligned beside the thumbnail.
metadata_frame = ttk.Frame(details_frame, style="Surface.TFrame")
metadata_frame.grid(row=0, column=1, sticky="nw")

title_label = tk.Label(
    metadata_frame,
    text="Load a video to see its details",
    bg=SURFACE,
    fg=TEXT,
    font=("Segoe UI", 14, "bold"),
    justify="left",
    wraplength=430,
)
title_label.pack(anchor="w", pady=(0, 10))

channel_label = tk.Label(metadata_frame, text="", bg=SURFACE, fg=MUTED, font=("Segoe UI", 10))
channel_label.pack(anchor="w", pady=2)
duration_label = tk.Label(metadata_frame, text="", bg=SURFACE, fg=MUTED, font=("Segoe UI", 10))
duration_label.pack(anchor="w", pady=2)
published_label = tk.Label(metadata_frame, text="", bg=SURFACE, fg=MUTED, font=("Segoe UI", 10))
published_label.pack(anchor="w", pady=2)

# ---------------------------------------------------------------------------
# Output options and download status
# ---------------------------------------------------------------------------
# Present video and audio choices in one compact options panel.
options_panel = ttk.Frame(scrollable_frame, style="Surface.TFrame", padding=20)
options_panel.pack(fill="x", padx=42)

# Video mode: the user chooses one of the available video resolutions.
resolution_column = ttk.Frame(options_panel, style="Surface.TFrame")
resolution_column.grid(row=0, column=0, sticky="w")
ttk.Label(resolution_column, text="Video resolution", style="Section.TLabel").pack(anchor="w")
resolution_menu = ttk.Combobox(resolution_column, state="disabled", width=18)
resolution_menu.pack(anchor="w", pady=(8, 0))
resolution_menu.bind("<<ComboboxSelected>>", check_resolution_warning)

# Audio mode: checking this disables video resolution and enables audio format.
audio_only = tk.BooleanVar(value=False)
audio_checkbox = tk.Checkbutton(
    options_panel,
    text="Audio only",
    variable=audio_only,
    command=toggle_audio_mode,
    bg=SURFACE,
    fg=TEXT,
    activebackground=SURFACE,
    activeforeground=TEXT,
    selectcolor=SURFACE,
    font=("Segoe UI", 10),
)
audio_checkbox.grid(row=0, column=1, padx=(55, 10), sticky="w")

audio_format_menu = ttk.Combobox(
    options_panel,
    state="disabled",
    values=("m4a", "mp3", "wav"),
    width=10,
)
audio_format_menu.grid(row=0, column=2, sticky="w", pady=(22, 0))
audio_format_menu.current(0)

options_panel.columnconfigure(3, weight=1)

# Warn about the extra processing cost of high-resolution downloads.
warning_label = tk.Label(
    options_panel,
    text="",
    bg="#fff3cd",
    fg="#735c18",
    font=("Segoe UI", 9),
    justify="left",
    wraplength=620,
    padx=10,
    pady=7,
)
warning_label.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(16, 0))

# Keep the save button and status text together on one row.
download_row = ttk.Frame(scrollable_frame, style="Surface.TFrame")
download_row.pack(fill="x", padx=42, pady=(18, 5))
download_row.columnconfigure(0, weight=1)

status_label = tk.Label(
    download_row,
    text="Ready",
    bg=BACKGROUND,
    fg=TEXT,
    font=("Segoe UI", 10, "bold"),
    anchor="e",
)
status_label.grid(row=0, column=0, sticky="ew", pady=(20, 0))

# Start either the audio-only download or the video-plus-audio workflow.
download_button = ttk.Button(
    download_row,
    text="Download selected video",
    command=download_selected_video,
    state="disabled",
    style="Primary.TButton",
)
download_button.grid(row=0, column=1, padx=(16, 0), pady=(20, 0), sticky="e")

# Enter Tkinter's event loop so user input, timers, and worker callbacks are handled.
root.mainloop()