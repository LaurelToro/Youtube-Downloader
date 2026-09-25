import sys
import re
from pathlib import Path
from urllib.request import urlopen
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtGui import QAction, QPixmap, QDesktopServices, QIcon
from PyQt6.QtWidgets import QFileDialog
from pytubefix import Playlist
import YouTube_HandlingV4 as yt_handler
import Write_FileV2 as file_writer
app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')
UI = Path(__file__).resolve().parent / "YouTube Downloader.ui"
icon_path= Path(__file__).resolve().parent / "app.ico"
window = uic.loadUi(UI)
window.setWindowIcon(QIcon(str(icon_path)))

class PlaylistWorker(QtCore.QObject):
    status_changed = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    failed = QtCore.pyqtSignal(str)

    def __init__(self, playlist_url, output_folder, audio_only):
        super().__init__()
        self.playlist_url = playlist_url
        self.output_folder = output_folder
        self.audio_only = audio_only

    @QtCore.pyqtSlot()
    def run(self):
        try:
            playlist = Playlist(self.playlist_url)
            videos = list(playlist.videos)
            total = len(videos)

            if total == 0:
                raise ValueError("The playlist contains no available videos")

            for number, video in enumerate(videos, start=1):
                mode = "audio" if self.audio_only else "video"
                self.status_changed.emit(
                    f"Downloading {mode} {number} of {total}: {video.title}"
                )
                if self.audio_only:
                    stream = (
                        video.streams
                        .filter(only_audio=True)
                        .order_by("abr")
                        .desc()
                        .first()
                    )
                    extension = stream.subtype if stream else "audio"
                else:
                    stream = (
                        video.streams
                        .filter(progressive=True, file_extension="mp4")
                        .order_by("resolution")
                        .desc()
                        .first()
                    )
                    extension = "mp4"
                if stream is None:
                    stream_type = "audio" if self.audio_only else "progressive MP4"
                    raise ValueError(f"No {stream_type} stream for: {video.title}")

                title = re.sub(r'[<>:"/\\|?*]', "", video.title)
                title = title.strip().rstrip(".") or f"video-{number}"
                stream.download(
                    output_path=self.output_folder,
                    filename=f"{number:02d} - {title}.{extension}",
                )

            self.finished.emit()
        except Exception as error:
            self.failed.emit(str(error))

def get_user_link():
    return window.lineEdit.text().strip()

def set_status(message):
    window.status_update.setText(message)
    QtWidgets.QApplication.processEvents()

def load_video_resolution():
    user_link = get_user_link()
    yt_handler.load_video(
        user_link,
        oauth,
        use_oauth=window.authenticationCheckBox.isChecked(),
    )
    resolutions = yt_handler.get_available_resolutions()
    window.comboBox.clear()
    window.comboBox.addItems(resolutions)

def print_text():
    title, channel, length, thumbnail_url = yt_handler.get_video_info(yt_handler.yt)
    title = "Title:\n" + title
    channel = "Channel: " + channel
    window.label.setText(title)
    window.label_2.setText(channel)
    window.label_4.setText("Run time: "+str(length))
    show_thumbnail(thumbnail_url)

def show_thumbnail(thumbnail_url):
    image_data = urlopen(thumbnail_url).read()
    pixmap = QPixmap()
    pixmap.loadFromData(image_data)

    scene = QtWidgets.QGraphicsScene(window)
    scene.addPixmap(pixmap)
    window.graphicsView.setEnabled(True)
    window.graphicsView.setScene(scene)
    window.graphicsView.fitInView(
        scene.sceneRect(),
        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
    )

def submit_url():
    try:
        set_status("Loading video information...")
        load_video_resolution()
        if window.checkBox.isChecked():
            load_audio_streams()
        print_text()
        set_status("Ready")
    except Exception as error:
        set_status(f"Failed to load video: {error}")
        QtWidgets.QMessageBox.critical(
            window,
            "Unable to load video",
            f"The video could not be loaded:\n\n{error}",
        )

def load_audio_streams():
    audio_streams = yt_handler.get_audio_streams()
    window.comboBox.clear()
    for stream in audio_streams:
        option = f"{stream.subtype} - {stream.abr}"
        window.comboBox.addItem(option, stream)

def oauth(verification_url, user_code):
    dialog = QtWidgets.QMessageBox(window)
    dialog.setWindowTitle("YouTube Authentication")
    dialog.setText(
        f"Open this link:\n{verification_url}\n\n"
        f"Enter this code:\n{user_code}"
    )

    open_button = dialog.addButton(
        "Open Link",
        QtWidgets.QMessageBox.ButtonRole.ActionRole,
    )
    dialog.addButton(
        "Continue",
        QtWidgets.QMessageBox.ButtonRole.AcceptRole,
    )

    def open_verification_link():
        if not QDesktopServices.openUrl(QtCore.QUrl(verification_url)):
            dialog.setInformativeText("The link could not be opened automatically.")

    open_button.clicked.connect(open_verification_link)

    dialog.exec()

def download_video():
    if yt_handler.yt is None:
        load_video_resolution()
        if window.checkBox.isChecked():
            load_audio_streams()

    user_res = window.comboBox.currentText()
    if not user_res:
        return

    safe_title = re.sub(r'[<>:"/\\|?*]', "", yt_handler.yt.title)
    safe_title = safe_title.strip().rstrip(".") or "video"

    if window.checkBox.isChecked():
        selected_stream = window.comboBox.currentData()
        if selected_stream is None:
            return
        extension = selected_stream.subtype
        output_path, _ = QFileDialog.getSaveFileName(
            window,
            "Save audio",
            f"{safe_title}.{extension}",
            f"{extension.upper()} files (*.{extension})",
        )
        if not output_path:
            return
        window.pushButton.setEnabled(False)
        try:
            set_status("Downloading audio...")
            yt_handler.download_selected_audio(selected_stream, output_path)
            set_status("Download complete")
        except Exception as error:
            set_status(f"Download failed: {error}")
        finally:
            window.pushButton.setEnabled(True)
        return

    output_path, _ = QFileDialog.getSaveFileName(
        window,
        "Save video",
        f"{safe_title}.mp4",
        "MP4 files (*.mp4)",
    )
    if not output_path:
        return

    window.pushButton.setEnabled(False)
    try:
        set_status("Downloading video...")
        yt_handler.download_video(user_res)
        set_status("Downloading audio...")
        yt_handler.download_audio()
        set_status("Combining video and audio...")
        file_writer.combine_video_audio(output_path)
        set_status("Download complete")
    except Exception as error:
        set_status(f"Download failed: {error}")
    finally:
        window.pushButton.setEnabled(True)

def download_playlist():
    playlist_url = get_user_link()
    if not playlist_url:
        set_status("Enter a playlist URL first")
        return

    output_folder = QFileDialog.getExistingDirectory(
        window,
        "Choose playlist download folder",
    )
    if not output_folder:
        return

    window.pushButton.setEnabled(False)
    window.playlist_action.setEnabled(False)
    set_status("Preparing playlist...")

    thread = QtCore.QThread(window)
    worker = PlaylistWorker(
        playlist_url,
        output_folder,
        window.checkBox.isChecked(),
    )
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.status_changed.connect(set_status)
    worker.finished.connect(playlist_finished)
    worker.failed.connect(playlist_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    window.playlist_thread = thread
    window.playlist_worker = worker
    thread.start()

def playlist_finished():
    window.pushButton.setEnabled(True)
    window.playlist_action.setEnabled(True)
    set_status("Playlist download complete")

def playlist_failed(message):
    window.pushButton.setEnabled(True)
    window.playlist_action.setEnabled(True)
    set_status(f"Playlist download failed: {message}")

def audio_only(checked):
    if checked:
        if yt_handler.yt is not None:
            load_audio_streams()
    else:
        if yt_handler.yt is not None:
            load_video_resolution()

window.checkBox.toggled.connect(audio_only)
window.lineEdit.returnPressed.connect(submit_url)
window.pushButton_2.clicked.connect(submit_url)
window.pushButton.clicked.connect(download_video)
window.playlist_action = QAction("Download playlist", window)
window.menuPlaylists.addAction(window.playlist_action)
window.playlist_action.triggered.connect(download_playlist)
window.show()
sys.exit(app.exec())