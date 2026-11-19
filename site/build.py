#!/usr/bin/env python3
"""Build lwa.avisha.ai into site/public/ from template.html + episodes.json.

    python3 site/build.py

Rolling hero: section 2 shows the most recent episode whose status is
'released' or 'dropping_soon'. Every other released episode is listed in the
episode index with a WATCH link. No video host other than this site is linked.
"""
import json, shutil, sys
from html import escape as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLIC = HERE / "public"
SITE_URL = "https://lwa.avisha.ai/"
DESCRIPTION = ("Short animated explainers on chemical engineering: real equipment, "
               "real phenomena, explained clearly. Free, always.")
FEATURABLE = ("released", "dropping_soon")

# Keeps the silent 3D video in step with the 2D episode: play, pause, seek and speed follow the 2D player;
# clicking the 3D view plays/pauses the episode.
SYNC_3D_JS = ("(()=>{const m=document.getElementById('feat-2d'),d=document.getElementById('feat-3d');"
              "if(!m||!d)return;"
              "const s=()=>{if(Math.abs(d.currentTime-m.currentTime)>0.3)d.currentTime=m.currentTime};"
              "m.addEventListener('play',()=>{s();d.play().catch(()=>{})});"
              "m.addEventListener('pause',()=>d.pause());"
              "m.addEventListener('ended',()=>d.pause());"
              "m.addEventListener('seeked',s);m.addEventListener('timeupdate',s);"
              "m.addEventListener('ratechange',()=>{d.playbackRate=m.playbackRate});"
              "d.addEventListener('click',()=>{m.paused?m.play():m.pause()});})();")


def featured_html(ep, linkedin):
    released = ep["status"] == "released"
    label = f'EPISODE {E(ep["num"])} · {E(ep["subject"]).upper()}' + (" · NOW SHOWING" if released else "")
    if released:
        v = ep["video"]
        poster = f' poster="{E(v["poster"])}"' if v.get("poster") else ""
        track = (f'<track kind="captions" src="{E(v["vtt"])}" srclang="en" label="English">'
                 if v.get("vtt") else "")
        card_label = f'Episode {E(ep["num"])} · ' + (f'The {E(ep["series"])}' if ep.get("series") else E(ep["subject"]))
        main_video = (f'          <div class="feat-video-wrap">\n'
                      f'            <video id="feat-2d" controls playsinline preload="none"{poster} aria-label="Episode {E(ep["num"])}: {E(ep["name"])}">\n'
                      f'              <source src="{E(v["mp4"])}" type="video/mp4">{track}\n'
                      f'            </video>\n'
                      f'          </div>\n')
        if v.get("mp4_3d"):
            # 3D equipment view to the right of the 2D episode; silent, follows the 2D player
            poster_3d = f' poster="{E(v["poster_3d"])}"' if v.get("poster_3d") else ""
            main_video = (f'          <div class="feat-video-pair">\n'
                          f'{main_video}'
                          f'          <div class="feat-video-wrap is-3d">\n'
                          f'            <video id="feat-3d" muted playsinline preload="none"{poster_3d} aria-label="3D view of the equipment, plays with the episode">\n'
                          f'              <source src="{E(v["mp4_3d"])}" type="video/mp4">\n'
                          f'            </video>\n'
                          f'          </div>\n'
                          f'          </div>\n'
                          f'          <script>{SYNC_3D_JS}</script>\n')
        action = (f'<div class="feat-video-card">\n'
                  f'          <div class="feat-video-card-label">{card_label}</div>\n'
                  f'{main_video}'
                  f'        </div>')
    else:
        action = (f'<p class="feat-soon">Episode {E(ep["num"])} — dropping soon. Follow on '
                  f'<a href="{E(linkedin)}" target="_blank" rel="noopener">LinkedIn</a> for the release.</p>')
    figure = ""
    # the 3D view replaces the side sketch; episodes without 3D keep it
    has_3d = released and bool(ep["video"].get("mp4_3d"))
    if ep.get("figure") and not has_3d:
        svg = (HERE / ep["figure"]).read_text().strip()
        svg = svg.replace("<svg ", f'<svg role="img" aria-label="{E(ep.get("figure_caption",""))}" ', 1)
        figure = (f'      <div class="feat-sketch">\n        {svg}\n'
                  f'        <div class="sketch-cap" aria-hidden="true">{E(ep.get("figure_caption",""))}</div>\n      </div>')
    return f'''    <h2 class="feat-fig" id="featured-h">FEATURED MYSTERY · EPISODE {E(ep["num"])}</h2>
    <div class="feat-inner{"" if figure else " no-fig"}" style="position:relative">
      <div class="margin-note" aria-hidden="true">EP {E(ep["num"])}<br>{E(ep["subject"]).replace(" ", "<br>")}</div>
      <div>
        <div class="feat-ep">{'<span class="live-dot"></span>' if released else ''}{label}</div>
        <h3 class="feat-q">{ep["question"]}</h3>
        <p class="feat-sub">{E(ep["summary"])}</p>
        {action}
      </div>
{figure}
    </div>'''


def row_html(ep):
    done = ep["status"] == "released"
    if done:
        right = f'<a class="cs-watch" href="{E(ep["video"]["mp4"])}" aria-label="Watch episode {E(ep["num"])}: {E(ep["name"])}">WATCH ▶</a>'
    else:
        right = f'<span class="cs-label">{"DROPPING SOON" if ep["status"] == "dropping_soon" else "COMING SOON"}</span>'
    return (f'      <div class="cs-row{" done" if done else ""}">\n'
            f'        <span class="cs-num">{E(ep["num"])}</span>\n'
            f'        <span class="cs-name">{E(ep.get("index_name") or ep["name"])}</span>\n'
            f'        <span class="cs-teaser">{E(ep.get("index_teaser") or ep["teaser"])}</span>\n'
            f'        {right}\n      </div>')


def main():
    data = json.loads((HERE / "episodes.json").read_text())
    eps = data["episodes"]
    for ep in eps:
        if ep["status"] == "released" and not (ep.get("video") or {}).get("mp4"):
            sys.exit(f'episode {ep["num"]} is released but has no video.mp4')
    cands = [e for e in eps if e["status"] in FEATURABLE]
    if not cands:
        sys.exit("no episode is released or dropping_soon — nothing to feature")
    feat = max(cands, key=lambda e: int(e["num"]))
    rows = "\n".join(row_html(e) for e in eps if e is not feat)
    live = sum(e["status"] == "released" for e in eps)

    out = (HERE / "template.html").read_text()
    for k, v in {"BASE_CSS": (HERE / "_base.css").read_text(), "FEATURED": featured_html(feat, data["linkedin"]),
                 "INDEX": rows, "LINKEDIN": E(data["linkedin"]), "TOPIC_COUNT": str(len(eps)),
                 "LIVE_COUNT": str(live), "COMING_COUNT": str(len(eps) - live),
                 "SITE_URL": SITE_URL, "DESCRIPTION": E(DESCRIPTION)}.items():
        out = out.replace("{{" + k + "}}", v)
    assert "{{" not in out, "unfilled placeholder"

    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / "index.html").write_text(out)
    for d in ("static", "media"):          # static/ → site root, media/ → /media/
        if (HERE / d).is_dir():
            shutil.copytree(HERE / d, PUBLIC if d == "static" else PUBLIC / d, dirs_exist_ok=True)
    print(f"built {PUBLIC/'index.html'} · featured EP {feat['num']} ({feat['status']}) · {len(eps)-1} index rows")


if __name__ == "__main__":
    main()
