# Ask LearnWithAvisha — the always-on ChE assistant (build plan)
Status: **agreed in principle by Mrinal, 14 Oct 2026. Name not chosen yet** (suggestions: "Vidya", "the Avisha Professor").
Builds on CLAUDE_MASTER.md Part 3 (ask.learnwithavisha.ai). Nothing here is built yet.

## Why a separate assistant
- Isha runs on Mrinal's Mac and is busy with Mrinal's work; if the Mac sleeps she can't answer.
- This assistant lives online, awake 24/7, and does one job: answer chemical engineering questions.

## What it does
1. **ask.learnwithavisha.ai** — anyone asks a ChE question, gets a simple answer (first-year level) with the
   sources it came from. Answers only from open-licence material (NPTEL, LibreTexts, OpenStax, MIT OCW) via
   RAG; chemical engineering only; never invents numbers ("I don't know" beats a guess).
2. **YouTube comments** — twice a day it reads new comments on LearnWithAvisha videos and drafts replies
   (short answer + link to the full answer on the Ask site). **Nothing is posted until Mrinal approves**
   (one-tap batch). Auto-reply for simple questions only if Mrinal later says so.
3. **Question log** — the best questions go into LWA_IDEAS.md as future Plant Mysteries.

## Isha's role (light)
- Weekly spot-check of a sample of answers for accuracy + a short report: top questions, anything to fix.
- Not in the live loop.

## Build order
1. Launch the first 4–6 short videos (Plant Mysteries format).
2. Knowledge base: open sources only → Supabase pgvector.
3. ask.learnwithavisha.ai on Vercel (DNS on Hostinger as in CLAUDE_MASTER.md).
4. Comment-reply drafts (YouTube Data API, read comments + post only after approval).
5. Every video description: "❓ Ask anything: ask.learnwithavisha.ai".

## Rules
- Production deploys and any public posting need the founders' explicit approval.
- Keys only in the hosting provider's secret store / Keychain — never in git or files.
- Never mention "free" inside videos (CLAUDE_MASTER rule); references in the description box only.

## Decisions waiting for Mrinal
- Name of the assistant.
- Whether simple comment replies may ever go out automatically.
