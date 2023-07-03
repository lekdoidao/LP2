#2 - Programa para calcular a massa de ar de um pneu de automóvel:
P = float(input("Digite a pressão do pneu: "))
V = float(input("Digite o volume do pneu: "))
T = float(input("Digite a temperatura do pneu: "))

M = (P * V) / (0.37 * (T + 460))
print(f"A massa de ar do pneu é: {M:.2f} kg")
