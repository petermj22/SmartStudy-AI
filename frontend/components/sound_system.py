"""
SmartStudy Sound System
Generates notification sounds using Web Audio API.
Zero external audio files — all sounds synthesized in-browser via JavaScript.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


AUDIO_ENGINE_JS = """
<script>
// ══════════════════════════════════════════════════════
// SmartStudy Web Audio Engine v1.0
// All sounds generated programmatically (no files needed)
// ══════════════════════════════════════════════════════

window.SmartStudyAudio = (function() {
    let audioCtx = null;
    let masterVolume = 0.7;
    let isMuted = false;

    function getCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    function playTone(freq, duration, type, vol, startTime) {
        type = type || 'sine';
        vol = vol || 0.4;
        const ctx = getCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const t = startTime || ctx.currentTime;

        osc.type = type;
        osc.frequency.setValueAtTime(freq, t);

        // ADSR envelope
        gain.gain.setValueAtTime(0, t);
        gain.gain.linearRampToValueAtTime(isMuted ? 0 : vol * masterVolume, t + 0.02);
        gain.gain.linearRampToValueAtTime(isMuted ? 0 : vol * masterVolume * 0.7, t + duration * 0.5);
        gain.gain.linearRampToValueAtTime(0, t + duration);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(t);
        osc.stop(t + duration);
        return osc;
    }

    const sounds = {

        // Break reminder — gentle ascending chime (C major arpeggio)
        playBreakChime: function() {
            const ctx = getCtx();
            var notes = [
                { freq: 523.25, t: 0 },
                { freq: 659.25, t: 0.18 },
                { freq: 783.99, t: 0.36 },
                { freq: 1046.50, t: 0.55 }
            ];
            notes.forEach(function(n) {
                playTone(n.freq, 0.6, 'sine', 0.35, ctx.currentTime + n.t);
            });
        },

        // Distraction alert — soft double pulse
        playDistractionAlert: function() {
            const ctx = getCtx();
            playTone(440, 0.15, 'sine', 0.3, ctx.currentTime);
            playTone(440, 0.15, 'sine', 0.3, ctx.currentTime + 0.25);
        },

        // Fatigue warning — descending minor thirds
        playFatigueAlert: function() {
            const ctx = getCtx();
            playTone(659.25, 0.4, 'triangle', 0.35, ctx.currentTime);
            playTone(554.37, 0.4, 'triangle', 0.30, ctx.currentTime + 0.35);
            playTone(440.00, 0.6, 'triangle', 0.25, ctx.currentTime + 0.65);
        },

        // Microsleep — urgent alternating alarm
        playCriticalAlert: function() {
            const ctx = getCtx();
            for (var i = 0; i < 5; i++) {
                playTone(1000, 0.1, 'square', 0.5, ctx.currentTime + i * 0.2);
                playTone(500, 0.1, 'square', 0.4, ctx.currentTime + i * 0.2 + 0.1);
            }
        },

        // Success — pleasant resolution chord
        playSuccessSound: function() {
            const ctx = getCtx();
            [523.25, 659.25, 783.99].forEach(function(freq, i) {
                playTone(freq, 0.8, 'sine', 0.25, ctx.currentTime + i * 0.05);
            });
        },

        // Focus session start — energizing ascending scale
        playFocusStart: function() {
            const ctx = getCtx();
            var scale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25];
            scale.forEach(function(freq, i) {
                playTone(freq, 0.15, 'sine', 0.25, ctx.currentTime + i * 0.08);
            });
        },

        // Break ending — wake up chime
        playBreakEnd: function() {
            const ctx = getCtx();
            var notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 1046.50];
            notes.forEach(function(freq, i) {
                playTone(freq, 0.2, 'sine', 0.3, ctx.currentTime + i * 0.12);
            });
        },

        // Eye strain warning — soft two-tone
        playEyeStrain: function() {
            const ctx = getCtx();
            playTone(330, 0.3, 'triangle', 0.25, ctx.currentTime);
            playTone(440, 0.3, 'triangle', 0.20, ctx.currentTime + 0.3);
        },

        // Achievement unlock — fanfare
        playAchievement: function() {
            const ctx = getCtx();
            var fanfare = [
                {freq: 523.25, t: 0, dur: 0.15},
                {freq: 523.25, t: 0.15, dur: 0.15},
                {freq: 523.25, t: 0.30, dur: 0.15},
                {freq: 659.25, t: 0.45, dur: 0.4},
                {freq: 622.25, t: 0.50, dur: 0.4},
                {freq: 659.25, t: 0.90, dur: 0.6}
            ];
            fanfare.forEach(function(n) {
                playTone(n.freq, n.dur, 'sine', 0.35, ctx.currentTime + n.t);
            });
        }
    };

    return {
        play: function(soundName) {
            try {
                if (sounds[soundName]) { sounds[soundName](); }
            } catch(e) { console.warn('SmartStudy Audio:', e); }
        },
        setVolume: function(vol) {
            masterVolume = Math.max(0, Math.min(1, vol / 100));
        },
        mute: function() { isMuted = true; },
        unmute: function() { isMuted = false; },
        toggleMute: function() { isMuted = !isMuted; return isMuted; },
        isMuted: function() { return isMuted; }
    };
})();

window.playSmartStudySound = function(name) { window.SmartStudyAudio.play(name); };
window.setSmartStudyVolume = function(vol) { window.SmartStudyAudio.setVolume(vol); };
</script>
"""


def inject_audio_engine(volume: int = 70, muted: bool = False) -> None:
    """
    Inject the Web Audio engine into the Streamlit app.
    Call once at app startup.
    """
    vol_call = f"window.SmartStudyAudio.setVolume({volume});"
    mute_call = "window.SmartStudyAudio.mute();" if muted else ""

    html = f"""
    {AUDIO_ENGINE_JS}
    <script>
    setTimeout(function() {{
        {vol_call}
        {mute_call}
    }}, 500);
    </script>
    """
    components.html(html, height=0, scrolling=False)


def play_sound(sound_name: str) -> None:
    """
    Trigger a sound in the browser.

    Sound names:
    - playBreakChime
    - playDistractionAlert
    - playFatigueAlert
    - playCriticalAlert
    - playSuccessSound
    - playFocusStart
    - playBreakEnd
    - playEyeStrain
    - playAchievement
    """
    js = f"""
    <script>
    (function() {{
        function tryPlay() {{
            if (window.SmartStudyAudio) {{
                window.SmartStudyAudio.play('{sound_name}');
            }} else {{
                setTimeout(tryPlay, 200);
            }}
        }}
        tryPlay();
    }})();
    </script>
    """
    components.html(js, height=0, scrolling=False)


def update_volume(volume: int, muted: bool = False) -> None:
    """Update audio engine volume and mute state."""
    mute_js = "window.SmartStudyAudio.mute();" if muted else "window.SmartStudyAudio.unmute();"
    components.html(
        f"<script>if(window.SmartStudyAudio){{window.SmartStudyAudio.setVolume({volume});{mute_js}}}</script>",
        height=0, scrolling=False,
    )


# ── Convenience functions ─────────────────────────────────

def play_break_reminder() -> None:
    play_sound("playBreakChime")

def play_distraction_alert() -> None:
    play_sound("playDistractionAlert")

def play_fatigue_warning() -> None:
    play_sound("playFatigueAlert")

def play_critical_alert() -> None:
    play_sound("playCriticalAlert")

def play_session_start() -> None:
    play_sound("playFocusStart")

def play_session_end() -> None:
    play_sound("playSuccessSound")

def play_achievement() -> None:
    play_sound("playAchievement")

def play_break_end() -> None:
    play_sound("playBreakEnd")

def play_eye_strain() -> None:
    play_sound("playEyeStrain")
