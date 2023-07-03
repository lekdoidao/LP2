#1 - Programa para converter temperatura de graus Fahrenheit para graus Celsius:
def fahrenheit_to_celsius(fahrenheit):
    return (5/9) * (fahrenheit - 32)

def main():
    try:
        fahrenheit = float(input("Digite a temperatura em graus Fahrenheit: "))
        celsius = fahrenheit_to_celsius(fahrenheit)
        print(f"{fahrenheit:.2f} graus Fahrenheit são {celsius:.2f} graus Celsius.")
    except ValueError:
        print("Entrada inválida. Certifique-se de digitar um valor numérico válido em graus Fahrenheit.")

if __name__ == "__main__":
    main()
