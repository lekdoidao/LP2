import tkinter as tk
from tkinter import colorchooser


def create_ball(event):
    color = colorchooser.askcolor()[1]
    ball = canvas.create_oval(event.x - 10, event.y - 10, event.x + 10, event.y + 10, fill=color)
    drag.bind(ball, canvas)

def connect_balls():
    items = canvas.find_withtag('ball')
    for i in range(len(items) - 1):
        x1, y1, _, _ = canvas.coords(items[i])
        x2, y2, _, _ = canvas.coords(items[i + 1])
        canvas.create_line(x1, y1, x2, y2, fill='black', width=2)

root = tk.Tk()
root.title('Arraste e Conecte Bolinhas')

canvas = tk.Canvas(root, width=800, height=600, bg='white')
canvas.pack()

canvas.bind('<Button-1>', create_ball)
connect_button = tk.Button(root, text='Conectar Bolinhas', command=connect_balls)
connect_button.pack()

root.mainloop()