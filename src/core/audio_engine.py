import os
import random
import wave


def generate_white_noise_file(filepath: str, duration_seconds: int = 5):
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if os.path.exists(filepath):
        return filepath

    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

    sample_rate = 44100
    amplitude = 8000
    frame_count = sample_rate * duration_seconds
    rng = random.Random(20260327)
    samples = bytearray()
    for _ in range(frame_count):
        value = rng.randint(-amplitude, amplitude)
        samples.extend(int(value).to_bytes(2, byteorder="little", signed=True))

    with wave.open(filepath, "wb") as obj:
        obj.setnchannels(1)
        obj.setsampwidth(2)
        obj.setframerate(sample_rate)
        obj.writeframes(samples)

    return filepath
