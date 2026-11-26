#!/usr/bin/env python3
"""Build lwa.avisha.ai into site/public/ from template.html + episodes.json.

    python3 site/build.py

Rolling hero: section 2 shows the most recent episode whose status is
'released' or 'dropping_soon'. Every other released episode is listed in the
episode index with a WATCH link. No video host other than this site is linked.
"""
import json, re, shutil, sys
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

# WATCH in the episode index plays that episode in the featured player (2D + 3D side by side) instead of
# opening the bare 2D file; a "Back to Episode NN" button returns to the featured episode.
SWAP_JS = ("(()=>{const box=document.querySelector('.feat-inner[data-ep]'),h=document.getElementById('featured-h'),"
           "m=document.getElementById('feat-2d');if(!box||!h||!m)return;"
           "const d=document.getElementById('feat-3d'),w3=box.querySelector('.is-3d'),q=box.querySelector('.feat-q'),"
           "sub=box.querySelector('.feat-sub'),lab=box.querySelector('.feat-ep'),note=box.querySelector('.margin-note'),"
           "cl=box.querySelector('.feat-video-card-label'),tr=document.getElementById('feat-tr'),"
           "trt=document.getElementById('feat-tr-text'),home=JSON.parse(box.dataset.ep);"
           "const back=document.createElement('button');back.type='button';back.className='btn-link feat-back';"
           "back.textContent='\\u2190 Back to Episode '+home.num;back.hidden=true;sub.after(back);"
           "const src=(v,url,poster,vtt)=>{v.pause();v.textContent='';const s=document.createElement('source');"
           "s.src=url;s.type='video/mp4';v.appendChild(s);if(vtt){const t=document.createElement('track');"
           "t.kind='captions';t.src=vtt;t.srclang='en';t.label='English';v.appendChild(t)}"
           "if(poster)v.poster=poster;else v.removeAttribute('poster');v.load()};"
           "const load=x=>{h.textContent=x.h;lab.innerHTML=x.e;q.innerHTML=x.q;sub.textContent=x.s;"
           "if(note)note.innerHTML=x.n;if(cl)cl.textContent=x.c;src(m,x.mp4,x.poster,x.vtt);"
           "if(tr&&trt){trt.textContent=x.t||'';tr.open=false;tr.style.display=x.t?'':'none'}"
           "if(d&&w3){if(x.mp4_3d){src(d,x.mp4_3d,x.poster_3d);w3.style.display=''}else{d.pause();w3.style.display='none'}}"
           "back.hidden=x.num===home.num};"
           "back.addEventListener('click',()=>{load(home);h.scrollIntoView({behavior:'smooth'})});"
           "document.addEventListener('click',e=>{const a=e.target.closest('.cs-watch[data-ep]');if(!a)return;"
           "e.preventDefault();load(JSON.parse(a.dataset.ep));h.scrollIntoView({behavior:'smooth'});"
           "m.play().catch(()=>{})});})();")


def transcript(ep):
    """Plain text of the episode's captions (.vtt in site/static/), for readers and search engines."""
    vtt = (ep.get("video") or {}).get("vtt")
    path = HERE / "static" / vtt if vtt else None
    if not path or not path.is_file():
        return ""
    lines = []
    for block in path.read_text(encoding="utf-8").replace("\r", "").split("\n\n"):
        for line in block.split("\n"):
            line = line.strip()
            if not line or line.startswith(("WEBVTT", "NOTE", "STYLE")) or "-->" in line or line.isdigit():
                continue
            line = re.sub(r"<[^>]+>", "", line)
            if not lines or lines[-1] != line:
                lines.append(line)
    return " ".join(lines)


def video_jsonld(eps):
    """schema.org VideoObject for every released episode, so search engines know the page has these videos."""
    vids = []
    for ep in eps:
        v = ep.get("video") or {}
        if ep["status"] != "released" or not ep.get("released"):
            if ep["status"] == "released":
                print(f'warning: episode {ep["num"]} has no "released" date, left out of the video data')
            continue
        obj = {"@type": "VideoObject",
               "name": f'Learn with Avisha {ep["num"]}: {ep["name"]}',
               "description": ep["summary"],
               "thumbnailUrl": SITE_URL + v.get("poster", "og-image.png"),
               "uploadDate": ep["released"],
               "contentUrl": SITE_URL + v["mp4"],
               "inLanguage": "en",
               "isFamilyFriendly": True,
               "publisher": {"@type": "Organization", "name": "Avisha", "url": "https://avisha.ai/",
                             "logo": {"@type": "ImageObject", "url": SITE_URL + "apple-touch-icon.png"}}}
        text = transcript(ep)
        if text:
            obj["transcript"] = text
        vids.append(obj)
    data = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": "Learn with Avisha", "url": SITE_URL,
         "publisher": {"@type": "Organization", "name": "Avisha", "url": "https://avisha.ai/"}}] + vids}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{js}</script>'


def ep_payload(ep, featured):
    """What the featured player needs to show an episode (used by SWAP_JS)."""
    v = ep.get("video") or {}
    num = E(ep["num"])
    return {"num": ep["num"],
            "h": f'{"FEATURED MYSTERY" if featured else "NOW PLAYING"} · EPISODE {ep["num"]}',
            "e": ('<span class="live-dot"></span>' if featured else '')
                 + f'EPISODE {num} · {E(ep["subject"]).upper()}' + (" · NOW SHOWING" if featured else ""),
            "n": f'EP {num}<br>{E(ep["subject"]).replace(" ", "<br>")}',
            "q": ep["question"], "s": ep["summary"],
            "c": f'Episode {ep["num"]} · ' + (f'The {ep["series"]}' if ep.get("series") else ep["subject"]),
            "mp4": v.get("mp4"), "mp4_3d": v.get("mp4_3d"), "poster": v.get("poster"),
            "poster_3d": v.get("poster_3d"), "vtt": v.get("vtt"), "t": transcript(ep)}


def featured_html(ep):
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
        text = transcript(ep)
        hide = "" if text else ' style="display:none"'
        tr_html = (f'          <details class="feat-tr" id="feat-tr"{hide}>'
                   f'<summary>Read the transcript</summary><p id="feat-tr-text">{E(text)}</p></details>\n')
        action = (f'<div class="feat-video-card">\n'
                  f'          <div class="feat-video-card-label">{card_label}</div>\n'
                  f'{main_video}'
                  f'{tr_html}'
                  f'        </div>')
    else:
        action = f'<p class="feat-soon">Episode {E(ep["num"])} — dropping soon.</p>'
    figure = ""
    # the 3D view replaces the side sketch; episodes without 3D keep it
    has_3d = released and bool(ep["video"].get("mp4_3d"))
    if ep.get("figure") and not has_3d:
        svg = (HERE / ep["figure"]).read_text().strip()
        svg = svg.replace("<svg ", f'<svg role="img" aria-label="{E(ep.get("figure_caption",""))}" ', 1)
        figure = (f'      <div class="feat-sketch">\n        {svg}\n'
                  f'        <div class="sketch-cap" aria-hidden="true">{E(ep.get("figure_caption",""))}</div>\n      </div>')
    data_ep = f' data-ep="{E(json.dumps(ep_payload(ep, True), ensure_ascii=False))}"' if released else ""
    if released:
        action += f'\n        <script>{SWAP_JS}</script>'
    return f'''    <h2 class="feat-fig" id="featured-h">FEATURED MYSTERY · EPISODE {E(ep["num"])}</h2>
    <div class="feat-inner{"" if figure else " no-fig"}"{data_ep} style="position:relative">
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
        payload = E(json.dumps(ep_payload(ep, False), ensure_ascii=False))
        right = f'<a class="cs-watch" href="{E(ep["video"]["mp4"])}" data-ep="{payload}" aria-label="Watch episode {E(ep["num"])}: {E(ep["name"])}">WATCH ▶</a>'
    else:
        right = f'<span class="cs-label">{"DROPPING SOON" if ep["status"] == "dropping_soon" else "COMING SOON"}</span>'
    return (f'      <div class="cs-row{" done" if done else ""}">\n'
            f'        <span class="cs-num">{E(ep["num"])}</span>\n'
            f'        <span class="cs-name">{E(ep.get("index_name") or ep["name"])}</span>\n'
            f'        <span class="cs-teaser">{E(ep.get("index_teaser") or ep["teaser"])}</span>\n'
            f'        {right}\n      </div>')


def index_html(eps):
    """Index rows, with the module heading (e.g. "The Heat Exchanger Files") above each series."""
    out, series = [], None
    for ep in eps:
        s = ep.get("series")
        if s and s != series:
            out.append(f'      <h3 class="cs-module">The {E(s)}</h3>')
        series = s
        out.append(row_html(ep))
    return "\n".join(out)


# tutor starter questions: the featured episode's optional "tutor_questions" ([{label, q}, ...]),
# else these three. WATCH does not change them.
DEFAULT_TUTOR_QUESTIONS = [
    {"label": "Why is countercurrent flow usually better?",
     "q": "Why is countercurrent flow usually better in a heat exchanger?"},
    {"label": "What is fouling, and why does it matter?",
     "q": "What is fouling in a heat exchanger, and why does it matter?"},
    {"label": "When does the viscous fluid go on the shell side?",
     "q": "When should the viscous fluid go on the shell side of a shell-and-tube exchanger?"}]


def tutor_chips(ep):
    qs = ep.get("tutor_questions") or DEFAULT_TUTOR_QUESTIONS
    return "\n".join(f'        <button class="bot-chip" type="button" data-q="{E(x["q"])}">{E(x["label"])}</button>'
                     for x in qs)


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
    rows = index_html([e for e in eps if e is not feat])

    out = (HERE / "template.html").read_text()
    for k, v in {"BASE_CSS": (HERE / "_base.css").read_text(), "FEATURED": featured_html(feat),
                 "INDEX": rows, "TUTOR_CHIPS": tutor_chips(feat), "TOPIC_COUNT": str(len(eps)),
                 "SITE_URL": SITE_URL, "DESCRIPTION": E(DESCRIPTION), "JSONLD": video_jsonld(eps)}.items():
        out = out.replace("{{" + k + "}}", v)
    assert "{{" not in out, "unfilled placeholder"

    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / "index.html").write_text(out)
    # search engines: allow everything and point to the sitemap (one page; lastmod = newest release)
    dates = sorted(e["released"] for e in eps if e["status"] == "released" and e.get("released"))
    (PUBLIC / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n")
    (PUBLIC / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{SITE_URL}</loc>{f"<lastmod>{dates[-1]}</lastmod>" if dates else ""}</url>\n'
        '</urlset>\n')
    for d in ("static", "media"):          # static/ → site root, media/ → /media/
        if (HERE / d).is_dir():
            shutil.copytree(HERE / d, PUBLIC if d == "static" else PUBLIC / d, dirs_exist_ok=True)
    print(f"built {PUBLIC/'index.html'} · featured EP {feat['num']} ({feat['status']}) · {len(eps)-1} index rows")


if __name__ == "__main__":
    main()
