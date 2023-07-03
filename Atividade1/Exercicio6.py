#6 - Programa para calcular a quantidade de latas de tinta necessárias para pintar uma parede:
largura = float(input("Digite a largura da parede em metros: "))
altura = float(input("Digite a altura da parede em metros: "))

area_parede = largura * altura
quantidade_tinta_litros = area_parede * 0.3
quantidade_latas = quantidade_tinta_litros // 2

if quantidade_tinta_litros % 2 != 0:
    quantidade_latas += 1

print("Você precisará de aproximadamente", int(quantidade_latas), "latas de tinta.")