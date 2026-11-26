import glob
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "demo" / "out"
K6 = shutil.which("k6") or r"C:\Program Files\k6\k6.exe"
FFMPEG = shutil.which("ffmpeg") or next(iter(glob.glob(os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe"))), "ffmpeg")

WIDTH, HEIGHT, FPS = 1280, 720, 15
PAD_X, HEADER_Y, BODY_Y, LINE_HEIGHT = 40, 26, 92, 36
COLORS = {
    "bg": (11, 12, 15), "ink": (236, 232, 225), "muted": (169, 176, 188),
    "orange": (255, 138, 61), "rule": (58, 65, 80),
}
FONT_PATH = next(p for p in (r"C:\Windows\Fonts\CascadiaMono.ttf", r"C:\Windows\Fonts\consola.ttf") if Path(p).exists())
FONT = ImageFont.truetype(FONT_PATH, 26)
HEADER_FONT = ImageFont.truetype(FONT_PATH, 22)
CHAR_WIDTH = FONT.getlength("M")
COLUMNS = int((WIDTH - 2 * PAD_X) // CHAR_WIDTH)
VISIBLE_LINES = (HEIGHT - BODY_Y - 20) // LINE_HEIGHT
TYPING_CPS = 32
PSQL = ["exec", "-T", "db", "psql", "-U", "lab", "-d", "shop", "-f"]


class Clip:
    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.lines = []
        self.snapshots = []
        self.t = 0.0
        self.snap()

    def snap(self, extra=None):
        self.snapshots.append((self.t, list(self.lines) + ([extra] if extra else [])))

    def cmd(self, text):
        for i in range(0, len(text) + 1, 2):
            self.snap(("cmd", text[:i]))
            self.t += 2 / TYPING_CPS
        self.lines.append(("cmd", text))
        self.snap()
        self.t += 0.4

    def out(self, text, kind="out"):
        for line in text.splitlines():
            self.lines.append((kind, line.rstrip()))
            self.snap()
            self.t += 0.07
        self.t += 0.3

    def note(self, text):
        self.out("# " + text, "note")

    def wait(self, label, seconds=2.5):
        self.lines.append(("note", f"... {label}"))
        self.snap()
        self.t += seconds

    def hold(self, seconds):
        self.t += seconds
        self.snap()


def physical_lines(lines):
    rows = []
    for kind, text in lines:
        prefix = "$ " if kind == "cmd" else ""
        wrapped = textwrap.wrap(prefix + text, COLUMNS, replace_whitespace=False, drop_whitespace=False) or [prefix]
        for i, row in enumerate(wrapped):
            rows.append((kind, row, i == 0))
    return rows[-VISIBLE_LINES:]


def render_frame(title, lines):
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg"])
    draw = ImageDraw.Draw(image)
    draw.text((PAD_X, HEADER_Y), title, font=HEADER_FONT, fill=COLORS["orange"])
    draw.line((PAD_X, 68, WIDTH - PAD_X, 68), fill=COLORS["rule"], width=2)
    for index, (kind, row, first) in enumerate(physical_lines(lines)):
        y = BODY_Y + index * LINE_HEIGHT
        if kind == "cmd" and first:
            draw.text((PAD_X, y), "$", font=FONT, fill=COLORS["orange"])
            draw.text((PAD_X + 2 * CHAR_WIDTH, y), row[2:], font=FONT, fill=COLORS["ink"])
        else:
            color = COLORS["muted"] if kind == "note" else COLORS["ink"]
            draw.text((PAD_X, y), row, font=FONT, fill=color)
    return image


def encode(clip):
    OUT.mkdir(parents=True, exist_ok=True)
    clip.hold(3)
    video = OUT / f"{clip.name}.mp4"
    ffmpeg = subprocess.Popen(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-movflags", "+faststart",
         str(video)], stdin=subprocess.PIPE)
    cache = {}
    snapshot_index = 0
    for frame in range(int(clip.t * FPS) + 1):
        now = frame / FPS
        while snapshot_index + 1 < len(clip.snapshots) and clip.snapshots[snapshot_index + 1][0] <= now:
            snapshot_index += 1
        if snapshot_index not in cache:
            cache.clear()
            cache[snapshot_index] = render_frame(clip.title, clip.snapshots[snapshot_index][1])
        ffmpeg.stdin.write(cache[snapshot_index].tobytes())
    ffmpeg.stdin.close()
    ffmpeg.wait()
    render_frame(clip.title, clip.snapshots[-1][1]).save(OUT / f"{clip.name}.png")
    print(f"{video.name}: {clip.t:.0f}s")


def run(args, check=False):
    result = subprocess.run(args, cwd=LAB, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr}")
    return result.stdout + result.stderr


def compose(env, *args):
    return run(["docker", "compose", "--env-file", f"envs/{env}.env", *args], check=True)


def compose_bg(*args, log=None):
    handle = open(log, "w", encoding="utf-8") if log else subprocess.DEVNULL
    return subprocess.Popen(["docker", "compose", "--env-file", "envs/baseline.env", *args], cwd=LAB,
                            stdout=handle, stderr=subprocess.STDOUT)


def k6_args(rate, duration, script):
    return [K6, "run", "-e", "BASE_URL=http://localhost:8080", "-e", f"RATE={rate}", "-e", f"DURATION={duration}",
            f"k6/{script}"]


def grep(text, pattern):
    return "\n".join(line.strip() for line in text.splitlines() if re.search(pattern, line))


def use_machine(env):
    compose(env, "up", "-d", "--wait")
    compose(env, "restart", "api")
    compose(env, "up", "-d", "--wait")
    time.sleep(2)


K6_METRICS = r"http_req_failed|http_req_duration\b|http_reqs|dropped_iterations"
K6_GREP = ' | grep -E "failed|duration|http_reqs|dropped"'
PSQL_ALIAS = "psql = docker compose exec -T db psql -U lab -d shop"


def show_up(clip, env):
    clip.cmd(f"docker compose --env-file envs/{env}.env up -d --wait")
    use_machine(env)
    clip.out(grep(compose(env, "ps", "--format", "{{.Service}}: {{.Status}}"), r"^(api|db|cache):"))


def show_read_load(clip, env, rate):
    clip.cmd(f"k6 run -e RATE={rate} -e DURATION=20s k6/read.js" + K6_GREP)
    output = run(k6_args(rate, "20s", "read.js"))
    clip.wait("20 s de carga (acelerado)")
    clip.out(grep(output, K6_METRICS))


def clip_baseline():
    clip = Clip("demo-1-sem-indice", "cenário 1 · sem índice · Postgres com 0,5 CPU e 512 MB")
    clip.note(PSQL_ALIAS)
    show_up(clip, "baseline")
    show_read_load(clip, "baseline", 50)
    clip.cmd('psql -f /sql/explain.sql | grep -E "Seq Scan|Removed|Execution"')
    clip.out(grep(compose("baseline", *PSQL, "/sql/explain.sql"), r"Seq Scan|Rows Removed|Execution Time"))
    encode(clip)


def clip_scale_up():
    clip = Clip("demo-2-scale-up", "cenário 2 · scale-up · Postgres com 2 CPU e 2 GB")
    show_up(clip, "scale-up")
    show_read_load(clip, "scale-up", 50)
    encode(clip)


def clip_index():
    clip = Clip("demo-3-indice", "cenário 3 · índice · de volta a 0,5 CPU e 512 MB")
    clip.note(PSQL_ALIAS)
    show_up(clip, "baseline")
    clip.cmd("psql -f /sql/index-create.sql")
    clip.out(compose("baseline", *PSQL, "/sql/index-create.sql").strip())
    show_read_load(clip, "baseline", 50)
    clip.cmd('psql -f /sql/explain.sql | grep -E "Index Scan|Execution"')
    clip.out(grep(compose("baseline", *PSQL, "/sql/explain.sql"), r"Index Scan|Execution Time"))
    encode(clip)


def show_load_with_stats(clip, env):
    clip.cmd("k6 run -e RATE=500 -e DURATION=20s k6/read.js &")
    k6 = subprocess.Popen(k6_args(500, "20s", "read.js"), cwd=LAB, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")
    time.sleep(10)
    clip.wait("10 s de carga", 1.2)
    clip.cmd('docker stats --no-stream --format "{{.Name}}: {{.CPUPerc}}"')
    clip.out(run(["docker", "stats", "--no-stream", "--format", "{{.Name}}: {{.CPUPerc}}"], check=True).strip())
    summary = k6.communicate()[0]
    clip.wait("fim dos 20 s (acelerado)", 1.5)
    clip.out(grep(summary, r"http_req_duration\b|dropped_iterations"))


def clip_cache():
    clip = Clip("demo-4-5-cache", "cenários 4 e 5 · 500 req/s · só índice x índice + Valkey")
    clip.note("só o índice; o Postgres tem limite de 0,5 CPU")
    show_load_with_stats(clip, "baseline")
    clip.note("liga o Valkey: cache-aside com TTL de 30 s")
    show_up(clip, "cache")
    compose("cache", "exec", "-T", "cache", "valkey-cli", "FLUSHALL")
    show_load_with_stats(clip, "cache")
    encode(clip)


def clip_lock(name, title, migration):
    clip = Clip(name, title)
    use_machine("baseline")
    compose("baseline", *PSQL, "/sql/migration-reset.sql")
    log = OUT / f"{name}-migration.log"
    clip.note(PSQL_ALIAS)
    clip.note("terminal 1: 20 checkouts por segundo durante 50 s")
    clip.cmd("k6 run -e RATE=20 -e DURATION=50s k6/write.js &")
    k6 = subprocess.Popen(k6_args(20, "50s", "write.js"), cwd=LAB, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")
    time.sleep(8)
    clip.wait("8 s depois", 1.2)
    clip.note("terminal 2: um relatório aberto e esquecido")
    clip.cmd("psql -f /sql/long-transaction.sql &")
    long_tx = compose_bg(*PSQL, "/sql/long-transaction.sql")
    time.sleep(4)
    clip.note("terminal 3: a migração")
    clip.cmd(f"psql -f /sql/{migration} &")
    started = time.time()
    mig = compose_bg(*PSQL, f"/sql/{migration}", log=log)
    time.sleep(6)
    clip.cmd("psql -f /sql/locks-short.sql")
    clip.out(grep(compose("baseline", *PSQL, "/sql/locks-short.sql"), r"\S"))
    mig.wait()
    clip.note(f"saída do terminal 3, depois de {time.time() - started:.0f} s:")
    clip.out(grep(log.read_text(encoding="utf-8"), r"\S"))
    summary = k6.communicate()[0]
    long_tx.wait()
    clip.wait("fim dos 50 s de carga (acelerado)")
    clip.out(grep(summary, r"http_req_failed|http_reqs"))
    compose("baseline", *PSQL, "/sql/migration-reset.sql")
    encode(clip)


CLIPS = {
    "1": lambda: clip_baseline(),
    "2": lambda: clip_scale_up(),
    "3": lambda: clip_index(),
    "4": lambda: clip_cache(),
    "6": lambda: clip_lock("demo-6-lock", "cenário 6 · migração durante o pico, sem lock_timeout",
                           "migration-unsafe.sql"),
    "7": lambda: clip_lock("demo-7-lock-timeout", "cenário 7 · a mesma migração com lock_timeout = 2s",
                           "migration-safe.sql"),
}


def main(selected):
    run(["docker", "info"], check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    compose("baseline", "up", "-d", "--build", "--wait", "--remove-orphans")
    compose("baseline", *PSQL, "/sql/migration-reset.sql")
    if "1" in selected:
        compose("baseline", *PSQL, "/sql/index-drop.sql")
    elif "4" in selected:
        compose("baseline", *PSQL, "/sql/index-create.sql")
    for key in selected:
        CLIPS[key]()
    use_machine("baseline")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or list(CLIPS)))
