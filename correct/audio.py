from gtts import gTTS
text_to_speak = "Your Outpass has been issued successfully."
language = 'en'
audio_path = 'outpass_notification.mp3'
tts = gTTS(text=text_to_speak, lang=language, slow=False)
tts.save(audio_path)
print("yesss")

