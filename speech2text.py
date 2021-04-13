from pydub import AudioSegment
import speech_recognition as sr
import requests
from pathlib import Path

def speech2text(path):
            
    speech = AudioSegment.from_file(path)

    speech.export(path.parent.joinpath('speech.wav'), format="wav")

    recognizer = sr.Recognizer()
    command = sr.AudioFile(str(path.parent.joinpath('speech.wav')))

    with command as source:
        audio = recognizer.record(source)

    transcripts = recognizer.recognize_google(audio, show_all=True)
    for transcript in transcripts['alternative']:
        transcript['transcript'] = transcript['transcript'].lower()
    #print(transcripts)

    texts = []
    for transcript in transcripts['alternative']:
        if (transcript['transcript'][:3] == 'bot' or
            transcript['transcript'][:2] == 'hi' or
            transcript['transcript'][:3] == 'bye'):
            texts.append(transcript['transcript'])
    #print(texts)
    text = ''
    for t in texts:
        if (t[3:] == 'bot' or t[4:] == 'bot' or
            t[4:8] == 'time' or t[4:10] == 'search' or
            t[4:9] == 'timer' or t[4:9] == 'gmail' or
            t[4:13] == 'make note' or t[4:] == 'show note' or
            t[4:11] == 'youtube' or t[4:9] == 'image' or
            t[4:9] == 'audio' or t[4:8] == 'help'):
            text = t
            break

    if text:
        log = 'success'
    else:
        log = 'Unable to recognize speech.'

    return text, log


if __name__ == '__main__':
    texts, log = speech2text(Path(r'F:\PYTHON\web-automation\Luv\speech.oga'))
    print(log, texts)

##mic = sr.Microphone()
##with mic as source:
##    recognizer.adjust_for_ambient_noise(source, duration=3)
##    audio = recognizer.listen(source)

##recognizer.energy_threshold = 20 #for earphones mic
##recognizer.dynamic_energy_threshold = False #Neccessary for explicit change

##a = audio.get_wav_data()
##open('file.wav', 'wb').write(a)
