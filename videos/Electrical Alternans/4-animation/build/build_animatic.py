"""Animatic for Electrical Alternans (adapted from Pulsus Paradoxus): key frames cut to the measured scratch VO.

Step 1  python3 build_animatic.py timeline <audio dir>            -> timeline.json
Step 2  python3 pulsus_synth.py <ks dir> cues timeline.json         -> cues/*.wav, markers.json
Step 3  python3 build_animatic.py render <audio dir> <kf dir> <out.mp4>

Pauses (s) between beats: 0.5 inside a scene, 1.0 between scenes, 1.0 lead-in before 1A
(Cue A taps play alone), 2.0 after 5C so the viewer hears expiration-only taps across a
whole breath, 2.5 tail after 5F. Every time comes from ffprobe on the real files.
"""
import json, os, subprocess, sys
import numpy as np

BEATS = ["1A", "1B", "2A", "2B", "2C", "3A", "3B", "3C", "3D", "3E", "4A", "4B", "4C", "4D", "4E", "4F",
         "5A", "5B", "5C", "5D", "5E", "5F", "6A", "6B", "6C"]
NAMES = {"1A": "1A_strip", "1B": "1B_title", "2A": "2A_definition", "2B": "2B_total", "2C": "2C_sign", "3A": "3A_two-buckets",
         "3B": "3B_electrical", "3C": "3C_effusion", "3D": "3D_swing", "3E": "3E_drain", "4A": "4A_every-other", "4B": "4B_leads",
         "4C": "4C_companions", "4D": "4D_numbers", "4E": "4E_rule", "4F": "4F_bigeminy", "5A": "5A_bedside", "5B": "5B_beck",
         "5C": "5C_common", "5D": "5D_pulsus", "5E": "5E_odds", "5F": "5F_link", "6A": "6A_recap-strip", "6B": "6B_checklist",
         "6C": "6C_end"}
LEAD_IN, IN_SCENE, NEW_SCENE, TAIL = 1.0, 0.5, 1.0, 3.0
SPECIAL_AFTER = {"3D": 1.0, "4D": 0.6, "4F": 1.0, "5E": 0.8}   # holds from the motion notes
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).strip())


def decode(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1",
                                   "-ar", str(SR), "-"])
    return np.frombuffer(raw, dtype=np.float32).copy()


def timeline(audio_dir):
    t, beats = LEAD_IN, []
    for i, b in enumerate(BEATS):
        d = dur(os.path.join(audio_dir, b + ".mp3"))
        beats.append(dict(id=b, file=b + ".mp3", start=round(t, 3), dur=round(d, 3), end=round(t + d, 3)))
        if i + 1 < len(BEATS):
            gap = SPECIAL_AFTER.get(b, NEW_SCENE if BEATS[i + 1][0] != b[0] else IN_SCENE)
            t += d + gap
        else:
            t += d + TAIL
    tl = dict(total=round(t, 3), beats=beats,
              pauses=dict(lead_in=LEAD_IN, in_scene=IN_SCENE, new_scene=NEW_SCENE, tail=TAIL, special_after=SPECIAL_AFTER))
    json.dump(tl, open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
    return tl


def render(audio_dir, kf_dir, out_mp4):
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    total = tl["total"]
    mix = np.zeros(int(total * SR) + SR, dtype=np.float32)

    def place(sig, at, gain):
        i = int(at * SR)
        mix[i:i + len(sig)] += gain * sig[:len(mix) - i]

    for b in tl["beats"]:
        place(decode(os.path.join(audio_dir, b["file"])), b["start"], 1.0)
    # no music or effect cues in this video
    mix /= max(1e-6, np.max(np.abs(mix))) / 0.9
    wav = os.path.join(HERE, "animatic_mix.wav")
    pcm = (mix * 32767).astype(np.int16)
    import wave
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

    # video: each key frame from its beat start to the next beat start (1A from 0)
    lst = os.path.join(HERE, "frames.txt")
    with open(lst, "w") as fh:
        beats = tl["beats"]
        for i, b in enumerate(beats):
            s = 0.0 if i == 0 else b["start"]
            e = beats[i + 1]["start"] if i + 1 < len(beats) else total
            fh.write(f"file '{os.path.join(kf_dir, NAMES[b['id']] + '.png')}'\nduration {e - s:.3f}\n")
        fh.write(f"file '{os.path.join(kf_dir, NAMES[beats[-1]['id']] + '.png')}'\n")
    font = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    vf = (f"fps=30,format=yuv420p,drawtext=fontfile={font}:text='ANIMATIC  %{{pts\\:hms}}':x=40:y=h-50:"
          f"fontsize=22:fontcolor=0x8A8B8C")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                           "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_mp4])
    print("rendered", out_mp4, round(total, 2), "s")


if __name__ == "__main__":
    if sys.argv[1] == "timeline":
        tl = timeline(sys.argv[2])
        print(json.dumps([(b["id"], b["start"], b["dur"]) for b in tl["beats"]]), tl["total"])
    else:
        render(*sys.argv[2:5])
