import os
import azure.cognitiveservices.speech as speechsdk


def recognize_from_microphone():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ.get("SPEECH_KEY"),
        region=os.environ.get("SPEECH_REGION"),
    )
    speech_config.speech_recognition_language = "hi-IN"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )

    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return str(speech_recognition_result.text)
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print(
            "No speech could be recognized: {}".format(
                speech_recognition_result.no_match_details
            )
        )
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
import os
import azure.cognitiveservices.speech as speechsdk

speech_key, service_region = os.environ['SPEECH_KEY'], os.environ['SPEECH_REGION']
from_language, to_language = 'hi-IN', 'en'

def translate_speech_to_text():
    translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=speech_key, region=service_region)

    translation_config.speech_recognition_language = from_language
    translation_config.add_target_language(to_language)

    translation_recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config)
    
    print('Say something...')
    result = translation_recognizer.recognize_once()
    print(get_result_text(reason=result.reason, result=result))

def get_result_text(reason, result):
    print(result.text)
    print(result.translations)
    reason_format = {
        speechsdk.ResultReason.TranslatedSpeech:
            f'RECOGNIZED "{from_language}": {result.text}\n' +
            f'TRANSLATED into "{to_language}"": {result.translations[to_language]}',
        speechsdk.ResultReason.RecognizedSpeech: f'Recognized: "{result.text}"',
        speechsdk.ResultReason.NoMatch: f'No speech could be recognized: {result.no_match_details}',
        speechsdk.ResultReason.Canceled: f'Speech Recognition canceled: {result.cancellation_details}'
    }
    return reason_format.get(reason, 'Unable to recognize speech')

if __name__ == '__main__':
    result = translate_speech_to_text()
    print(result)