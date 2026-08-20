import os
from elevenlabs.client import ElevenLabs

_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


def text_to_speech(text: str, output_path: str, voice: str = "Rachel") -> str:
    """Convert text to an audio file using ElevenLabs. Returns the output path."""
    audio = _client.text_to_speech.convert(
        text=text,
        voice_id=voice,
        model_id="eleven_multilingual_v2",
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path