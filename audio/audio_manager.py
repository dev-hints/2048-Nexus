"""
Audio manager for 2048-Nexus.

Wraps PyQt6 QMediaPlayer (background music) and QSoundEffect (low-latency
SFX).  Degrades gracefully when audio files are missing or the backend
is unavailable.

Audio files are generated programmatically on first launch if absent.
"""
from __future__ import annotations

import math
import os
import struct
import wave
from typing import Dict, Optional

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect

from utils.constants import (
    AUDIO_DIR,
    AUDIO_MUSIC, AUDIO_MOVE, AUDIO_MERGE,
    AUDIO_WIN, AUDIO_LOSE, AUDIO_SPAWN,
)


# ---------------------------------------------------------------------------
# Programmatic audio generation
# ---------------------------------------------------------------------------

def _write_sine_wav(
    path: str,
    freq: float,
    duration: float,
    amplitude: float = 0.4,
    sample_rate: int = 44100,
) -> None:
    """Write a mono sine-wave .wav file."""
    n_samples = int(sample_rate * duration)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # Apply simple envelope (fade in/out over 10 ms)
            env = 1.0
            fade = int(0.01 * sample_rate)
            if i < fade:
                env = i / fade
            elif i > n_samples - fade:
                env = (n_samples - i) / fade
            val = int(amplitude * env * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            val = max(-32768, min(32767, val))
            frames += struct.pack("<h", val)
        wf.writeframes(bytes(frames))


def _write_chord_wav(
    path: str,
    freqs: list[float],
    duration: float,
    sample_rate: int = 44100,
) -> None:
    """Write a multi-frequency chord .wav file."""
    n_samples = int(sample_rate * duration)
    amplitude = 0.25 / len(freqs)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            env = 1.0
            fade = int(0.02 * sample_rate)
            if i < fade:
                env = i / fade
            elif i > n_samples - fade:
                env = (n_samples - i) / fade
            sample = sum(
                amplitude * env * 32767 * math.sin(2 * math.pi * f * i / sample_rate)
                for f in freqs
            )
            val = max(-32768, min(32767, int(sample)))
            frames += struct.pack("<h", val)
        wf.writeframes(bytes(frames))


def _write_ambient_pad(
    path: str,
    sample_rate: int = 44100,
    duration: float = 8.0,
) -> None:
    """
    Write a gentle ambient pad loop.

    Uses four harmonically related frequencies with slow amplitude
    modulation (LFO at 0.15 Hz) and long fade-in / fade-out envelopes
    so the loop is smooth and non-irritating.
    """
    # Soft Cm-ish ambient chord (C3 · E♭3 · G3 · B♭3)
    freqs = [130.81, 155.56, 196.00, 233.08]
    lfo_rate = 0.15        # Hz — slow breath-like modulation
    base_amp = 0.04        # very quiet
    n_samples = int(sample_rate * duration)
    fade_samples = int(0.6 * sample_rate)   # 600 ms fade

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # Fade-in / fade-out envelope
            if i < fade_samples:
                env = i / fade_samples
            elif i > n_samples - fade_samples:
                env = (n_samples - i) / fade_samples
            else:
                env = 1.0

            # LFO modulates amplitude gently (0.7 – 1.0 range)
            lfo = 0.85 + 0.15 * math.sin(2 * math.pi * lfo_rate * i / sample_rate)

            # Sum the pad frequencies with slight detuning per voice
            sample = 0.0
            per_amp = base_amp / len(freqs)
            for k, f in enumerate(freqs):
                detune = 1.0 + (k - 1) * 0.0008   # tiny chorus
                sample += per_amp * math.sin(2 * math.pi * f * detune * i / sample_rate)

            val = int(env * lfo * sample * 32767)
            val = max(-32768, min(32767, val))
            frames += struct.pack("<h", val)
        wf.writeframes(bytes(frames))


def generate_audio_assets() -> None:
    """Generate placeholder audio assets if they don't exist."""
    os.makedirs(AUDIO_DIR, exist_ok=True)

    specs = {
        # Short crisp click (high freq, very short)
        AUDIO_MOVE:  lambda p: _write_sine_wav(p, 660, 0.06, amplitude=0.18),
        # Bright upward chord stab
        AUDIO_MERGE: lambda p: _write_chord_wav(p, [587, 740, 880], 0.14),
        # Quiet soft blip
        AUDIO_SPAWN: lambda p: _write_sine_wav(p, 392, 0.05, amplitude=0.10),
        # Triumphant ascending chord
        AUDIO_WIN:   lambda p: _write_chord_wav(p, [523, 659, 784, 1047], 1.0),
        # Descending somber chord
        AUDIO_LOSE:  lambda p: _write_chord_wav(p, [220, 196, 165], 0.9),
        # Gentle ambient pad (non-irritating loop)
        AUDIO_MUSIC: _write_ambient_pad,
    }

    for filename, generator in specs.items():
        path = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(path):
            try:
                generator(path)
            except Exception:
                pass  # non-fatal


def regenerate_music() -> None:
    """Force-regenerate the background music file (call after settings change)."""
    path = os.path.join(AUDIO_DIR, AUDIO_MUSIC)
    try:
        if os.path.exists(path):
            os.unlink(path)
        _write_ambient_pad(path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Audio manager
# ---------------------------------------------------------------------------

class AudioManager(QMediaPlayer):
    """
    Manages background music and sound effects.

    Background music loops via ``QMediaPlayer``.
    Sound effects use ``QSoundEffect`` for minimum latency.
    """

    _instance: "AudioManager | None" = None

    @classmethod
    def instance(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        super().__init__()
        # Make sure assets exist before we try to load them
        generate_audio_assets()

        # Background music via QMediaPlayer
        self._audio_out = QAudioOutput()
        self.setAudioOutput(self._audio_out)
        self._audio_out.setVolume(0.5)
        self.mediaStatusChanged.connect(self._on_status_changed)

        # SFX pool
        self._sfx: Dict[str, QSoundEffect] = {}
        for name in (AUDIO_MOVE, AUDIO_MERGE, AUDIO_WIN, AUDIO_LOSE, AUDIO_SPAWN):
            path = os.path.join(AUDIO_DIR, name)
            if os.path.exists(path):
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(path))
                effect.setVolume(0.7)
                self._sfx[name] = effect

        self._sound_enabled: bool = True
        self._music_enabled: bool = False   # off by default — user can enable in Settings

    # ------------------------------------------------------------------
    # Music
    # ------------------------------------------------------------------

    def play_music(self) -> None:
        if not self._music_enabled:
            return
        path = os.path.join(AUDIO_DIR, AUDIO_MUSIC)
        if os.path.exists(path):
            self.setSource(QUrl.fromLocalFile(path))
            self.play()

    def stop_music(self) -> None:
        self.stop()

    def _on_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """Loop background music when it ends."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self._music_enabled:
            self.setPosition(0)
            self.play()

    # ------------------------------------------------------------------
    # SFX
    # ------------------------------------------------------------------

    def play_sfx(self, name: str) -> None:
        if not self._sound_enabled:
            return
        effect = self._sfx.get(name)
        if effect:
            effect.play()

    def play_move(self) -> None:
        self.play_sfx(AUDIO_MOVE)

    def play_merge(self) -> None:
        self.play_sfx(AUDIO_MERGE)

    def play_win(self) -> None:
        self.play_sfx(AUDIO_WIN)

    def play_lose(self) -> None:
        self.play_sfx(AUDIO_LOSE)

    def play_spawn(self) -> None:
        self.play_sfx(AUDIO_SPAWN)

    # ------------------------------------------------------------------
    # Toggle controls
    # ------------------------------------------------------------------

    def set_sound_enabled(self, enabled: bool) -> None:
        self._sound_enabled = enabled

    def set_music_enabled(self, enabled: bool) -> None:
        self._music_enabled = enabled
        if not enabled:
            self.stop_music()
        else:
            self.play_music()

    def set_volume(self, percent: int) -> None:
        """Set volume from 0–100."""
        self._audio_out.setVolume(max(0, min(100, percent)) / 100.0)

    @property
    def sound_enabled(self) -> bool:
        return self._sound_enabled

    @property
    def music_enabled(self) -> bool:
        return self._music_enabled
