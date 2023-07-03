#2 - Programa para trocar os valores de três variáveis:
a = 1
b = 2
c = 3

# Trocar os valores entre as variáveis usando uma variável temporária
temp = a
a = c
c = b
b = temp

print("A =", a)
print("B =", b)
print("C =", c)