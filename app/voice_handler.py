import urllib.request
import librosa
import soundfile as sf
import os
import openai
from .chat_handler import process_chat_message

def transcribe_audio(audio_filepath):
    with open(audio_filepath, "rb") as audio:
        transcript = openai.Audio.transcribe("whisper-1", audio)
        return transcript["text"]

async def handle_voice_message(audio_filepath):
    # Transcribe the audio file
    transcribed_text = transcribe_audio(audio_filepath)
    print("transcribed text: " + transcribed_text)
    output = await process_chat_message(transcribed_text)
    return output

async def process_voice_message(voice_url: str):
    # Download the voice file from the URL
    voice_file = "voice_message.ogg"
    
    # Create a custom user agent to bypass any restrictions
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    headers = {"User-Agent": user_agent}
    request = urllib.request.Request(voice_url, headers=headers)

    # Download the file using the custom user agent
    with urllib.request.urlopen(request) as response:
        with open(voice_file, 'wb') as out_file:
            out_file.write(response.read())

    # Convert the OGG/Opus audio file to a supported format (e.g., 'wav')
    y, sr = librosa.load(voice_file, sr=None)
    converted_voice_file = "converted_audio.wav"
    sf.write(converted_voice_file, y, sr, format='wav', subtype='PCM_24')

    # Process the voice file (transcribe, analyze, respond, etc.)
    output = await handle_voice_message(converted_voice_file)

    # Clean up the voice files
    os.remove(voice_file)
    os.remove(converted_voice_file)

    # Return the output (text, image, etc.)
    return output
