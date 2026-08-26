# -*- coding: utf-8 -*-
"""
오디오 자산(BGM & SFX) 프로시저럴 생성기
- 외부 라이브러리 없이 순수 Python wave 모듈로 고음질 SFX 및 앰비언트 BGM 생성
"""

import os
import math
import struct
import wave

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIO_DIR = os.path.join(BASE_DIR, "outputs", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

SAMPLE_RATE = 44100

def write_wav(filename, samples):
    filepath = os.path.join(AUDIO_DIR, filename)
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)        # mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(SAMPLE_RATE)
        packed = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            val = int(clamped * 32767.0)
            packed.extend(struct.pack("<h", val))
        wf.writeframes(packed)
    print(f"[OK] Audio asset created: {filepath}")
    return filepath

def generate_whoosh():
    """부드러운 씬 전환 Whoosh 효과음 (0.45초)"""
    duration = 0.45
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    
    import random
    random.seed(42)
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = t / duration
        # Frequency sweep from 250Hz -> 800Hz -> 180Hz
        freq = 250.0 + 550.0 * math.sin(progress * math.pi)
        # Volume envelope: smooth bell curve
        amp = math.sin(progress * math.pi) ** 1.8
        # Sine wave + filtered white noise for wind rush feel
        tone = math.sin(2.0 * math.pi * freq * t)
        noise = (random.random() * 2.0 - 1.0) * 0.4
        val = (tone * 0.6 + noise * 0.4) * amp * 0.5
        samples.append(val)
    return write_wav("sfx_whoosh.wav", samples)

def generate_ding():
    """선배 팁 강조 맑은 차임 Ding 효과음 (0.7초)"""
    duration = 0.7
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    
    # E6 (1318.5 Hz) + B6 (1975.5 Hz) harmonic bell
    f1 = 1318.5
    f2 = 1975.5
    f3 = 2637.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        decay = math.exp(-6.0 * t)
        tone = (
            math.sin(2.0 * math.pi * f1 * t) * 0.6 +
            math.sin(2.0 * math.pi * f2 * t) * 0.3 +
            math.sin(2.0 * math.pi * f3 * t) * 0.1
        )
        samples.append(tone * decay * 0.6)
    return write_wav("sfx_ding.wav", samples)

def generate_pop():
    """체크리스트 출현 경쾌한 Pop 효과음 (0.15초)"""
    duration = 0.15
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = t / duration
        # Fast pitch drop: 600Hz -> 150Hz
        freq = 600.0 * (1.0 - progress * 0.75)
        decay = math.exp(-22.0 * t)
        tone = math.sin(2.0 * math.pi * freq * t)
        samples.append(tone * decay * 0.5)
    return write_wav("sfx_pop.wav", samples)

def generate_ambient_bgm():
    """전문적이고 차분한 신뢰형 테크 앰비언트 BGM 루프 (60초)"""
    duration = 60.0
    num_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * num_samples
    
    # Chord progression: Am9 -> Fmaj7 -> Cmaj7 -> Gsus4 (각 7.5초 x 2 = 15초 x 4 = 60초)
    chords = [
        # Am9 (A3, C4, E4, G4, B4)
        [220.0, 261.63, 329.63, 392.00, 493.88],
        # Fmaj7 (F3, A3, C4, E4)
        [174.61, 220.00, 261.63, 329.63],
        # Cmaj7 (C3, E3, G3, B3, D4)
        [130.81, 164.81, 196.00, 246.94, 293.66],
        # Gsus4 -> G (G3, C4, D4 -> G3, B3, D4)
        [196.00, 261.63, 293.66, 392.00]
    ]
    
    chord_duration = 7.5
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        chord_idx = int((t / chord_duration) % len(chords))
        current_chord = chords[chord_idx]
        
        # Soft warm synth pad synthesis
        pad_val = 0.0
        for f in current_chord:
            # Dual oscillator with slight detune for lush thickness
            osc1 = math.sin(2.0 * math.pi * f * t)
            osc2 = math.sin(2.0 * math.pi * (f * 1.002) * t)
            # Gentle pulsing LFO (0.2Hz)
            lfo = 0.7 + 0.3 * math.sin(2.0 * math.pi * 0.2 * t)
            pad_val += (osc1 + osc2) * 0.5 * lfo
            
        # Subtle sub-bass
        bass_freq = current_chord[0] / 2.0
        bass_val = math.sin(2.0 * math.pi * bass_freq * t) * 0.35
        
        # Soft rhythmic pulse (120 BPM = 0.5s period)
        beat_t = (t % 0.5) / 0.5
        pulse = math.exp(-8.0 * beat_t) * math.sin(2.0 * math.pi * 80.0 * (t % 0.5)) * 0.15
        
        total = (pad_val * 0.12 + bass_val * 0.2 + pulse) * 0.5
        samples[i] = total

    # Smooth fade-in and fade-out at borders
    fade_len = int(SAMPLE_RATE * 1.5)
    for i in range(fade_len):
        samples[i] *= (i / fade_len)
        samples[-1 - i] *= (i / fade_len)

    return write_wav("bgm_ambient_tech.wav", samples)

if __name__ == "__main__":
    generate_whoosh()
    generate_ding()
    generate_pop()
    generate_ambient_bgm()
    print("All procedural audio assets generated successfully.")
