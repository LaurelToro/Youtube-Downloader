# Source - https://stackoverflow.com/a/16996475
# Posted by 7stud, modified by community. See post 'Timeline' for change history
# Retrieved 2026-09-16, License - CC BY-SA 3.0

import tkinter as tk

root = tk.Tk()
root.geometry("300x200")

def func(event):
    print("You hit return.")
root.bind('<Return>', func)

def onclick():
    print("You clicked the button")

button = tk.Button(root, text="click me", command=onclick)
button.pack()

root.mainloop()
