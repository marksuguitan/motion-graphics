"""Pulsus paradoxus tap cues for the Pulsus Paradoxus video (Medzcool).

Reuses the K-sound model from Korotkoff Sounds/audio/korotkoff_sound_pack/korotkoff_synth.py
(k_sound, PHASES, speaker_mix, stethoscope_ambience). What is new is the patient: systolic
pressure swings with breathing, 132 mmHg on expiration and 116 mmHg on inspiration
(the illustrative 16 mmHg pulsus approved by Mark 2026-10-22). A beat is heard when the
cuff pressure is below that beat's systolic pressure.

Cue A  (Scene 1, 1A): cuff held at 125 mmHg, so taps are heard on expiration and vanish on
                      inspiration. Loop length set from the measured 1A VO.
Cue B  (Scene 5, 5B-5E): cuff deflates from 145 mmHg at RATE mmHg/s. First taps (expiration
                      only) at 132, taps on every beat once the cuff is below 116.

Usage: python3 pulsus_synth.py <korotkoff_synth.py dir> <out dir> <timeline.json>
The timeline (from build_animatic.py) gives the start times of 1A, 5B, 5C, 5D, 5E, 5F so
the breath cycle and deflation are placed against the real VO.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, sys.argv[1])
import korotkoff_synth as ks  # noqa: E402

SR = ks.SR
HR = 76                 # beats/min
BREATH = 5.0            # s per breath (12/min), normal tidal breathing
INSP_FRAC = 0.4         # inspiration = 2.0 s, expiration = 3.0 s
SBP_EXP, SBP_INSP, DBP = 132.0, 116.0, 78.0
RATE = 2.0              # mmHg/s cuff deflation (within the standard 2-3 mmHg/s)


def breath_state(t, t0):
    """'IN' or 'OUT' at time t; the cycle starts with expiration at t0."""
    ph = ((t - t0) % BREATH) / BREATH
    return "OUT" if ph < (1 - INSP_FRAC) else "IN"


def sbp_at(t, t0):
    """Systolic pressure for a beat at time t: smooth swing between 132 and 116."""
    ph = ((t - t0) % BREATH) / BREATH
    # 0..0.6 expiration (high), 0.6..1.0 inspiration (low), 0.15-s style ramps
    exp_w = 1 - INSP_FRAC
    ramp = 0.06
    if ph < ramp:
        w = ph / ramp
    elif ph < exp_w - ramp:
        w = 1
    elif ph < exp_w:
        w = (exp_w - ph) / ramp
    else:
        w = 0
    return SBP_INSP + (SBP_EXP - SBP_INSP) * w


def render(duration, cuff_fn, breath_t0, log_name, out_dir):
    n = int(duration * SR)
    out = np.zeros(n + SR)
    log, t = [], 0.4
    period = 60.0 / HR
    while t < duration - 0.3:
        p = cuff_fn(t)
        sbp = sbp_at(t, breath_t0)
        heard = p < sbp
        if heard:
            prm = dict(ks.PHASES["I"])
            # louder the further the cuff is below this beat's systolic, like real phase I
            prm["amp"] *= 0.45 + 0.55 * np.clip((sbp - p) / 8.0, 0, 1)
            prm["amp"] *= 1 + ks.RNG.normal(0, 0.05)
            s = ks.k_sound(prm)
            i = int(t * SR)
            out[i:i + len(s)] += s
        log.append(dict(time_s=round(t, 3), cuff_mmHg=round(p, 1), sbp_mmHg=round(sbp, 1),
                        breath=breath_state(t, breath_t0), audible=bool(heard)))
        t += period * (1 + ks.RNG.normal(0, 0.02))
    out = out[:n] + ks.stethoscope_ambience(n)
    f = int(0.05 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    ks.write_wav(os.path.join(out_dir, log_name + ".wav"), ks.speaker_mix(out))
    with open(os.path.join(out_dir, log_name + "_beats.json"), "w") as fh:
        json.dump(log, fh, indent=1)
    return log


def main():
    _, _, out_dir, tl_path = sys.argv
    os.makedirs(out_dir, exist_ok=True)
    tl = {b["id"]: b for b in json.load(open(tl_path))["beats"]}

    # Cue A: under 1A only (plus a short lead-in), cuff fixed at 125 mmHg.
    a_len = tl["1A"]["end"] + 0.6
    logA = render(a_len, lambda t: 125.0, breath_t0=0.0, log_name="cueA_1A", out_dir=out_dir)

    # Cue B: starts at 5B. Deflation timed so the first expiratory tap lands just after 5C
    # begins and taps through the whole breath arrive while 5D is being spoken.
    b0 = tl["5B"]["start"]
    t_first = tl["5C"]["start"] - b0 + 0.4          # first audible tap target (cue time)
    start_p = SBP_EXP + RATE * t_first             # cuff pressure at cue start
    b_len = tl["5F"]["start"] - b0
    # put an expiration window around t_first
    breath_t0 = t_first - 0.5
    cuff = lambda t: max(start_p - RATE * t, 100.0)
    logB = render(b_len, cuff, breath_t0, "cueB_5B-5E", out_dir)

    def first(log, cond):
        for b in log:
            if cond(b):
                return b
    fexp = first(logB, lambda b: b["audible"])
    finsp = first(logB, lambda b: b["audible"] and b["breath"] == "IN")
    # "every beat": first time every beat in one full breath is audible
    allbeat = None
    for i, b in enumerate(logB):
        window = [x for x in logB if b["time_s"] <= x["time_s"] < b["time_s"] + BREATH]
        if window and all(x["audible"] for x in window):
            allbeat = b
            break
    markers = dict(
        patient=dict(sbp_expiration=SBP_EXP, sbp_inspiration=SBP_INSP, dbp=DBP, hr=HR,
                     breath_s=BREATH, inspiration_s=BREATH * INSP_FRAC),
        cueA=dict(file="cueA_1A.wav", cuff_mmHg=125, starts_at_s=0.0,
                  breath_bands=[[round(k * BREATH + BREATH * (1 - INSP_FRAC), 2), round((k + 1) * BREATH, 2)]
                                for k in range(int(a_len // BREATH) + 1)]),
        cueB=dict(file="cueB_5B-5E.wav", starts_at_video_s=round(b0, 3), start_cuff_mmHg=round(start_p, 1),
                  rate_mmHg_s=RATE,
                  first_tap_expiration=dict(cue_s=fexp["time_s"], video_s=round(b0 + fexp["time_s"], 3), cuff=fexp["cuff_mmHg"]),
                  first_tap_inspiration=dict(cue_s=finsp["time_s"], video_s=round(b0 + finsp["time_s"], 3), cuff=finsp["cuff_mmHg"]),
                  taps_every_beat_from=dict(cue_s=allbeat["time_s"], video_s=round(b0 + allbeat["time_s"], 3), cuff=allbeat["cuff_mmHg"]) if allbeat else None,
                  breath_t0_cue_s=round(breath_t0, 3)))
    with open(os.path.join(out_dir, "markers.json"), "w") as fh:
        json.dump(markers, fh, indent=2)
    print(json.dumps(markers, indent=1))


if __name__ == "__main__":
    main()
