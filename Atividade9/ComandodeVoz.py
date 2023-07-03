import speech_recognition as sr
import pyttsx3

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Diga algo...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="pt-BR")
        print("Você disse:", text)
        return text.lower()
    except sr.UnknownValueError:
        print("Não foi possível entender.")
        return ""
    except sr.RequestError:
        print("Erro ao acessar o serviço de reconhecimento.")
        return ""

def process_command(command):
    if "olá" in command:
        return "Olá! Como posso ajudar?"
    elif "quero saber a hora" in command:
        return "Ainda não implementei essa funcionalidade. Desculpe!"
    elif "tchau" in command:
        return "Até logo!"
    else:
        return "Comando não reconhecido."

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def main():
    while True:
        command = recognize_speech()
        response = process_command(command)
        speak(response)

if __name__ == "__main__":
    main()
