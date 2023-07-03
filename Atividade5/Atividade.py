import tkinter as tk

def increment():
    global value
    value += 1
    label.config(text=f"Valor: {value}")

def reset():
    global value
    value = 0
    label.config(text="Valor: 0")

# Inicialização do Tkinter
root = tk.Tk()
root.title("Incrementar Valor")

# Variável para armazenar o valor
value = 0

# Rótulo para exibir o valor atual
label = tk.Label(root, text="Valor: 0")
label.pack(pady=20)

# Botão para incrementar
increment_button = tk.Button(root, text="Incrementar", command=increment)
increment_button.pack()

# Botão para zerar
reset_button = tk.Button(root, text="Zerar", command=reset)
reset_button.pack()

# Executar o loop principal do Tkinter
root.mainloop()
