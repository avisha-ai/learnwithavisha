// api/ask.js — LWA AI Q&A: Gemini Flash answer + optional Kokoro TTS
// Env vars (set in Vercel → Project → Settings → Environment Variables; never commit them):
//   GEMINI_API_KEY      required
//   GEMINI_MODEL        optional, default below (2.0/2.5 Flash are closed to new keys;
//                       3.8 Flash and flash-latest timed out in testing on 2026-11-07)
//   KOKORO_SERVER_URL   optional; OpenAI-compatible Kokoro server, e.g. https://voice.avisha.ai
//                       If unset or unreachable, the text answer is returned without audio.

export const config = { maxDuration: 30 };

const MODEL = process.env.GEMINI_MODEL || 'gemini-3.5-flash';

const SYSTEM_PROMPT = `You are Avisha — a chemical engineering tutor who explains process plant phenomena with clarity and precision. Your voice is Mrinal Gala's: warm, direct, and deeply knowledgeable. You love revealing the physical intuition behind equations.

Rules:
- Keep answers under 120 words.
- Always explain the physical mechanism first, then the equation or rule.
- Use plain language; define jargon when you use it.
- Never say "Great question!" or use hollow filler phrases.
- If the question is outside chemical engineering, say so briefly and redirect.
- Plain text only: no Markdown, no LaTeX, no asterisks. Write equations inline with Unicode, e.g. LMTD = (ΔT₁ − ΔT₂) / ln(ΔT₁/ΔT₂).`;

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
    const geminiRes = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
          contents: [{ role: 'user', parts: [{ text: q }] }],
          // minimal thinking: ~2–3 s answers, and reasoning tokens don't eat the output budget
          generationConfig: { maxOutputTokens: 400, temperature: 0.7, thinkingConfig: { thinkingLevel: 'minimal' } }
        }),
        signal: AbortSignal.timeout(15000)
      }
    );

    if (!geminiRes.ok) {
      console.error('Gemini error:', geminiRes.status, (await geminiRes.text()).slice(0, 500));
      return res.status(502).json({ error: 'AI unavailable — try again shortly.' });
    }

    const geminiData = await geminiRes.json();
    const answerText = (geminiData?.candidates?.[0]?.content?.parts || [])
      .map(p => p.text || '').join('').trim();
    if (!answerText) {
      return res.status(502).json({ error: 'No answer returned.' });
    }

    const audioB64 = await speak(answerText);
    return res.status(200).json({ text: answerText, audio: audioB64 });
  } catch (err) {
    console.error('ask handler error:', err);
    return res.status(500).json({ error: 'Server error — please try again.' });
  }
}
