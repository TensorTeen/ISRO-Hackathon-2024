from typing import Optional
import json
import os
import io
import requests
import uuid

from azure.cognitiveservices import speech as speechsdk
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models._models import InputTextItem

class Speech:
    """
    A class that represents a speech recognizer for translation.
    Args:
        from_language (str, optional): The language of the input speech. Defaults to 'hi-IN'.
        to_language (str, optional): The language to translate the speech into. Defaults to 'en'.
        config (str, optional): The path to the configuration file. Defaults to None.
    Attributes:
        from_language (str): The language of the input speech.
        to_language (str): The language to translate the speech into.
        config (dict): The configuration settings for the speech recognizer.
    Methods:
        translate(from_language, to_language): (main) Translates the speech from the input language to the target language.
        translate_speech_to_text(from_language, to_language): Translates the speech to text in the target language.
        get_result_text(reason, result, from_language, to_language): Returns the formatted result text based on the recognition reason.
    """
        
    def __init__(self) -> None:
        """
        Initializes a new instance of the SpeechRecognizer class.
        Args:
            from_language (str, optional): The language of the input speech. Defaults to 'hi-IN'.
            to_language (str, optional): The language to translate the speech into. Defaults to 'en'.
            config (str, optional): The path to the configuration file. Defaults to None.
        Raises:
            ValueError: If the target language contains a hyphen.
        """
        self.config = {
            'SPEECH_KEY': os.environ['SPEECH_KEY'],
            'SPEECH_REGION': os.environ['SPEECH_REGION'],
            'TEXT_TRANSLATION_KEY': os.environ['TEXT_TRANSLATION_KEY'],
            'endpoint': 'https://api.cognitive.microsofttranslator.com/'
        }

    def translate_text(self, text: str, from_language: str = 'en', to_language: str = 'hi'):
        """
        Translate text to text
        """
        url = f'{self.config["endpoint"]}/translate'
        params = {
            'api-version': '3.0',
            'from': from_language,
            'to': [to_language]
        }
        headers = {
            'Ocp-Apim-Subscription-Key': self.config['TEXT_TRANSLATION_KEY'],
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        body = [{
            'text': text
        }]
        request = requests.post(url, params=params, headers=headers, json=body)
        response = request.json()
        # print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))
        response = response[0]['translations'][0]['text']
        return response

    
    def recognize_from_microphone(self):
        # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
        speech_config = speechsdk.SpeechConfig(subscription=self.config['SPEECH_KEY'], region=self.config['SPEECH_REGION'])
        speech_config.speech_recognition_language="en-US"

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        speech_recognition_result = speech_recognizer.recognize_once_async().get()

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # print("Recognized: {}".format(speech_recognition_result.text))
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

    
    def translate_speech(self, from_language: str = 'hi-IN', to_language: str = 'en'):
        """
        Use this one. Translates the speech from the input language to the target language.

        Args:
            from_language (str, optional): The language of the input speech. Defaults to 'hi-IN'.
            to_language (str, optional): The language to translate the speech into. Defaults to 'en'.

        """
        if to_language.find('-') != -1:
            raise ValueError('It has to be en, not en-US, I\'m pretty sure')
        try:
            result, reason = self.translate_speech_to_text(from_language, to_language)
        except:
            print(result)
        return result, reason
    
    def translate_speech_to_text(self, from_language='hi-IN', to_language='en'):
        """
        Translates the speech to text in the target language.
        
        Args:
            from_language (str, optional): The language of the input speech. Defaults to 'hi-IN'.
            to_language (str, optional): The language to translate the speech into. Defaults to 'en'.
        """
        translation_config = speechsdk.translation.SpeechTranslationConfig(
                subscription=self.config['SPEECH_KEY'], region=self.config['SPEECH_REGION'])

        translation_config.speech_recognition_language = from_language
        translation_config.add_target_language(to_language)

        translation_recognizer = speechsdk.translation.TranslationRecognizer(
                translation_config=translation_config)
        
        result = translation_recognizer.recognize_once()
        reason = self.get_result_text(reason=result.reason, result=result, from_language=from_language, to_language=to_language)
        return result, reason

    def get_result_text(self, reason, result, from_language, to_language):
        """
        Returns the formatted result text based on the recognition reason.
        Args:
            reason (str): The reason for the recognition.
            result (str): The result of the recognition.
            from_language (str): The language of the input speech. Defaults to 'hi-IN'.
            to_language (str): The language to translate the speech into. Defaults to 'en'.
        Returns:
            str: The formatted result text.
        """
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
    def text_to_speech(self, text, language = 'en-IN'):
        voice_map = {
            'en-IN': 'en-IN-NeerjaNeural',
            'hi-IN': 'hi-IN-SwaraNeural'
        }
        speech_config = speechsdk.SpeechConfig(subscription=self.config['SPEECH_KEY'], region=self.config['SPEECH_REGION'])
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        speech_config.speech_synthesis_voice_name=voice_map[language]
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # print("Speech synthesized for text [{}]".format(text))
            return None
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    translator = Speech()
    translator.translate_text('मेरा नाम क्या है?')
    # result, _ = translator.translate_speech('hi-IN', 'en')