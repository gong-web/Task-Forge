from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REMINDER_SOUND_ID = "classic_chime"
_SAMPLE_RATE = 44_100


def _note(name: str) -> float:
    semitones = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11,
    }
    pitch = name.strip().upper()
    if len(pitch) < 2:
        raise ValueError(f"Invalid note name: {name}")
    head = pitch[:2] if pitch[:2] in semitones else pitch[:1]
    octave = int(pitch[len(head):])
    midi_number = (octave + 1) * 12 + semitones[head]
    return 440.0 * (2 ** ((midi_number - 69) / 12))


def _layer(frequency: float, start_ms: int, duration_ms: int, gain: float) -> tuple[float, int, int, float]:
    return frequency, start_ms, duration_ms, gain


@dataclass(frozen=True)
class ReminderSoundSpec:
    id: str
    label: str
    subtitle: str
    mood: str
    accent: str
    texture: str
    file_name: str
    duration_ms: int
    layers: tuple[tuple[float, int, int, float], ...]


_REMINDER_SOUND_SPECS: tuple[ReminderSoundSpec, ...] = (
    ReminderSoundSpec(
        id="classic_chime",
        label="标准木拨",
        subtitle="清脆三连音，适合通用提醒。",
        mood="清亮",
        accent="#60a5fa",
        texture="bell",
        file_name="reminder-classic.wav",
        duration_ms=980,
        layers=(
            _layer(_note("E5"), 0, 520, 0.95),
            _layer(_note("B5"), 140, 500, 0.62),
            _layer(_note("E6"), 320, 640, 0.42),
        ),
    ),
    ReminderSoundSpec(
        id="soft_chime",
        label="柔和木拨",
        subtitle="绵柔上扬，适合长时间驻留。",
        mood="轻柔",
        accent="#34d399",
        texture="soft",
        file_name="reminder-soft.wav",
        duration_ms=1060,
        layers=(
            _layer(_note("D5"), 0, 560, 0.82),
            _layer(_note("A5"), 160, 560, 0.48),
            _layer(_note("D6"), 340, 700, 0.35),
        ),
    ),
    ReminderSoundSpec(
        id="aurora_bloom",
        label="极光绽放",
        subtitle="温暖四音，像晨光逐步打开。",
        mood="温暖",
        accent="#f59e0b",
        texture="soft",
        file_name="reminder-aurora.wav",
        duration_ms=1380,
        layers=(
            _layer(_note("A4"), 0, 640, 0.76),
            _layer(_note("C#5"), 150, 640, 0.56),
            _layer(_note("E5"), 320, 680, 0.46),
            _layer(_note("A5"), 500, 860, 0.32),
        ),
    ),
    ReminderSoundSpec(
        id="glass_drop",
        label="琉璃滴答",
        subtitle="高频轻薄，短促但很清楚。",
        mood="轻快",
        accent="#38bdf8",
        texture="glass",
        file_name="reminder-glass.wav",
        duration_ms=820,
        layers=(
            _layer(_note("G5"), 0, 400, 0.95),
            _layer(_note("D6"), 110, 430, 0.58),
            _layer(_note("B6"), 260, 520, 0.28),
        ),
    ),
    ReminderSoundSpec(
        id="marimba_smile",
        label="木琴微笑",
        subtitle="节奏更跳，适合白天办公。",
        mood="明快",
        accent="#fb7185",
        texture="marimba",
        file_name="reminder-marimba.wav",
        duration_ms=930,
        layers=(
            _layer(_note("F5"), 0, 330, 0.94),
            _layer(_note("A5"), 150, 360, 0.70),
            _layer(_note("C6"), 320, 420, 0.52),
            _layer(_note("A5"), 540, 280, 0.24),
        ),
    ),
    ReminderSoundSpec(
        id="harbor_bell",
        label="港湾钟声",
        subtitle="低频更稳，适合晚间提醒。",
        mood="沉静",
        accent="#22c55e",
        texture="bell",
        file_name="reminder-harbor.wav",
        duration_ms=1240,
        layers=(
            _layer(_note("C5"), 0, 620, 0.84),
            _layer(_note("E5"), 190, 580, 0.58),
            _layer(_note("G5"), 390, 820, 0.42),
        ),
    ),
    ReminderSoundSpec(
        id="starlight_echo",
        label="星光回响",
        subtitle="轻盈延展，保留一点空间感。",
        mood="空灵",
        accent="#67e8f9",
        texture="glass",
        file_name="reminder-starlight.wav",
        duration_ms=1480,
        layers=(
            _layer(_note("E5"), 0, 520, 0.82),
            _layer(_note("G5"), 180, 500, 0.52),
            _layer(_note("B5"), 360, 620, 0.40),
            _layer(_note("G6"), 580, 760, 0.25),
        ),
    ),
    ReminderSoundSpec(
        id="sunrise_ping",
        label="曦光短讯",
        subtitle="轻提示一下，不打断节奏。",
        mood="轻醒",
        accent="#f97316",
        texture="soft",
        file_name="reminder-sunrise.wav",
        duration_ms=640,
        layers=(
            _layer(_note("D5"), 0, 250, 0.82),
            _layer(_note("F#5"), 120, 250, 0.42),
            _layer(_note("A5"), 240, 380, 0.30),
        ),
    ),
)
_REMINDER_SOUND_INDEX = {spec.id: spec for spec in _REMINDER_SOUND_SPECS}
_ASSETS_READY = False


def reminder_audio_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "audio"


def list_reminder_sound_specs() -> tuple[ReminderSoundSpec, ...]:
    ensure_reminder_sound_assets()
    return _REMINDER_SOUND_SPECS


def reminder_sound_spec(sound_id: str | None) -> ReminderSoundSpec:
    normalized = normalize_reminder_sound_id(sound_id)
    ensure_reminder_sound_assets()
    return _REMINDER_SOUND_INDEX.get(normalized, _REMINDER_SOUND_SPECS[0])


def reminder_sound_specs() -> list[dict[str, str]]:
    ensure_reminder_sound_assets()
    return [
        {
            "id": spec.id,
            "label": spec.label,
            "subtitle": spec.subtitle,
            "mood": spec.mood,
            "accent": spec.accent,
            "file_name": spec.file_name,
            "duration_ms": str(spec.duration_ms),
        }
        for spec in _REMINDER_SOUND_SPECS
    ]


def reminder_sound_options() -> list[tuple[str, str]]:
    ensure_reminder_sound_assets()
    return [(spec.id, spec.label) for spec in _REMINDER_SOUND_SPECS]


def normalize_reminder_sound_id(sound_id: str | None) -> str:
    requested = (sound_id or "").strip()
    if requested in _REMINDER_SOUND_INDEX:
        return requested
    return DEFAULT_REMINDER_SOUND_ID


def reminder_sound_path(sound_id: str | None) -> Path:
    ensure_reminder_sound_assets()
    return reminder_audio_dir() / reminder_sound_spec(sound_id).file_name


def reminder_sound_label(sound_id: str | None) -> str:
    return reminder_sound_spec(sound_id).label


def ensure_reminder_sound_assets() -> None:
    global _ASSETS_READY
    if _ASSETS_READY:
        return
    audio_dir = reminder_audio_dir()
    audio_dir.mkdir(parents=True, exist_ok=True)
    for spec in _REMINDER_SOUND_SPECS:
        sound_path = audio_dir / spec.file_name
        if sound_path.exists() and sound_path.stat().st_size > 128:
            continue
        _synthesize_sound(spec, sound_path)
    _ASSETS_READY = True


def _partials_for(texture: str) -> tuple[tuple[float, float], ...]:
    if texture == "soft":
        return ((1.0, 1.0), (2.0, 0.14), (0.5, 0.07))
    if texture == "glass":
        return ((1.0, 1.0), (2.6, 0.28), (4.2, 0.10))
    if texture == "marimba":
        return ((1.0, 1.0), (3.0, 0.22), (4.5, 0.08))
    return ((1.0, 1.0), (2.01, 0.40), (3.96, 0.16))


def _sample_value(spec: ReminderSoundSpec, frequency: float, elapsed_seconds: float) -> float:
    value = 0.0
    for harmonic, weight in _partials_for(spec.texture):
        value += math.sin(2 * math.pi * frequency * harmonic * elapsed_seconds) * weight
    if spec.texture == "soft":
        value *= 0.94 + 0.06 * math.sin(2 * math.pi * 4.8 * elapsed_seconds)
    elif spec.texture == "glass":
        value *= 0.88 + 0.12 * math.cos(2 * math.pi * 8.0 * elapsed_seconds)
    elif spec.texture == "marimba":
        value *= 0.9 + 0.1 * math.sin(2 * math.pi * 7.2 * elapsed_seconds)
    return value


def _envelope(position: int, total: int) -> float:
    attack = max(1, int(total * 0.08))
    release = max(1, int(total * 0.26))
    if position < attack:
        base = position / attack
    elif position > total - release:
        base = max(0.0, (total - position) / release)
    else:
        sustain_span = max(1, total - attack - release)
        decay_progress = (position - attack) / sustain_span
        base = 1.0 - (decay_progress * 0.68)
    return max(0.0, base) ** 1.18


def _synthesize_sound(spec: ReminderSoundSpec, sound_path: Path) -> None:
    total_ms = max(start_ms + duration_ms for _, start_ms, duration_ms, _ in spec.layers) + 180
    total_samples = int(_SAMPLE_RATE * total_ms / 1000)
    waveform = [0.0] * max(1, total_samples)

    for frequency, start_ms, duration_ms, gain in spec.layers:
        start_index = int(_SAMPLE_RATE * start_ms / 1000)
        sample_count = max(1, int(_SAMPLE_RATE * duration_ms / 1000))
        for offset in range(sample_count):
            target_index = start_index + offset
            if target_index >= len(waveform):
                break
            tone = _sample_value(spec, frequency, offset / _SAMPLE_RATE)
            waveform[target_index] += tone * _envelope(offset, sample_count) * gain

    peak = max((abs(sample) for sample in waveform), default=0.0)
    normalizer = 0.78 / peak if peak > 0 else 0.0
    pcm = bytearray()
    for sample in waveform:
        clipped = max(-1.0, min(1.0, sample * normalizer))
        pcm.extend(struct.pack("<h", int(clipped * 32767)))

    with wave.open(str(sound_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(_SAMPLE_RATE)
        wav_file.writeframes(bytes(pcm))
