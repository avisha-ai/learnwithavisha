# pipeline/patches

Small patches the render robot (.github/workflows/render-episode.yml) applies before rendering,
usually to make an episode pipeline run on Linux (fonts, model paths) or to carry a small
approved script fix. A patch that is already in the code is skipped. Once a patch
is merged into main, it can be deleted.

- ep02-ci.patch: Linux fonts (Liberation), KOKORO_DIR, and the EP02 steel line
  ("about 6.4 mm", 20 Nov 2026).

Branch previews build on Vercel from this branch (linked 20 Nov 2026).
