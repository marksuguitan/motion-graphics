"""Carry word timings from a transcribed reference take onto the take we use (same text, same voice).

Why: ElevenLabs transcription needs an upload that the network blocks, but it will transcribe audio that is
already in an ElevenLabs flow (the other take of each beat, or a fresh one-take reference). This script
lines the two recordings up by sound (MFCC + dynamic time warping) and maps every word's start/end
from the reference onto our file.

Usage: python3 align_words.py <our_audio_dir> <ref_audio_dir> <ref_transcripts.json> <out.json>
  ref_transcripts.json: {"1A": [{"text","start","end"}, ...], ...}  (ElevenLabs Scribe words, type == word)
  ref audio files are named REF_<beat>.mp3; ours are <beat>.mp3

Checks per beat (reported in out.json["_qc"]):
  path_cost   mean frame distance along the DTW path (lower = closer match)
  onset_err   first-word start vs. measured speech onset in our file (s)
  offset_err  last-word end vs. measured speech offset in our file (s)
  pause_hits  share of long pauses in the reference (>= 0.18 s between words) that land in a
              low-energy stretch of our file after mapping
"""
import json, subprocess, sys
import numpy as np
from scipy.fft import dct

SR, HOP, WIN = 16000, 160, 400          # 10 ms hop, 25 ms window


def decode(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.float32).copy()


def mel_fb(n_mels=40, n_fft=512):
    f = lambda m: 700 * (10 ** (m / 2595) - 1)
    m = lambda hz: 2595 * np.log10(1 + hz / 700)
    pts = f(np.linspace(m(60), m(7600), n_mels + 2))
    bins = np.floor((n_fft + 1) * pts / SR).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        a, b, c = bins[i], bins[i + 1], bins[i + 2]
        fb[i, a:b] = (np.arange(a, b) - a) / max(b - a, 1)
        fb[i, b:c] = (c - np.arange(b, c)) / max(c - b, 1)
    return fb


FB = mel_fb()


def features(x):
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
    n = 1 + max(0, (len(x) - WIN) // HOP)
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    frames = x[idx] * np.hamming(WIN)
    spec = np.abs(np.fft.rfft(frames, 512)) ** 2
    logmel = np.log(spec @ FB.T + 1e-10)
    mfcc = dct(logmel, type=2, axis=1, norm="ortho")[:, 1:14]
    d = np.gradient(mfcc, axis=0)
    F = np.hstack([mfcc, d])
    F = (F - F.mean(0)) / (F.std(0) + 1e-8)
    energy = 10 * np.log10(np.mean(frames ** 2, axis=1) + 1e-12)
    return F, energy


def dtw(A, B):
    """Classic DTW, steps (1,1),(1,0),(0,1). Returns path as list of (i, j) and mean cost."""
    C = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1))
    n, m = C.shape
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0
    for i in range(1, n + 1):
        Ci, Dp, Dc = C[i - 1], D[i - 1], D[i]
        diag_up = np.minimum(Dp[:-1], Dp[1:]) + Ci          # best of (i-1,j-1),(i-1,j) for each j
        for j in range(1, m + 1):
            v = diag_up[j - 1]
            w = Dc[j - 1] + Ci[j - 1]
            Dc[j] = v if v < w else w
    i, j, path = n, m, []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        k = np.argmin([D[i - 1, j - 1], D[i - 1, j], D[i, j - 1]])
        i, j = (i - 1, j - 1) if k == 0 else (i - 1, j) if k == 1 else (i, j - 1)
    path.reverse()
    return path, D[n, m] / len(path)


def speech_bounds(energy, thresh_db=-35):
    peak = energy.max()
    on = np.where(energy > peak + thresh_db)[0]
    return on[0] * HOP / SR, (on[-1] + 1) * HOP / SR


def align(ours_path, ref_path, words):
    xo, xr = decode(ours_path), decode(ref_path)
    Fo, Eo = features(xo)
    Fr, Er = features(xr)
    path, cost = dtw(Fr, Fo)
    ref2ours = {}
    for r, o in path:
        ref2ours.setdefault(r, []).append(o)
    rmax = len(Fr) - 1

    def mp(t):
        r = int(round(t * SR / HOP))
        r = min(max(r, 0), rmax)
        while r not in ref2ours and r > 0:
            r -= 1
        return float(np.median(ref2ours[r])) * HOP / SR

    out = [dict(text=w["text"], start=round(mp(w["start"]), 3), end=round(mp(w["end"]), 3)) for w in words]
    # the transcriber pins the first word at 0.0; use the measured onset of our file instead when it is later
    on, off = speech_bounds(Eo)
    raw_first = out[0]["start"]
    out[0]["start"] = round(max(out[0]["start"], on), 3)
    # the transcriber stretches a word before punctuation across the pause after it; end the word where
    # a measured silence (>= 120 ms, 35 dB under peak) begins, so "end" means end of sound
    q = Eo < (Eo.max() - 35)
    sil, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]:
                j += 1
            if (j - i) * HOP / SR >= 0.12:
                sil.append((i * HOP / SR, j * HOP / SR))
            i = j
        else:
            i += 1
    for k, w in enumerate(out):
        nxt = out[k + 1]["start"] if k + 1 < len(out) else off + 0.5
        for s, e in sil:
            if w["start"] + 0.05 < s < w["end"] and e >= min(w["end"], nxt) - 0.05:
                w["end"] = round(s, 3)
                break
    out[-1]["end"] = round(min(out[-1]["end"], off), 3)
    # QC
    quiet = Eo < (Eo.max() - 30)
    hits, tot = 0, 0
    for a, b in zip(words, words[1:]):
        if b["start"] - a["end"] >= 0.18:
            tot += 1
            mid = (mp(a["end"]) + mp(b["start"])) / 2
            f = int(mid * SR / HOP)
            win = quiet[max(f - 3, 0): f + 4]
            hits += bool(win.any())
    qc = dict(path_cost=round(cost, 3), onset_err=round(raw_first - on, 3), offset_err=round(out[-1]["end"] - off, 3),
              pause_hits=f"{hits}/{tot}", file_dur=round(len(xo) / SR, 3))
    return out, qc


if __name__ == "__main__":
    ours_dir, ref_dir, tx_path, out_path = sys.argv[1:5]
    tx = json.load(open(tx_path))
    result, qcs = {}, {}
    for beat, words in tx.items():
        words = [w for w in words if w.get("type", "word") == "word"]
        result[beat], qcs[beat] = align(f"{ours_dir}/{beat}.mp3", f"{ref_dir}/REF_{beat}.mp3", words)
        print(beat, qcs[beat], flush=True)
    result["_qc"] = qcs
    json.dump(result, open(out_path, "w"), indent=1)
