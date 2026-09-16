import tkinter as tk
from youtube_handling import *

    

def get_input_text():
    youtube_link_input=youtube_link_.get("1.0", "end-1c")
    print(youtube_link_input)

root = tk.Tk()
root.geometry("700x500")
root.title("Test")
root.resizable(False, False)


label= tk.Label(root, text="YouTube Downloader")
label.config(font=("Helvetica", 14, "bold"))
label.pack()

youtube_link_text = tk.Label(root, text="Indtast dit link her")
youtube_link_text.pack()

youtube_link_ = tk.Text(root,height=1, width=40)
youtube_link_.pack()

root.mainloop()

