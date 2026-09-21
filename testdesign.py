import sys
import re
from urllib.request import urlopen
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog
import test1 as yt_handler
import Write_FileV2 as file_writer
app = QtWidgets.QApplication(sys.argv)

window = uic.loadUi("YouTube Downloader.ui")

def get_user_link():
    return window.lineEdit.text().strip()

def load_video_resolution():
    user_link = get_user_link()
    yt_handler.load_video(user_link)
    resolutions = yt_handler.get_available_resolutions()
    window.comboBox.clear()
    window.comboBox.addItems(resolutions)

def print_text():
    title, channel, length, thumbnail_url = yt_handler.get_video_info(yt_handler.yt)
    title = "Title: " + title
    channel = "Channel: " + channel
    window.label.setText(title)
    window.label_2.setText(channel)
    window.label_4.setText(str(length))
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
    load_video_resolution()
    print_text()
def download_video():
    if yt_handler.yt is None:
        load_video_resolution()

    user_res = window.comboBox.currentText()
    if not user_res:
        return

    safe_title = re.sub(r'[<>:"/\\|?*]', "", yt_handler.yt.title)
    safe_title = safe_title.strip().rstrip(".") or "video"

    output_path, _ = QFileDialog.getSaveFileName(
        window,
        "Save video",
        f"{safe_title}.mp4",
        "MP4 files (*.mp4)",
    )
    if not output_path:
        return

    yt_handler.download_video(user_res)
    yt_handler.download_audio()
    file_writer.combine_video_audio(output_path)



window.lineEdit.returnPressed.connect(submit_url)
window.pushButton.clicked.connect(download_video)
window.show()
sys.exit(app.exec())