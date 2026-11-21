"""Generate LAST LIGHT's sound library: every effect, ambience loop and music cue, synthesised here.

python3 -I tools/audio/make_sounds.py <project dir> [only=name,name]      (needs numpy, scipy, soundfile)

Everything is built from first principles at 44.1 kHz: filtered noise and granular textures for
footsteps, rain and rustles; modal resonators (sums of decaying partials) for wood, metal and glass;
a glottal source shaped by vowel formants for the infected's voices; layered transients, bodies and
outdoor echoes for guns; and a small set of synthesised instruments (felt piano, pads, bowed strings,
bells) for the original music, all through a convolution reverb built from shaped noise.
Short effects are written as 16-bit WAV in assets/audio/sfx (several takes each, so nothing repeats
exactly); loops and music as Ogg Vorbis in assets/audio/loops and assets/audio/music.
assets/audio/manifest.json lists them for the game.
"""
import sys, os, json, math
import numpy as np
import scipy.signal as ss
import soundfile as sf

SR = 44100
root = sys.argv[1]
only = []
for a in sys.argv[2:]:
    if a.startswith("only="):
        only = a[5:].split(",")
OUT = os.path.join(root, "assets/audio")
for d in ("sfx", "loops", "music"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
rng = np.random.default_rng(20261121)
MAN = {"sounds": {}, "loops": {}, "music": {}}
mpath = os.path.join(OUT, "manifest.json")
if only and os.path.exists(mpath):
    MAN = json.load(open(mpath))


# ------------------------------------------------------------------ building blocks
def N(d):
    return max(1, int(round(d * SR)))


def T(d):
    return np.arange(N(d)) / SR


def white(d):
    return rng.standard_normal(N(d))


def pink(d):
    n = N(d)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    y = np.fft.irfft(X / np.sqrt(f), n)
    return y / (np.max(np.abs(y)) + 1e-9)


def brown(d):
    y = np.cumsum(rng.standard_normal(N(d)))
    y = ss.sosfilt(ss.butter(1, 15, "hp", fs=SR, output="sos"), y)
    return y / (np.max(np.abs(y)) + 1e-9)


def _sos(kind, f, o):
    if kind == "bp":
        lo, hi = max(20, f[0]), min(SR * 0.45, f[1])
        return ss.butter(o, [lo, hi], "bandpass", fs=SR, output="sos")
    return ss.butter(o, min(max(f, 20), SR * 0.45), kind, fs=SR, output="sos")


def lp(x, f, o=2):
    return ss.sosfilt(_sos("lowpass", f, o), x)


def hp(x, f, o=2):
    return ss.sosfilt(_sos("highpass", f, o), x)


def bp(x, lo, hi, o=2):
    return ss.sosfilt(_sos("bp", (lo, hi), o), x)


def reson(x, f, q):
    """a resonant peak (2-pole) at f with quality q"""
    b, a = ss.iirpeak(min(f, SR * 0.45), q, fs=SR)
    return ss.lfilter(b, a, x)


def decay(d, tau, attack=0.0005):
    t = T(d)
    e = np.exp(-t / max(tau, 1e-4))
    if attack > 0:
        e *= np.minimum(1.0, t / attack)
    return e


def place(dst, src, at, gain=1.0):
    i = int(at * SR)
    if i >= len(dst):
        return dst
    j = min(len(dst), i + len(src))
    dst[i:j] += src[: j - i] * gain
    return dst


def modal(d, modes, phase_rand=True):
    """sum of decaying partials: [(freq, tau, amp)]"""
    t = T(d)
    y = np.zeros_like(t)
    for f, tau, a in modes:
        ph = rng.uniform(0, 2 * np.pi) if phase_rand else 0.0
        y += a * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + ph)
    return y


def tick(d=0.004, lo=2000, hi=9000):
    return bp(white(d) * decay(d, d / 3), lo, hi)


def grains(d, count, lo, hi, glen=(0.001, 0.004), amp=(0.3, 1.0), dens_curve=None):
    """a crunch: many tiny noise bursts"""
    y = np.zeros(N(d))
    for _ in range(int(count)):
        u = rng.random()
        if dens_curve == "front":
            u = u ** 2
        at = u * d * 0.95
        gl = rng.uniform(*glen)
        g = white(gl) * decay(gl, gl / 3)
        place(y, g, at, rng.uniform(*amp))
    return bp(y, lo, hi)


def mix(*parts):
    """sum sounds of different lengths (each zero-padded to the longest)"""
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out


def fade(x, fin=0.002, fout=0.012):
    x = x.copy()
    a, b = N(fin), min(N(fout), len(x) // 3)
    x[:a] *= np.linspace(0, 1, a)
    if b > 1:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def norm(x, peak=0.89):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 1e-9 else x


def rms_norm(x, db=-20.0):
    r = np.sqrt(np.mean(x ** 2)) + 1e-9
    y = x * (10 ** (db / 20) / r)
    m = np.max(np.abs(y))
    return y * (0.95 / m) if m > 0.95 else y


def soft(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def ir(rt=1.2, bright=7000, er=True, stereo_seed=0):
    """a room/hall impulse response: early reflections and a noise tail that darkens as it decays"""
    n = N(rt * 1.3)
    r = np.random.default_rng(777 + stereo_seed)
    t = np.arange(n) / SR
    tail = r.standard_normal(n) * np.exp(-6.9 * t / rt)
    seg = 4
    out = np.zeros(n)
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg
        fc = bright * (0.55 ** k)
        out[a:b] = lp(tail, fc)[a:b]
    if er:
        for _ in range(8):
            out[int(r.uniform(0.005, 0.05) * SR)] += r.uniform(-0.6, 0.6)
    out[0] = 0.0
    return out / (np.sqrt(np.sum(out ** 2)) + 1e-9)


def reverb(x, rt=1.0, wet=0.2, bright=7000, tail=True, seed=0):
    h = ir(rt, bright, True, seed)
    y = ss.fftconvolve(x, h)
    if not tail:
        y = y[: len(x)]
    dry = np.zeros(len(y))
    dry[: len(x)] = x
    return dry * (1 - wet * 0.5) + y * wet


def glottal(d, f0, jitter=0.01, shimmer=0.08, creak=0.0, harmonics=60):
    """a voiced source: band-limited pulse train following f0 (array or number)"""
    n = N(d)
    if np.isscalar(f0):
        f0 = np.full(n, float(f0))
    f0 = np.asarray(f0)[:n]
    wob = lp(rng.standard_normal(n), 6, 1)
    wob /= np.std(wob) + 1e-9
    f = f0 * (1 + jitter * np.clip(wob, -3, 3))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(n)
    for k in range(1, harmonics + 1):
        mask = (f * k) < SR * 0.45
        y += mask * np.sin(k * ph) / (k ** 1.1)
    if shimmer > 0:
        y *= 1 + shimmer * lp(rng.standard_normal(n), 30)
    if creak > 0:
        # every other pulse weaker: a rough, creaking throat
        y *= 1 - creak * (0.5 + 0.5 * np.sign(np.sin(ph / 2)))
    return y / (np.max(np.abs(y)) + 1e-9)


VOWELS = {"a": [(730, 90), (1090, 110), (2440, 170)], "o": [(570, 80), (840, 100), (2410, 170)], "u": [(330, 70), (870, 100), (2240, 160)],
          "e": [(530, 80), (1840, 120), (2480, 170)], "uh": [(640, 90), (1190, 110), (2390, 170)], "ah_low": [(600, 110), (950, 130), (2300, 200)]}


def formant(x, vowel, gains=(1.0, 0.6, 0.25)):
    y = np.zeros_like(x)
    for (f, bw), g in zip(VOWELS[vowel], gains):
        y += g * reson(x, f, f / bw)
    return y


def morph(x, v1, v2, curve):
    return formant(x, v1) * (1 - curve) + formant(x, v2) * curve


def smooth_rand(n, rate_hz, lo=0.0, hi=1.0, seed=None):
    r = np.random.default_rng(seed) if seed is not None else rng
    k = max(2, int(n / SR * rate_hz) + 2)
    pts = r.uniform(lo, hi, k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


# ------------------------------------------------------------------ writing
def level(x, win=0.05):
    """loudness of the loudest moment: the highest RMS over any 50 ms window"""
    n = N(win)
    if len(x) <= n:
        return np.sqrt(np.mean(x ** 2)) + 1e-9
    c = np.cumsum(np.concatenate([[0.0], x ** 2]))
    return np.sqrt(np.max(c[n:] - c[:-n]) / n) + 1e-9


def master(x, db):
    """no DC, the loudest moment at `db` dBFS, peaks held under 0.95 with a soft knee"""
    x = hp(np.asarray(x, dtype=np.float64), 25, 2)
    x = x * (10 ** (db / 20) / level(x))
    pk = np.max(np.abs(x))
    if pk > 0.8:
        x = np.where(np.abs(x) > 0.8, np.sign(x) * (0.8 + 0.15 * np.tanh((np.abs(x) - 0.8) / 0.15)), x)
    return fade(x)


# how loud each effect is in the library (dBFS at its loudest moment); the game mixes from there
LOUD = {"click": -18, "pickup": -16, "equip": -16, "eat": -15, "fire": -16, "levelup": -14, "call": -12, "reload": -13}


def save_sfx(name, takes):
    if only and name not in only:
        return
    files = []
    for i, x in enumerate(takes):
        x = master(x, LOUD.get(name, -10 if not name.startswith("step_") else -13))
        # short sounds stay as WAV (instant, no decoding); long ones are Ogg Vorbis to keep the game small
        if len(x) / SR > 0.85:
            fn = "sfx/%s_%d.ogg" % (name, i)
            with sf.SoundFile(os.path.join(OUT, fn), "w", SR, 1, format="OGG", subtype="VORBIS") as f:
                for j in range(0, len(x), 4096):
                    f.write(np.clip(x[j:j + 4096], -1, 1).astype(np.float32))
        else:
            fn = "sfx/%s_%d.wav" % (name, i)
            sf.write(os.path.join(OUT, fn), np.clip(x, -1, 1).astype(np.float32), SR, subtype="PCM_16")
        files.append(fn)
    MAN["sounds"][name] = files
    print("sfx", name, len(takes), "%.2fs" % (len(takes[0]) / SR))


def loop_seamless(x, xfade=1.5):
    """fold the tail onto the start so the loop has no seam"""
    n = N(xfade)
    y = x[:-n].copy()
    w = np.linspace(0, 1, n)
    y[:n] = y[:n] * w + x[-n:] * (1 - w)
    return y


def save_ogg(kind, name, x, q=0.45):
    if only and name not in only:
        return
    fn = "%s/%s.ogg" % ("loops" if kind == "loops" else "music", name)
    data = np.clip(np.asarray(x, dtype=np.float64), -1, 1).astype(np.float32)
    # written in small blocks: libsndfile's Vorbis encoder overflows its stack on one large write
    with sf.SoundFile(os.path.join(OUT, fn), "w", SR, 1 if data.ndim == 1 else data.shape[1], format="OGG", subtype="VORBIS") as f:
        for i in range(0, data.shape[0], 4096):
            f.write(data[i:i + 4096])
    MAN[kind][name] = fn
    print(kind, name, "%.1fs" % (data.shape[0] / SR), "stereo" if data.ndim == 2 else "mono")


# ------------------------------------------------------------------ footsteps
def footstep(surface, k):
    d = 0.32
    y = np.zeros(N(d))
    toe_at = rng.uniform(0.045, 0.075)

    def strike(gain):
        if surface == "concrete":
            s = mix(hp(white(0.02) * decay(0.02, 0.0035), 900) * 0.8, lp(white(0.05) * decay(0.05, 0.016), 380) * 0.9,
                    modal(0.05, [(rng.uniform(95, 130), 0.018, 0.5)]), grains(0.04, rng.integers(5, 12), 2500, 9000, amp=(0.05, 0.2)))
        elif surface == "tile":
            s = mix(hp(white(0.015) * decay(0.015, 0.0025), 1500), modal(0.06, [(rng.uniform(1700, 2300), 0.012, 0.25), (rng.uniform(2800, 3400), 0.008, 0.15)]),
                    lp(white(0.04) * decay(0.04, 0.012), 500) * 0.6)
        elif surface == "wood":
            s = mix(lp(white(0.08) * decay(0.08, 0.02), 700) * 0.9,
                    modal(0.12, [(rng.uniform(140, 190), 0.06, 0.7), (rng.uniform(300, 360), 0.04, 0.35), (rng.uniform(820, 980), 0.018, 0.15)]),
                    hp(white(0.01) * decay(0.01, 0.002), 1200) * 0.35)
        elif surface == "carpet":
            s = mix(lp(white(0.08) * decay(0.08, 0.025), 420), bp(white(0.07) * decay(0.07, 0.03, 0.01), 700, 2500) * 0.18)
        elif surface == "grass":
            s = mix(lp(white(0.05) * decay(0.05, 0.02), 220) * 0.6, grains(0.16, rng.integers(30, 60), 1800, 9000, glen=(0.0008, 0.003), amp=(0.1, 0.6)) * 0.9)
        elif surface == "dirt":
            s = mix(lp(white(0.06) * decay(0.06, 0.02), 300) * 0.8, grains(0.09, rng.integers(14, 28), 500, 3200, amp=(0.2, 0.8)) * 0.8)
        elif surface == "gravel":
            s = mix(lp(white(0.05) * decay(0.05, 0.02), 260) * 0.6, grains(0.17, rng.integers(45, 90), 1200, 7500, glen=(0.0008, 0.0035), dens_curve="front") * 1.1)
            for _ in range(4):
                place(s, modal(0.02, [(rng.uniform(3000, 6000), 0.004, 0.3)]), rng.uniform(0, 0.08))
        elif surface == "water":
            s = mix(bp(white(0.16) * decay(0.16, 0.06, 0.004), 700, 5000) * 0.6, lp(white(0.2) * decay(0.2, 0.08, 0.01), 380) * 0.6)
            for _ in range(rng.integers(4, 9)):
                bd = rng.uniform(0.012, 0.04)
                tt = T(bd)
                f0 = rng.uniform(500, 1600)
                ch = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.6 * tt / bd)) / SR) * np.exp(-tt / (bd * 0.5))
                place(s, ch * rng.uniform(0.1, 0.35), rng.uniform(0.0, 0.12))
        else:  # snow
            s = mix(grains(0.19, rng.integers(25, 45), 450, 2600, glen=(0.002, 0.006), amp=(0.2, 0.9)) * 0.9, lp(white(0.05) * decay(0.05, 0.025), 260) * 0.4)
            sq = reson(grains(0.15, 18, 900, 2200), rng.uniform(1100, 1700), 8) * 0.4
            place(s, sq, 0.02)
        return s * gain

    place(y, strike(1.0), 0.0)
    place(y, strike(0.45), toe_at)
    if surface in ("concrete", "tile", "wood") and k % 3 == 1:
        place(y, bp(white(0.05) * np.hanning(N(0.05)), 900, 4000) * 0.12, toe_at + 0.01)    # a scuff
    if surface == "wood" and k % 3 == 2:
        # a board creaks under the weight
        cr = np.zeros(N(0.18))
        t = 0.0
        while t < 0.17:
            place(cr, np.array([1.0]), t, rng.uniform(0.5, 1.0))
            t += rng.uniform(0.004, 0.011)
        cr = reson(cr, rng.uniform(650, 900), 18) + 0.6 * reson(cr, rng.uniform(1200, 1500), 22)
        place(y, cr * np.hanning(len(cr)) * 0.05, 0.05)
    y = y[: int((toe_at + 0.2) * SR)]
    return norm(y, 0.85)


# ------------------------------------------------------------------ combat
def swoosh(d, bands, peak_at, amp=1.0):
    """motion through the air: noise in several bands, each swelling at its own moment"""
    y = np.zeros(N(d))
    t = T(d)
    for (lo, hi), off, g in bands:
        e = np.exp(-((t - (peak_at + off) * d) ** 2) / (2 * (0.18 * d) ** 2))
        y += bp(white(d), lo, hi) * e * g
    return norm(y, 0.8 * amp)


def swing(kind, k):
    if kind == "blade":
        return swoosh(rng.uniform(0.15, 0.19), [((1500, 4200), -0.05, 1.0), ((3500, 8000), -0.1, 0.5), ((700, 1500), 0.08, 0.4)], 0.45)
    if kind == "heavy":
        return swoosh(rng.uniform(0.32, 0.38), [((250, 700), 0.05, 1.0), ((600, 1400), 0.0, 0.7), ((1400, 3200), -0.08, 0.3)], 0.55)
    if kind == "shove":
        y = swoosh(0.2, [((300, 900), 0.0, 1.0), ((900, 2500), -0.05, 0.3)], 0.45, 0.6)
        return y + grains(0.2, 25, 1500, 6000, amp=(0.05, 0.15))
    return swoosh(rng.uniform(0.22, 0.27), [((400, 1100), 0.04, 1.0), ((1000, 2400), -0.04, 0.6), ((2200, 5000), -0.1, 0.25)], 0.5)


def hit(kind, k):
    d = 0.5
    y = np.zeros(N(d))
    t = T(0.25)
    if kind in ("blunt", "crit", "bullet"):
        f0 = rng.uniform(95, 125) if kind != "crit" else rng.uniform(80, 95)
        thud = np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-t / 0.06) + 45) / SR) * np.exp(-t / (0.06 if kind != "crit" else 0.09))
        place(y, thud, 0.0, 1.0)
        place(y, lp(white(0.06) * decay(0.06, 0.014), 2200), 0.0, 0.8)
    if kind == "blade":
        place(y, hp(white(0.02) * decay(0.02, 0.003), 3000), 0.0, 0.9)
        place(y, bp(white(0.09) * decay(0.09, 0.035), 2000, 7000), 0.003, 0.5)
        place(y, lp(white(0.05) * decay(0.05, 0.015), 600), 0.0, 0.45)
    # the wet part: flesh giving
    sq = bp(white(0.16) * decay(0.16, 0.05, 0.008), 260, 1100) * (1 + 0.6 * lp(rng.standard_normal(N(0.16)), 40))
    place(y, reson(sq, rng.uniform(380, 620), 3) * 0.25, 0.006, 0.45 if kind != "bullet" else 0.55)
    if kind == "crit" or (kind == "blunt" and k % 3 == 2):
        # bone gives way
        for _ in range(rng.integers(4, 9) if kind == "crit" else 2):
            cr = mix(hp(white(0.006) * decay(0.006, 0.0012), 1800), modal(0.02, [(rng.uniform(1300, 3000), 0.006, 0.5)]))
            place(y, cr, rng.uniform(0.0, 0.03), 0.7)
    y = reverb(y, 0.35, 0.08)[: N(0.42)]
    return norm(soft(y, 1.3), 0.9)


def body_fall(gain=1.0):
    y = np.zeros(N(0.6))
    t = T(0.3)
    for at, g in ((0.0, 0.7), (rng.uniform(0.12, 0.2), 1.0)):
        th = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t / 0.08) + 40) / SR) * np.exp(-t / 0.09)
        place(y, th + lp(white(0.3) * decay(0.3, 0.05), 900) * 0.6, at, g * gain)
    place(y, grains(0.3, 40, 1500, 6000, amp=(0.02, 0.12)), 0.05)
    return y


def voice(d, f0, vowel_a, vowel_b, breath=0.2, creak=0.2, rattle=0.25, rough=1.6, env=None):
    n = N(d)
    src = glottal(d, f0, jitter=0.02, shimmer=0.12, creak=creak)
    curve = np.linspace(0, 1, n) ** 1.3
    v = morph(src, vowel_a, vowel_b, curve)
    br = bp(pink(d), 400, 4500) * breath
    v = v / (np.max(np.abs(v)) + 1e-9) + br
    if rattle > 0:
        v *= 1 + rattle * np.sin(2 * np.pi * rng.uniform(22, 34) * T(d)) * smooth_rand(n, 3, 0.3, 1.0)
    if env is None:
        t = T(d)
        env = np.minimum(1, t / 0.12) * np.minimum(1, (d - t) / 0.35)
    return soft(v * env, rough)


def groan(k):
    d = rng.uniform(0.9, 2.3) if k < 7 else rng.uniform(0.5, 0.8)
    n = N(d)
    base = rng.uniform(70, 100) if k % 3 else rng.uniform(100, 135)
    f0 = base * (1 + 0.12 * np.sin(np.linspace(0, rng.uniform(1.5, 4), n)) - 0.15 * np.linspace(0, 1, n))
    va, vb = [("a", "o"), ("uh", "u"), ("o", "uh"), ("ah_low", "u"), ("a", "uh")][k % 5]
    y = voice(d, f0, va, vb, breath=rng.uniform(0.15, 0.35), creak=rng.uniform(0.1, 0.5), rattle=rng.uniform(0.15, 0.4))
    return norm(reverb(y, 0.6, 0.1), 0.85)


def snarl(k):
    d = rng.uniform(0.38, 0.6)
    n = N(d)
    f0 = rng.uniform(150, 210) * (1 + 0.25 * np.sin(np.linspace(0, 3, n)))
    y = voice(d, f0, "a", "e", breath=0.5, creak=0.3, rattle=0.35, rough=2.6, env=np.minimum(1, T(d) / 0.02) * np.exp(-T(d) / (d * 0.7)))
    return norm(reverb(y, 0.4, 0.08), 0.9)


def zdie(k):
    d = 1.2
    y = np.zeros(N(d))
    g = voice(rng.uniform(0.55, 0.8), 75 * np.linspace(1.0, 0.7, N(0.8))[: N(0.8)], "uh", "u", breath=0.4, creak=0.6, rattle=0.5)
    g = g[: N(0.8)] if len(g) > N(0.8) else g
    place(y, g, 0.0, 0.6)
    place(y, body_fall(), rng.uniform(0.15, 0.3), 0.9)
    return norm(reverb(y, 0.5, 0.08)[: N(1.3)], 0.88)


def grunt(k, death=False):
    if death:
        d = 1.0
        f0 = np.linspace(135, 80, N(d))
        y = voice(d, f0, "a", "o", breath=0.45, creak=0.3, rattle=0.1, rough=1.4)
        out = np.zeros(N(1.5))
        place(out, y, 0.0, 0.7)
        place(out, body_fall(), 0.6, 0.8)
        return norm(out, 0.85)
    d = rng.uniform(0.16, 0.26)
    f0 = np.linspace(rng.uniform(150, 175), rng.uniform(105, 120), N(d))
    y = voice(d, f0, "uh", "a" if k % 2 else "uh", breath=0.9, creak=0.15, rattle=0.0, rough=1.3, env=np.minimum(1, T(d) / 0.008) * np.exp(-T(d) / (d * 0.45)))
    return norm(y, 0.8)


# ------------------------------------------------------------------ guns
def gunshot(kind, k, far=False):
    d = 2.6
    y = np.zeros(N(d))
    big = {"pistol": 1.0, "revolver": 1.25, "shotgun": 1.6, "rifle": 1.35}[kind]
    place(y, hp(white(0.006) * decay(0.006, 0.0007 if kind != "rifle" else 0.0004), 1500 if kind != "rifle" else 2800), 0.0, 1.0)
    t = T(0.4)
    boom = np.sin(2 * np.pi * np.cumsum((140 / big) * np.exp(-t / 0.03) + 45 / big) / SR) * np.exp(-t / (0.05 * big))
    place(y, boom, 0.0, 0.95)
    place(y, lp(white(0.3) * decay(0.3, 0.045 * big), 1400), 0.0, 0.8)
    place(y, bp(white(0.12) * decay(0.12, 0.022 * big), 350, 2600), 0.0, 0.55)
    if kind in ("pistol", "rifle"):
        place(y, modal(0.05, [(3100, 0.008, 0.4), (4600, 0.006, 0.3)]), 0.02, 0.25)     # the action cycling
    if kind == "shotgun":
        for at in (0.55, 0.72):                                                        # the pump
            place(y, mix(modal(0.06, [(1900, 0.012, 0.5), (3200, 0.008, 0.4)]), lp(white(0.04) * decay(0.04, 0.01), 900) * 0.4), at, 0.3)
    # outdoors: slapback off buildings, then a long darkening tail
    dry = y.copy()
    for dl, g in ((rng.uniform(0.14, 0.2), 0.28), (rng.uniform(0.3, 0.42), 0.16), (rng.uniform(0.6, 0.8), 0.08)):
        place(y, lp(dry, 2200), dl, g)
    y = reverb(y, 1.8 if kind != "rifle" else 2.4, 0.28, 4500)[: N(d)]
    if far:
        y = lp(y, 1100) * 0.9
        y = reverb(y, 2.0, 0.4, 2500)[: N(d)]
    return norm(soft(y, 2.0), 0.95)


# ------------------------------------------------------------------ the built world
def wood_knock(gain=1.0, low=1.0):
    t = T(0.4)
    th = np.sin(2 * np.pi * np.cumsum(85 * low * np.exp(-t / 0.05) + 55 * low) / SR) * np.exp(-t / 0.07)
    m = modal(0.4, [(rng.uniform(135, 155) * low, 0.12, 0.6), (rng.uniform(220, 250) * low, 0.09, 0.4), (rng.uniform(360, 400), 0.06, 0.3), (rng.uniform(590, 650), 0.04, 0.2)])
    return (th * 0.9 + m * 0.6 + lp(white(0.4) * decay(0.4, 0.02), 1500) * 0.5) * gain


def thump(k):
    y = np.zeros(N(0.6))
    place(y, wood_knock(1.0, rng.uniform(0.85, 1.1)), 0.0)
    place(y, grains(0.15, 12, 2500, 8000, amp=(0.05, 0.2)), 0.01, 0.6)   # the frame rattles
    return norm(reverb(y, 0.5, 0.1)[: N(0.65)], 0.9)


def door(k):
    d = 0.9
    y = np.zeros(N(d))
    click = modal(0.03, [(rng.uniform(2600, 3000), 0.006, 0.5), (rng.uniform(4000, 4400), 0.004, 0.4)])
    if k < 3:   # opening: the latch, then the hinge creaks
        place(y, click, 0.0, 0.5)
        place(y, click, 0.05, 0.35)
        cr = np.zeros(N(0.55))
        t = 0.0
        rate = rng.uniform(0.006, 0.012)
        while t < 0.53:
            place(cr, np.array([1.0]), t, rng.uniform(0.4, 1.0))
            t += rate * rng.uniform(0.7, 1.3)
            rate *= rng.uniform(0.985, 1.02)
        cr = reson(cr, rng.uniform(420, 520), 14) + 0.7 * reson(cr, rng.uniform(760, 900), 18) + 0.3 * reson(cr, rng.uniform(1250, 1450), 24)
        place(y, cr * np.sin(np.linspace(0, np.pi, len(cr))) * 0.6, 0.08)
    else:       # closing: air, a thud, the latch catching
        place(y, bp(white(0.15) * np.hanning(N(0.15)), 300, 1500) * 0.2, 0.0)
        place(y, wood_knock(0.9, 1.15), 0.14)
        place(y, click, 0.16, 0.45)
    return norm(reverb(y, 0.45, 0.1)[: N(d)], 0.85)


def locked(k):
    y = np.zeros(N(0.5))
    for i in range(rng.integers(3, 5)):
        place(y, modal(0.05, [(rng.uniform(1700, 1950), 0.015, 0.5), (rng.uniform(2900, 3300), 0.01, 0.4), (rng.uniform(4300, 4700), 0.007, 0.3)]), i * rng.uniform(0.07, 0.09), rng.uniform(0.6, 1.0))
    place(y, wood_knock(0.25, 1.3), 0.02)
    return norm(y, 0.8)


def splinter(k):
    d = 1.1
    y = np.zeros(N(d))
    place(y, hp(white(0.06) * decay(0.06, 0.014), 300), 0.0, 1.0)
    place(y, wood_knock(0.9, 0.9), 0.0)
    for i in range(rng.integers(60, 120)):
        at = (rng.random() ** 2) * 0.55
        g = mix(hp(white(0.004) * decay(0.004, 0.001), 900), modal(0.03, [(rng.uniform(600, 1900), 0.008, 0.6)]))
        place(y, g, at, rng.uniform(0.15, 0.6) * (1 - at))
    for _ in range(rng.integers(2, 4)):
        place(y, wood_knock(0.5, rng.uniform(0.7, 1.2)), rng.uniform(0.15, 0.55))
    return norm(reverb(y, 0.6, 0.12)[: N(d)], 0.9)


def glass(k, far=False):
    d = 1.3
    y = np.zeros(N(d))
    place(y, hp(white(0.05) * decay(0.05, 0.01), 1500), 0.0, 0.9)
    for i in range(rng.integers(35, 70)):
        at = (rng.random() ** 2.2) * 0.9
        shard = modal(0.4, [(rng.uniform(2200, 9000), rng.uniform(0.02, 0.18), 1.0), (rng.uniform(2200, 9000), rng.uniform(0.02, 0.1), 0.5)])
        place(y, shard, at, rng.uniform(0.05, 0.35) * (1.2 - at))
    y = reverb(y, 0.5, 0.12)[: N(d)]
    if far:
        y = reverb(lp(y, 1400), 1.8, 0.45, 2500)[: N(d + 0.8)]
    return norm(y, 0.85)


def hammer(k):
    y = np.zeros(N(0.5))
    if k == 3:   # a few strokes of a saw
        for i in range(3):
            st = bp(white(0.16), 1800, 6000) * np.sin(np.linspace(0, np.pi, N(0.16))) * (1 + 0.6 * np.sin(2 * np.pi * 70 * T(0.16)))
            place(y, st, i * 0.16, 0.6)
        return norm(y, 0.8)
    place(y, modal(0.3, [(rng.uniform(2300, 2600), 0.03, 0.6), (rng.uniform(3800, 4100), 0.02, 0.4), (rng.uniform(5000, 5400), 0.012, 0.3)]), 0.0, 0.8)
    place(y, wood_knock(0.6, 1.3), 0.0)
    place(y, modal(0.25, [(rng.uniform(1500, 1700), 0.06, 0.3)]), 0.002, 0.5)
    return norm(reverb(y, 0.4, 0.1)[: N(0.5)], 0.88)


def rustle(k):
    d = rng.uniform(0.18, 0.3)
    y = grains(d, rng.integers(40, 80), 1200, 7000, glen=(0.002, 0.006), amp=(0.1, 0.6)) * np.sin(np.linspace(0, np.pi, N(d)))
    if k % 2:
        place(y, modal(0.08, [(rng.uniform(2000, 3500), 0.02, 0.4)]), d * 0.5, 0.4)   # something small knocks
    return norm(y, 0.7)


def zipper(k):
    d = 0.32
    y = np.zeros(N(d))
    t = 0.0
    gap = 0.012
    while t < d - 0.01:
        place(y, tick(0.003, 2000, 7000), t, rng.uniform(0.4, 1.0))
        t += gap
        gap *= 0.97
    return norm(y + grains(d, 20, 1000, 4000, amp=(0.05, 0.15)), 0.7)


def reload(k):
    y = np.zeros(N(0.7))
    for at, f in ((0.0, 2600), (0.22, 3400), (0.42, 2900), (0.5, 4200)):
        place(y, mix(modal(0.06, [(f * rng.uniform(0.95, 1.05), 0.012, 0.6), (f * 1.6, 0.008, 0.4)]), lp(white(0.03) * decay(0.03, 0.006), 1200) * 0.3), at, rng.uniform(0.6, 1.0))
    return norm(y, 0.8)


def ui_click(k):
    return norm(modal(0.03, [(2200, 0.004, 0.6), (3500, 0.003, 0.3)]) + hp(white(0.03) * decay(0.03, 0.002), 3000) * 0.2, 0.6)


def bite(k):
    y = np.zeros(N(0.6))
    for i in range(2):
        place(y, mix(grains(0.08, rng.integers(15, 28), 900, 5500, glen=(0.002, 0.006)), lp(white(0.06) * decay(0.06, 0.02), 300) * 0.5), i * rng.uniform(0.22, 0.3), 1.0 - i * 0.3)
    return norm(y, 0.75)


def thunder(k):
    d = 4.5
    y = np.zeros(N(d))
    place(y, hp(white(0.4) * decay(0.4, 0.05), 200) * 0.8, rng.uniform(0.0, 0.2))
    place(y, grains(0.5, 80, 300, 4000, glen=(0.002, 0.01)), 0.0, 0.6)
    rum = lp(brown(d), rng.uniform(150, 260), 3)
    env = np.zeros(N(d))
    for _ in range(rng.integers(4, 8)):
        at = rng.uniform(0.1, 3.0)
        env += np.exp(-np.maximum(0, T(d) - at) / rng.uniform(0.3, 1.0)) * (T(d) > at) * rng.uniform(0.4, 1.0)
    y += rum * env * 1.2
    return norm(reverb(y, 2.5, 0.3, 2000)[: N(d + 0.5)], 0.95)


def whistle(k):
    d = 0.55
    n = N(d)
    f = np.interp(np.linspace(0, 1, n), [0, 0.35, 0.5, 1.0], [1750, 2350, 2350, 1900]) * (1 + 0.01 * np.sin(2 * np.pi * 6 * T(d)))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, T(d) / 0.03) * np.minimum(1, (d - T(d)) / 0.08)
    y += bp(white(d), 1500, 3000) * 0.06
    return norm(reverb(y, 0.8, 0.15)[: N(0.8)], 0.7)


def chime(k):
    d = 1.4
    y = np.zeros(N(d))
    for i, f in enumerate((1046.5, 1568.0)):
        t = T(d)
        bell = np.sin(2 * np.pi * f * t + 1.2 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t / 0.15)) * np.exp(-t / 0.5)
        place(y, bell, i * 0.12, 0.5)
    return norm(reverb(y, 1.2, 0.25)[: N(d)], 0.6)


def sneeze(k):
    y = np.zeros(N(1.1))
    for i in range(2):
        inh = voice(0.25, np.linspace(180, 260, N(0.25)), "a", "a", breath=1.2, rattle=0.0, rough=1.0, env=np.linspace(0.2, 1.0, N(0.25)))
        place(y, inh, i * 0.3, 0.4)
    ch = voice(0.22, np.linspace(300, 200, N(0.22)), "u", "u", breath=2.5, rattle=0.0, rough=1.5, env=np.minimum(1, T(0.22) / 0.005) * np.exp(-T(0.22) / 0.07))
    place(y, ch, 0.7, 1.0)
    return norm(y, 0.8)


def bark(k, far=True):
    d = 0.35
    y = np.zeros(N(1.4))
    for i in range(2 if k % 2 else 1):
        f0 = np.linspace(rng.uniform(420, 520), rng.uniform(260, 320), N(0.14))
        b = voice(0.14, f0, "a", "uh", breath=0.6, creak=0.2, rattle=0.0, rough=2.2, env=np.minimum(1, T(0.14) / 0.006) * np.exp(-T(0.14) / 0.06))
        place(y, b, i * 0.22, 1.0)
    if far:
        y = reverb(lp(y, 1800), 1.6, 0.35)[: N(1.6)]
    return norm(y, 0.85)


def scream(k):
    d = 1.3
    n = N(d)
    f0 = np.interp(np.linspace(0, 1, n), [0, 0.2, 0.7, 1], [480, 640, 600, 430]) * (1 + 0.02 * np.sin(2 * np.pi * 6 * T(d)))
    y = voice(d, f0, "a", "a", breath=0.4, creak=0.0, rattle=0.0, rough=1.8)
    y = reverb(lp(y, 2000), 1.8, 0.4)[: N(d + 1.2)]
    return norm(y, 0.85)


def crash_far(k):
    y = glass(k)
    m = modal(1.2, [(rng.uniform(300, 600), 0.4, 0.5), (rng.uniform(900, 1400), 0.25, 0.4), (rng.uniform(1800, 2600), 0.15, 0.3)])
    out = np.zeros(max(len(y), len(m)) + N(1.0))
    place(out, y, 0.0)
    place(out, m, 0.02)
    out = reverb(lp(out, 1500), 2.0, 0.45, 2200)
    return norm(out, 0.85)


# ------------------------------------------------------------------ ambience loops
def bed_wind():
    d = 26.0
    n = N(d)
    gust = smooth_rand(n, 0.35, 0.25, 1.0, seed=11) ** 1.5
    y = lp(brown(d), 520) * 0.9 + lp(pink(d), 1400) * 0.25
    y *= gust
    # whistling round corners, following the gusts
    wh = np.zeros(n)
    for f in (420, 560, 740):
        wh += reson(white(d), f, 35) * smooth_rand(n, 0.25, 0, 1, seed=int(f))
    y += wh / (np.max(np.abs(wh)) + 1e-9) * 0.08 * gust
    return rms_norm(loop_seamless(y, 3.0), -21)


def rain_layer(d, rate, drop_gain=1.0, muffle=None):
    n = N(d)
    y = hp(pink(d), 1400) * 0.25
    count = int(d * rate)
    for _ in range(count):
        at = rng.uniform(0, d - 0.01)
        if rng.random() < 0.3:
            bd = rng.uniform(0.004, 0.012)
            tt = T(bd)
            f0 = rng.uniform(1200, 4500)
            drop = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.8 * tt / bd)) / SR) * np.exp(-tt / (bd * 0.4))
        else:
            drop = hp(white(0.002) * decay(0.002, 0.0005), 2500)
        place(y, drop, at, rng.uniform(0.05, 0.4) * drop_gain)
    if muffle:
        y = lp(y, muffle, 3)
    return y


def bed_rain():
    return rms_norm(loop_seamless(rain_layer(16.0, 900), 2.0), -21)


def bed_rain_in():
    d = 16.0
    y = rain_layer(d, 700, 1.4, muffle=1300) * 1.6
    for _ in range(14):     # drips from the eaves
        at = rng.uniform(0, d - 0.3)
        tt = T(0.08)
        f0 = rng.uniform(900, 1800)
        drip = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.9 * tt / 0.08)) / SR) * np.exp(-tt / 0.02)
        place(y, reverb(drip, 0.5, 0.25)[: N(0.4)], at, 0.25)
    return rms_norm(loop_seamless(y, 2.0), -23)


def bed_crickets():
    d = 16.0
    y = lp(pink(d), 3000) * 0.01
    for c in range(7):
        car = rng.uniform(4100, 5400)
        rate = rng.uniform(32, 48)
        period = rng.uniform(0.45, 1.3)
        g = rng.uniform(0.15, 0.6)
        t = rng.uniform(0, period)
        while t < d - 0.3:
            pulses = rng.integers(3, 6)
            tt = T(pulses / rate)
            chirp = (np.sin(2 * np.pi * car * tt) + 0.2 * np.sin(4 * np.pi * car * tt)) * (np.sin(np.pi * (tt * rate % 1.0)) ** 2)
            place(y, chirp, t, g)
            t += period * rng.uniform(0.85, 1.15)
    return rms_norm(loop_seamless(reverb(y, 1.2, 0.2)[: N(d)], 1.5), -27)


def bird_call(kind):
    if kind == 0:     # a trill
        n_ = rng.integers(6, 14)
        out = np.zeros(N(n_ * 0.07 + 0.1))
        f = rng.uniform(3000, 5000)
        for i in range(n_):
            tt = T(0.05)
            out_s = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.25 * np.sin(np.pi * tt / 0.05))) / SR) * np.sin(np.pi * tt / 0.05)
            place(out, out_s, i * 0.065, 1.0 - i * 0.03)
        return out
    if kind == 1:     # a clear whistle, falling
        d = rng.uniform(0.4, 0.8)
        tt = T(d)
        f = np.linspace(rng.uniform(2600, 3400), rng.uniform(1800, 2400), N(d))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 0.8
    if kind == 2:     # chip-chip
        out = np.zeros(N(0.6))
        for i in range(rng.integers(2, 4)):
            tt = T(0.04)
            s = np.sin(2 * np.pi * np.cumsum(np.linspace(5000, 3500, N(0.04))) / SR) * np.sin(np.pi * tt / 0.04)
            place(out, s, i * 0.15)
        return out
    if kind == 3:     # a warble
        d = rng.uniform(0.6, 1.1)
        tt = T(d)
        f = rng.uniform(2200, 3200) + 600 * np.sin(2 * np.pi * rng.uniform(9, 14) * tt)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d)
    d = 1.4           # a dove, low and soft
    out = np.zeros(N(d))
    for i, (at, ln) in enumerate(((0.0, 0.3), (0.42, 0.25), (0.75, 0.45))):
        tt = T(ln)
        s = np.sin(2 * np.pi * np.cumsum(np.linspace(520, 470, N(ln))) / SR) * np.sin(np.pi * tt / ln)
        place(out, lp(s, 1200), at, 0.6)
    return out


def bed_birds():
    d = 24.0
    y = lp(pink(d), 2500) * 0.012
    for _ in range(26):
        c = bird_call(int(rng.integers(0, 5)))
        place(y, c, rng.uniform(0, d - 1.6), rng.uniform(0.08, 0.35))
    return rms_norm(loop_seamless(reverb(y, 1.6, 0.3)[: N(d)], 2.0), -27)


def bed_tension():
    d = 16.0
    t = T(d)
    y = np.zeros(N(d))
    for f, g in ((55.0, 0.5), (55.4, 0.4), (82.4, 0.25), (110.6, 0.12)):
        y += g * ss.sawtooth(2 * np.pi * f * t)
    y = lp(y, 300, 3) * 0.6
    beat = np.zeros(N(d))
    per = 1.0
    k = 0.0
    while k < d:
        for off, g in ((0.0, 1.0), (0.22, 0.6)):
            place(beat, np.sin(2 * np.pi * 52 * T(0.12)) * decay(0.12, 0.04), k + off, g)
        k += per
    y += beat * 0.5
    y += 0.03 * (np.sin(2 * np.pi * 1244 * t) + np.sin(2 * np.pi * 1318 * t)) * smooth_rand(N(d), 0.2, 0.2, 1.0, seed=5)
    return rms_norm(loop_seamless(reverb(y, 2.0, 0.25)[: N(d)], 1.5), -22)


# ------------------------------------------------------------------ music: synthesised instruments and original cues
def note_hz(nm):
    names = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3, "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}
    p, o = nm[:-1], int(nm[-1])
    return 440.0 * 2 ** ((names[p] + (o - 4) * 12) / 12)


def piano(f, d, vel=0.7):
    t = T(d)
    y = np.zeros(N(d))
    for k in range(1, 12):
        fk = f * k * math.sqrt(1 + 0.0004 * k * k)      # strings are a little stiff
        if fk > SR * 0.45:
            break
        y += (vel ** (0.5 + k * 0.15)) / k ** 1.1 * np.sin(2 * np.pi * fk * t) * np.exp(-t / (1.8 / (1 + 0.35 * k) * (220 / max(f, 110)) ** 0.3))
    place(y, lp(white(0.02) * decay(0.02, 0.004), 2500) * 0.05 * vel, 0.0)
    return y * np.minimum(1, t / 0.003)


def pad(freqs, d, bright=1200, att=1.6, rel=2.0):
    t = T(d)
    y = np.zeros(N(d))
    for f in freqs:
        for det in (-0.004, 0.0, 0.0045):
            y += ss.sawtooth(2 * np.pi * f * (1 + det) * t + rng.uniform(0, 6))
    y = lp(y, bright, 2)
    env = np.minimum(1, t / att) * np.minimum(1, np.maximum(0, d - t) / rel)
    return y * env / max(1, len(freqs) * 3) * 0.9


def bowed(f, d, att=0.6):
    t = T(d)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.8)
    y = ss.sawtooth(2 * np.pi * np.cumsum(f * vib) / SR)
    y = lp(y, 1600, 2) + bp(white(d), 1500, 4000) * 0.015
    return y * np.minimum(1, t / att) * np.minimum(1, np.maximum(0, d - t) / 0.8) * 0.5


def bell(f, d):
    t = T(d)
    return np.sin(2 * np.pi * f * t + 1.4 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t / 0.3)) * np.exp(-t / 1.4) * 0.4


def stereo_hall(x, rt=3.2, wet=0.38):
    l = reverb(x, rt, wet, 6000, seed=1)
    r = reverb(x, rt, wet, 6000, seed=2)
    n = max(len(l), len(r))
    out = np.zeros((n, 2))
    out[: len(l), 0] = l
    out[: len(r), 1] = r
    return out


def compose(beat, bars, chords, melody, arp=True, cello=None, bells=None, bright=1100):
    """bars of chords (lists of note names), a melody of (bar position in beats, note, beats) and optional layers"""
    bar = beat * 4
    d = bars * bar + 4.0
    y = np.zeros(N(d))
    for i in range(bars):
        ch = chords[i % len(chords)]
        place(y, pad([note_hz(n) for n in ch], bar + 1.5, bright), i * bar, 0.55)
        place(y, np.sin(2 * np.pi * note_hz(ch[0][:-1] + "2") * T(bar)) * np.minimum(1, T(bar) / 0.3) * np.minimum(1, (bar - T(bar)) / 0.5), i * bar, 0.18)
        if arp:
            pat = [ch[0], ch[1], ch[2], ch[1], ch[0], ch[2], ch[1], ch[2]]
            for j, nm in enumerate(pat):
                o = int(nm[-1]) + 1
                place(y, piano(note_hz(nm[:-1] + str(o)), 2.5, 0.35 + 0.1 * (j == 0)), i * bar + j * beat * 0.5, 0.22)
    for at, nm, ln in melody:
        place(y, piano(note_hz(nm), max(2.5, ln * beat + 1.0), 0.75), at * beat, 0.42)
    if cello:
        for at, nm, ln in cello:
            place(y, bowed(note_hz(nm), ln * beat), at * beat, 0.3)
    if bells:
        for at, nm in bells:
            place(y, bell(note_hz(nm), 3.0), at * beat, 0.25)
    return y


def music_title():
    beat = 60 / 68
    chords = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C3", "E3", "G3"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"], ["D3", "F3", "A3"], ["E3", "G#3", "B3"]]
    mel = [(32, "E5", 2), (34, "D5", 1), (35, "C5", 1), (36, "B4", 2), (38, "C5", 2), (40, "A4", 3), (44, "C5", 2), (46, "B4", 1), (47, "G4", 1), (48, "A4", 4),
           (52, "E5", 2), (54, "F5", 1), (55, "E5", 1), (56, "D5", 2), (58, "C5", 2), (60, "B4", 3), (63, "G#4", 1)]
    cel = [(32, "A2", 4), (36, "F2", 4), (40, "C3", 4), (44, "G2", 4), (48, "A2", 4), (52, "F2", 4), (56, "D2", 4), (60, "E2", 4)]
    y = compose(beat, 16, chords, mel, cello=cel, bells=[(0, "E6"), (16, "A5"), (48, "E6")])
    return stereo_hall(rms_norm(y, -19), 3.4, 0.4)


def music_dawn():
    beat = 60 / 72
    chords = [["C4", "E4", "B4"], ["A3", "C4", "G4"], ["F3", "A3", "E4"], ["G3", "B3", "D4"]]
    mel = [(1, "G5", 1), (2, "E5", 1), (3, "C5", 2), (5, "D5", 1), (6, "E5", 2), (8, "C5", 3), (13, "A4", 1), (14, "C5", 1), (15, "G5", 3)]
    y = compose(beat, 8, chords, mel, bells=[(0, "G6"), (8, "E6"), (16, "C6")], bright=1600)
    return stereo_hall(rms_norm(y, -20), 3.0, 0.35)


def music_night():
    beat = 60 / 60
    chords = [["D3", "F3", "A3"], ["Bb2", "D3", "F3"], ["G2", "Bb2", "D3"], ["A2", "C#3", "E3"]]
    mel = [(4, "A5", 2), (7, "F5", 1), (12, "D5", 3), (20, "E5", 2), (23, "C#5", 3)]
    cel = [(0, "D2", 8), (8, "G2", 8), (16, "D2", 8), (24, "A1", 8)]
    y = compose(beat, 8, chords, mel, arp=False, cello=cel, bright=800)
    return stereo_hall(rms_norm(y, -22), 3.8, 0.45)


def music_rain():
    beat = 60 / 66
    chords = [["E3", "G3", "B3"], ["C3", "E3", "B3"], ["G3", "B3", "D4"], ["D3", "F#3", "A3"]]
    mel = [(2, "B5", 1), (3, "G5", 1), (6, "E5", 2), (10, "D5", 1), (11, "B4", 1), (14, "E5", 3), (18, "F#5", 1), (19, "G5", 2), (22, "B4", 3)]
    y = compose(beat, 8, chords, mel, bright=900)
    return stereo_hall(rms_norm(y, -21), 3.2, 0.4)


def music_home():
    beat = 60 / 70
    chords = [["F3", "A3", "C4"], ["E3", "G3", "C4"], ["D3", "F3", "A3"], ["Bb2", "D3", "F3"]]
    mel = [(0, "C5", 2), (2, "A4", 1), (3, "F4", 1), (4, "G4", 3), (8, "A4", 2), (10, "F4", 2), (12, "D5", 3), (16, "C5", 2), (18, "Bb4", 2), (20, "A4", 3)]
    cel = [(0, "F2", 8), (8, "D2", 8)]
    y = compose(beat, 8, chords, mel, cello=cel, bright=1300)
    return stereo_hall(rms_norm(y, -20), 3.0, 0.35)


def music_death():
    d = 12.0
    y = np.zeros(N(d))
    place(y, bowed(note_hz("A1"), 9.0, 1.5), 0.0, 0.5)
    place(y, pad([note_hz("A2"), note_hz("C3"), note_hz("E3")], 9.0, 600, 2.0, 3.0), 0.0, 0.4)
    for i, nm in enumerate(["A4", "G4", "E4", "D4", "C4", "A3"]):
        place(y, piano(note_hz(nm), 4.0, 0.6), 0.6 + i * 1.1, 0.5)
    return stereo_hall(rms_norm(y, -21), 4.0, 0.45)


def car_door(k):
    """a car door shut: the panel's dull boom, its tinny ring and the latch"""
    y = np.zeros(N(0.7))
    t = T(0.3)
    place(y, np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t / 0.05) + 48) / SR) * np.exp(-t / 0.08), 0.0, 1.0)
    place(y, modal(0.5, [(rng.uniform(170, 200), 0.12, 0.5), (rng.uniform(390, 430), 0.08, 0.35), (rng.uniform(740, 800), 0.05, 0.25), (rng.uniform(1250, 1400), 0.03, 0.18)]), 0.0, 0.6)
    place(y, modal(0.05, [(rng.uniform(2400, 2700), 0.008, 0.6), (rng.uniform(3700, 4000), 0.006, 0.4)]), 0.012, 0.35)
    place(y, grains(0.12, 14, 2000, 7000, amp=(0.05, 0.2)), 0.01, 0.4)
    return reverb(y, 0.7, 0.14)[: N(0.8)]


def ignition(k):
    """the starter cranks, the engine catches and settles"""
    d = 2.0
    y = np.zeros(N(d))
    crank = rng.uniform(0.6, 0.85)
    t = T(crank)
    whine = np.sin(2 * np.pi * np.cumsum(np.full(N(crank), 210.0) * (1 + 0.04 * np.sin(2 * np.pi * 10 * t))) / SR)
    whine += 0.5 * np.sin(2 * np.pi * np.cumsum(np.full(N(crank), 420.0)) / SR)
    whine = lp(whine, 1800) * (0.55 + 0.45 * np.sin(2 * np.pi * 10.5 * t) ** 2) * np.minimum(1, t / 0.03)
    place(y, whine, 0.05, 0.35)
    place(y, bp(white(crank), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 10.5 * t) ** 2) * 0.08, 0.05)
    at = 0.05 + crank
    rate = 9.0
    while at < d - 0.1:
        g = min(1.0, 0.5 + (at - crank) * 0.8)
        place(y, mix(np.sin(2 * np.pi * np.cumsum(np.linspace(95, 55, N(0.05))) / SR) * decay(0.05, 0.018), lp(white(0.04) * decay(0.04, 0.009), 600) * 0.7), at, g * rng.uniform(0.75, 1.0))
        at += 1.0 / rate
        rate = min(30.0, rate * 1.12)
    y += lp(brown(d), 160) * 0.2 * np.clip((T(d) - crank) * 2, 0, 1)
    y *= np.minimum(1, (d - T(d)) / 0.4)
    return lp(y, 3000)


def shuffle(k):
    """an infected dragging a foot: a scrape that swells and fades, then the foot planted"""
    d = rng.uniform(0.45, 0.65)
    n = N(d)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.5 * (1 + 0.5 * smooth_rand(n, 12, -1, 1))
    y = bp(pink(d), 350, 2800) * env * 0.6 + grains(d, rng.integers(30, 60), 900, 5000, glen=(0.001, 0.004), amp=(0.05, 0.3)) * env
    out = np.zeros(N(d + 0.25))
    place(out, y, 0.0)
    place(out, lp(white(0.08) * decay(0.08, 0.02), 320), d * 0.92, 0.9)
    return out


def horn(k, siren=False):
    if siren:     # a police siren: a long rising and falling wail
        d = 3.0
        t = T(d)
        f = 650 + 650 * (0.5 - 0.5 * np.cos(2 * np.pi * t / 1.5))
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = lp(np.sign(np.sin(ph)) * 0.5 + np.sin(ph) * 0.5, 3200)
        y *= np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.3)
        return reverb(y, 1.6, 0.3)
    d = rng.uniform(0.7, 0.9)
    t = T(d)
    y = np.zeros(N(d))
    for f in (415.0, 523.0):                # two horns a third apart, as on most cars
        ph = 2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * f * 2 * t)
        y += np.tanh(3 * np.sin(ph)) * 0.5
    y = reson(y, 1800, 2) * 0.4 + lp(y, 2600) * 0.8
    y *= np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.04)
    return reverb(y, 1.2, 0.22)


def loop_engine():
    """a petrol engine turning over: 30 firings a second (the game raises the pitch with speed)"""
    per = 1 / 30.0
    d = 4.25
    y = np.zeros(N(d))
    k = 0
    while k * per < d:
        g = rng.uniform(0.7, 1.0)
        place(y, mix(np.sin(2 * np.pi * np.cumsum(np.linspace(95, 55, N(0.05))) / SR) * decay(0.05, 0.018), lp(white(0.04) * decay(0.04, 0.009), 600) * 0.7), k * per, g)
        place(y, bp(white(0.006) * decay(0.006, 0.0015), 2500, 7000) * 0.06, k * per + per * 0.5)   # valve tick
        k += 1
    t = T(d)
    y += lp(brown(d), 160) * 0.35 * (1 + 0.4 * np.sin(2 * np.pi * 30 * t))
    y += bp(white(d), 900, 2200) * 0.025 * (1 + 0.8 * np.sin(2 * np.pi * 30 * t))
    y = lp(y, 3000)
    return rms_norm(loop_seamless(y, 0.25), -16)


def loop_fire():
    d = 11.0
    y = lp(brown(d), 240) * 0.5 * smooth_rand(N(d), 0.5, 0.6, 1.0, seed=3) + bp(pink(d), 400, 1800) * 0.08
    for _ in range(int(d * 14)):
        pop = mix(hp(white(0.004) * decay(0.004, 0.0008), 1500), modal(0.02, [(rng.uniform(2000, 6000), 0.004, 0.4)]))
        place(y, pop, rng.uniform(0, d - 0.03), rng.uniform(0.05, 0.6) ** 1.5)
    for _ in range(int(d * 1.2)):           # a log settles, a knot bursts
        place(y, grains(0.25, 30, 700, 4000, amp=(0.1, 0.5)), rng.uniform(0, d - 0.3), rng.uniform(0.2, 0.5))
    return rms_norm(loop_seamless(y, 1.0), -20)


def loop_alarm(car=False):
    if car:       # a car alarm: a whooping sweep, 2.5 a second
        d = 4.4
        t = T(d)
        f = 700 + 900 * ((t * 2.5) % 1.0)
        xf = 0.4
    else:         # a building alarm: a piercing two-tone
        d = 4.5
        t = T(d)
        f = np.where((t % 0.5) < 0.25, 960.0, 720.0)
        xf = 0.5
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = lp(np.sign(np.sin(ph)) * 0.45 + np.sin(ph) * 0.55, 4000)
    y = reverb(y, 0.9, 0.18)[: N(d)]
    return rms_norm(loop_seamless(y, xf), -14)


def loop_rotor():
    """rotor blades overhead: 5.33 slaps a second over the turbine's whine"""
    per = 0.1875
    d = 3.375
    y = np.zeros(N(d))
    t0 = 0.0
    while t0 < d:
        place(y, mix(lp(white(0.07) * decay(0.07, 0.022), 800), np.sin(2 * np.pi * 62 * T(0.07)) * decay(0.07, 0.03)), t0, 1.0)
        t0 += per
    t = T(d)
    y += 0.07 * np.sin(2 * np.pi * 1320 * t + 2 * np.sin(2 * np.pi * 5.333 * t)) + 0.03 * np.sin(2 * np.pi * 2640 * t)
    y += lp(brown(d), 260) * 0.45
    return rms_norm(loop_seamless(y, 0.375), -15)


# ------------------------------------------------------------------ build everything
SURFACES = ["concrete", "tile", "wood", "carpet", "grass", "dirt", "gravel", "water", "snow"]
for s in SURFACES:
    save_sfx("step_" + s, [footstep(s, k) for k in range(6)])
save_sfx("swing_blunt", [swing("blunt", k) for k in range(4)])
save_sfx("swing_blade", [swing("blade", k) for k in range(4)])
save_sfx("swing_heavy", [swing("heavy", k) for k in range(3)])
save_sfx("swing_shove", [swing("shove", k) for k in range(3)])
save_sfx("hit_blunt", [hit("blunt", k) for k in range(5)])
save_sfx("hit_blade", [hit("blade", k) for k in range(4)])
save_sfx("hit_crit", [hit("crit", k) for k in range(4)])
save_sfx("hit_bullet", [hit("bullet", k) for k in range(3)])
save_sfx("groan", [groan(k) for k in range(10)])
save_sfx("snarl", [snarl(k) for k in range(4)])
save_sfx("zdie", [zdie(k) for k in range(4)])
save_sfx("hurt", [grunt(k) for k in range(5)])
save_sfx("death", [grunt(0, death=True)])
save_sfx("shot_pistol", [gunshot("pistol", k) for k in range(3)])
save_sfx("shot_revolver", [gunshot("revolver", k) for k in range(2)])
save_sfx("shot_shotgun", [gunshot("shotgun", k) for k in range(2)])
save_sfx("shot_rifle", [gunshot("rifle", k) for k in range(2)])
save_sfx("shot_far", [gunshot("rifle", k, far=True) for k in range(2)])
save_sfx("thump", [thump(k) for k in range(5)])
save_sfx("door_open", [door(k) for k in range(3)])
save_sfx("door_close", [door(k) for k in range(3, 6)])
save_sfx("car_door", [car_door(k) for k in range(3)])
save_sfx("ignition", [ignition(k) for k in range(2)])
save_sfx("locked", [locked(k) for k in range(3)])
save_sfx("break", [splinter(k) for k in range(4)])
save_sfx("glass", [glass(k) for k in range(4)])
save_sfx("build", [hammer(k) for k in range(4)])
save_sfx("pickup", [rustle(k) for k in range(5)])
save_sfx("equip", [zipper(k) for k in range(2)])
save_sfx("reload", [reload(k) for k in range(2)])
save_sfx("click", [ui_click(0)])
save_sfx("eat", [bite(k) for k in range(3)])
save_sfx("thunder", [thunder(k) for k in range(3)])
save_sfx("call", [whistle(0)])
save_sfx("levelup", [chime(0)])
save_sfx("sneeze", [sneeze(0)])
save_sfx("bark", [bark(k) for k in range(3)])
save_sfx("scream", [scream(k) for k in range(2)])
save_sfx("crash_far", [crash_far(k) for k in range(2)])
save_sfx("shuffle", [shuffle(k) for k in range(6)])
save_sfx("horn", [horn(k) for k in range(2)])
save_sfx("siren", [horn(0, siren=True)])
for name, fn in (("bed_wind", bed_wind), ("bed_rain", bed_rain), ("bed_rain_in", bed_rain_in), ("bed_crickets", bed_crickets), ("bed_birds", bed_birds), ("bed_tension", bed_tension),
                 ("loop_engine", loop_engine), ("loop_fire", loop_fire), ("loop_alarm", loop_alarm), ("loop_caralarm", lambda: loop_alarm(True)), ("loop_rotor", loop_rotor)):
    if not only or name in only:
        save_ogg("loops", name, fn())
for name, fn in (("title", music_title), ("dawn", music_dawn), ("night", music_night), ("rain", music_rain), ("home", music_home), ("death", music_death)):
    if not only or name in only:
        save_ogg("music", name, fn())
json.dump(MAN, open(mpath, "w"), indent=1)
print("manifest:", len(MAN["sounds"]), "effects,", len(MAN["loops"]), "loops,", len(MAN["music"]), "music cues")
