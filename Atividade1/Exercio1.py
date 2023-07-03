#1 - Programa para imprimir três números em ordem inversa:
numeros = []

for i in range(3):
    numero = int(input("Digite um número: "))
    numeros.append(numero)

print("Números em ordem inversa:")
for i in range(2, -1, -1):
    print(numeros[i])
