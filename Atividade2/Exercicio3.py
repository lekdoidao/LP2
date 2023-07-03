#3 - Programa para calcular o N-ésimo termo de uma Progressão Aritmética (PA):
def nth_term_arithmetic_progression(a_1, r, n):
    nth_term = a_1 + (n - 1) * r
    return nth_term

def main():
    try:
        a_1 = float(input("Digite o primeiro termo da Progressão Aritmética: "))
        r = float(input("Digite a razão da Progressão Aritmética: "))
        n = int(input("Digite o valor de N (posição do termo que deseja calcular): "))

        nth_term = nth_term_arithmetic_progression(a_1, r, n)
        print(f"O {n}-ésimo termo da Progressão Aritmética é: {nth_term}")
    except ValueError:
        print("Entrada inválida. Certifique-se de digitar valores numéricos válidos.")

if __name__ == "__main__":
    main()
