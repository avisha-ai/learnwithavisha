// api/ask.js — LWA AI Q&A: Gemini Flash answer + optional Kokoro TTS
// Env vars (set in Vercel → Project → Settings → Environment Variables; never commit them):
//   GEMINI_API_KEY      required
//   GEMINI_MODEL        optional, default below (2.0/2.5 Flash are closed to new keys;
//                       3.8 Flash and flash-latest timed out in testing on 2026-11-07)
//   GEMINI_FALLBACK_MODELS optional, comma-separated; tried in order when the primary
//                       model is overloaded (503/429/5xx) or too slow. On 2026-11-17
//                       3.5 Flash returned 503 "high demand" for every request while
//                       3.5 Flash-Lite and 3.1 Flash-Lite answered in ~1-2 s.
//   KOKORO_SERVER_URL   optional; OpenAI-compatible Kokoro server, e.g. https://voice.avisha.ai
//                       If unset or unreachable, the text answer is returned without audio.

export const config = { maxDuration: 30 };

const MODEL = process.env.GEMINI_MODEL || 'gemini-3.5-flash';
const FALLBACKS = (process.env.GEMINI_FALLBACK_MODELS || 'gemini-3.5-flash-lite,gemini-3.1-flash-lite')
  .split(',').map(m => m.trim()).filter(m => m && m !== MODEL);
const GEMINI_BUDGET_MS = 22000;          // all Gemini attempts together; leaves room for TTS under maxDuration
const ATTEMPT_MS = [6000, 7000, 6000];   // per-model timeout: primary gets the most time

// Ask one model. Returns { text } on success, { retry: true } when another model should be tried.
async function askModel(model, q, timeoutMs) {
  let r;
  try {
    r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{ role: 'user', parts: [{ text: q }] }],
        // minimal thinking: ~2-3 s answers, and reasoning tokens don't eat the output budget
        generationConfig: { maxOutputTokens: 400, temperature: 0.3, thinkingConfig: { thinkingLevel: 'minimal' } }
      }),
      signal: AbortSignal.timeout(timeoutMs)
    });
  } catch (err) {
    console.error(`Gemini ${model} unreachable/timeout:`, err.name, err.message);
    return { retry: true };
  }
  if (!r.ok) {
    console.error(`Gemini ${model} error:`, r.status, (await r.text()).slice(0, 300));
    // overload, rate limit, server error or a model that has been retired: try the next model
    return { retry: r.status === 429 || r.status >= 500 || r.status === 404 };
  }
  const data = await r.json();
  const text = (data?.candidates?.[0]?.content?.parts || []).map(p => p.text || '').join('').trim();
  return text ? { text } : { retry: true };
}

const SYSTEM_PROMPT = `You are Avisha — a chemical engineering tutor who explains process plant phenomena with clarity and precision. Your voice is warm, direct, and deeply knowledgeable. You love revealing the physical intuition behind equations.

Rules:
- Keep answers under 120 words.
- Always explain the physical mechanism first, then the equation or rule.
- Use plain language; define jargon when you use it.
- Never say "Great question!" or use hollow filler phrases.
- If the question is outside chemical engineering, say so briefly and redirect.
- Plain text only: no Markdown, no LaTeX, no asterisks. Write equations inline with Unicode, e.g. LMTD = (ΔT₁ − ΔT₂) / ln(ΔT₁/ΔT₂).
- Accuracy first: only give equations and numbers you are sure are standard textbook results, with correct units. If you are not sure, explain the idea in words instead. Never invent data. Say "typical" or "illustrative" when a number is an example.

Standard relations to keep exactly right (thin plane wall; for tubes, refer every term to the same area):
- Resistances in series: 1/U = 1/hₒ + R_f,o + x_w/k_w + R_f,i + 1/hᵢ. Fouling factors R_f are resistances in m²·K/W added directly; they are never divided by a conductivity.
- Duty: Q = U·A·ΔT_lm, with ΔT_lm = (ΔT₁ − ΔT₂) / ln(ΔT₁/ΔT₂) from the end temperature differences.
- Learn with Avisha Episode 02 example: clean total resistance 0.0020 m²·K/W (U = 500 W/m²·K); a 0.08 mm deposit adds about 0.0004 m²·K/W, so U falls to about 417 W/m²·K (about 17% lower) and the exchanger moves about 6% less heat.`;

async function speak(text) {
  const base = process.env.KOKORO_SERVER_URL;
  if (!base) return null;
  try {
    const r = await fetch(`${base.replace(/\/$/, '')}/v1/audio/speech`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'kokoro', input: text, voice: 'af_heart', response_format: 'mp3' }),
      signal: AbortSignal.timeout(12000)
    });
    if (!r.ok) { console.error('TTS error:', r.status, (await r.text()).slice(0, 300)); return null; }
    return Buffer.from(await r.arrayBuffer()).toString('base64');
  } catch (err) {
    // TTS failure is non-fatal — the text answer is still returned
    console.error('TTS unreachable:', err.message);
    return null;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const question = req.body && typeof req.body.question === 'string' ? req.body.question : '';
  if (question.trim().length < 3) {
    return res.status(400).json({ error: 'Question too short' });
  }
  const q = question.trim().slice(0, 200); // cap question length

  if (!process.env.GEMINI_API_KEY) {
    console.error('GEMINI_API_KEY is not set');
    return res.status(503).json({ error: 'Avisha is not configured yet — try again later.' });
  }

  try {
    const started = Date.now();
    let answerText = '';
    const models = [MODEL, ...FALLBACKS];
    for (let i = 0; i < models.length && !answerText; i++) {
      const left = GEMINI_BUDGET_MS - (Date.now() - started);
      if (left < 2500) break;
      const out = await askModel(models[i], q, Math.min(ATTEMPT_MS[i] ?? 6000, left));
      if (out.text) {
        answerText = out.text;
        if (i > 0) console.warn(`answered by fallback ${models[i]}`);
      } else if (!out.retry) break;
    }
    if (!answerText) {
      return res.status(502).json({ error: 'AI unavailable — try again shortly.' });
    }

    const audioB64 = await speak(answerText);
    return res.status(200).json({ text: answerText, audio: audioB64 });
  } catch (err) {
    console.error('ask handler error:', err);
    return res.status(500).json({ error: 'Server error — please try again.' });
  }
}
