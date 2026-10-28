# Plant Mysteries: this week's episode plan (2026-10-27)

DRAFT for Mrinal. Nothing has been published or uploaded.

## What is already out there

- **lwa.avisha.ai** (read 27 Oct): "Learn with Avisha, Plant Mysteries Series". EP 01 *Heat Transfer* is live (parallel vs counter-current flow). EP 02 to EP 08 are "coming soon" and are listed by *subject* (Fluid Flow, Mass Transfer, Reaction Engineering, Thermodynamics, Separations, Process Safety, Instrumentation & Control). The site's Q&A (linked to EP 01) already covers countercurrent vs parallel, LMTD, PID response and pump cavitation.
- **Documents/Avisha/learnwithavisha** (HANDOFF 14 Oct, LWA_IDEAS.md, pm01_the_flip): Series 1 is "The Heat Exchanger Files": 1 The Flip (done, 72 s, 9:16), **2 Fouling**, 3 Baffles, 4 Fluid allocation, 5 Your kettle. Rules: hook in first 3 s, one idea, big captions, narrator Leandra, LWA watermark, never say "free" in a video, every number from a stated worked example, references in the description box, Tue + Thu cadence.
- EP 01's worked example (equal flows, NTU = 2, hot 90 °C, cold 10 °C, counter-current outlets about 37 and 63 °C) is reused below so the two episodes agree.

## Three candidate topics

| # | Topic | One-line hook (first 3 s) |
|---|---|---|
| A | **Fouling** (Heat Exchanger Files #2) | "Nothing broke. Nothing leaked. Yet the outlet is three degrees colder." |
| B | **Baffles** (Heat Exchanger Files #3) | "Engineers put plates in the way of the flow on purpose, and the pump works harder. Why?" |
| C | **Pump cavitation** (site Q&A already asks it) | "The pump is running, the pipe is full, flow is falling, and it sounds like gravel." |

**Pick: A, Fouling.** It is the next episode in the series Mrinal's team already agreed (EP 01's own "Next:" line points to it), it reuses EP 01's example so the series feels connected, it has the cleanest "puzzle then one idea" shape, and it needs no new equipment drawing. B and C stay in the queue (B is already the "Next:" line at the end of this episode).

## Episode plan: "The Layer You Can't See"

- **Series / number:** Plant Mysteries, Series 1 "The Heat Exchanger Files", episode 2 (page label **EP 02**; see decision 1 below).
- **Title:** The Layer You Can't See
- **Hook (0 to 3 s):** TI-102 flips from 63 °C to 60 °C on screen. Caption: "Nothing broke. The outlet is 3 °C colder."
- **The one key idea:** a thin deposit is one more resistance in series with the others. Resistances add, so 1/U rises, U falls, and the exchanger moves less heat even though flows and inlet temperatures have not changed.
- **Length:** about 74 s at a calm pace (170 words), vertical 9:16.

### Script (about 74 s)

Beat 1 · Hook, 0:00 to 0:04.5
> Nothing broke. Nothing leaked. Yet the outlet is three degrees colder.

Beat 2 · Same plant, 0:04.5 to 0:15.5
> Same exchanger. Same flows. Hot in at ninety, cold in at ten degrees Celsius.
> Clean, the cold stream left at sixty-three. Now it leaves at sixty.

Beat 3 · The layer, 0:15.5 to 0:49
> What changed is a layer inside the tubes, eight hundredths of a millimetre thick. Thinner than a sheet of paper.
> It doesn't block the flow. It sits in the path of the heat, and resistances in series simply add.
> Clean, the resistance to heat flow is two thousandths of a square-metre-kelvin per watt. The deposit adds four ten-thousandths. So U falls from five hundred to about four hundred seventeen watts per square-metre-kelvin.
> That sliver resists heat like six millimetres of stainless steel.

Beat 4 · Payoff and pull, 0:49 to 1:14
> Lower U means fewer transfer units: two becomes about one point seven. Effectiveness slips from point six seven to point six three, and the exchanger moves about six percent less heat.
> Six percent is easy to miss. Flow is normal. The only clue is a drifting thermometer.
> Fouling is a resistance in series. Watch the temperatures, not just the flow.
> Next: why are there plates inside the shell?

Notes: timings are estimates at about 2.3 words per second; retime to Leandra's recording. "Free" is not used. "Next:" points to Baffles, which is real episode 3 of the series. The 63 → 60 and every other number is labelled on screen as an illustrative worked example.

### Short caption (YouTube Short / Instagram / LinkedIn)

> Same exchanger. Same flows. The outlet is 3 °C colder. A deposit 0.08 mm thick adds one more resistance in series, and heat duty drops about 6%. Plant Mysteries 02: The Layer You Can't See. Illustrative worked example. #ChemicalEngineering #HeatTransfer #PlantMysteries

Description-box references (to be confirmed by Mrinal before upload): any standard heat transfer text covering fouling factors and the ε-NTU method (e.g. NPTEL heat transfer course, LibreTexts Heat Transfer, MIT OCW). Per the series rule, exact URLs must be opened and checked at upload time; I did not open them this week, so none are listed.

### Episode-page text (lwa.avisha.ai)

- **Tag:** EP 02
- **Title:** The Layer You Can't See
- **Question:** Why does an exchanger move less heat when nothing has broken and nothing has changed?
- **Description (two lines):** A deposit thinner than a sheet of paper adds one more resistance in series and cuts the heat moved by about 6%.
  One worked example, one idea: watch the temperatures, not just the flow.
- **Figure caption:** FIG. 1 · A thin layer is a resistance in series (illustrative worked example).

## The worked example and every number checked

Assumptions, all stated on the diagram: counter-current, equal heat-capacity rates (C_r = 1), hot in 90 °C, cold in 10 °C, clean NTU = 2 (same as EP 01), clean U = 500 W/m²·K, deposit 0.08 mm thick with k = 0.2 W/m·K (typical of a poorly conducting organic or scale film; illustrative), tube ID 20 mm, tubes carry the hot fluid, flows held constant.

| Quantity | Working | Result | Used in script / diagram |
|---|---|---|---|
| Clean resistance | 1/U = 1/500 | 0.0020 m²·K/W | yes |
| Fouling resistance | R_f = δ/k = 0.00008 m / 0.2 | 0.0004 m²·K/W | yes ("four ten-thousandths") |
| Fouled resistance | 0.0020 + 0.0004 | 0.0024 m²·K/W | yes |
| Fouled U | 1/0.0024 | 416.7, so "about 417" W/m²·K (down 16.7%) | yes |
| NTU | 2 × 416.7/500 | 1.667, "about 1.7" | yes (1.67) |
| Effectiveness, counter-current, C_r = 1 | ε = NTU/(1 + NTU): 2/3 and 1.667/2.667 | 0.667 and 0.625 | yes (0.67, 0.63) |
| Cold outlet | 10 + ε × 80 | 63.3 and 60.0 °C | yes (63, 60) |
| Hot outlet | 90 − ε × 80 | 36.7 and 40.0 °C | yes (37, 40) |
| Heat duty change | 0.625/0.667 − 1 | −6.25%, "about 6%" (94% of clean) | yes |
| Stainless-steel equivalent | R_f × k_steel = 0.0004 × 16 | 6.4 mm (k ≈ 16 W/m·K, 304 stainless) | yes ("six millimetres") |
| "Thinner than paper" | 0.08 mm vs office paper about 0.1 mm | true, though close | yes |
| Tube pressure drop (not in script) | ΔP ∝ D⁻⁵ at fixed flow, (20/19.84)⁵ | about +4% (lower bound: fouled surfaces are also rougher) | no, kept out so the video makes no pressure claim it cannot back |

All of the arithmetic above was recomputed in Python on 27 Oct and matches. Consistency with EP 01 (outlets about 37 and 63 °C, NTU = 2, 90/10 °C inlets) is exact.

Things to confirm (not yet checked against a cited textbook this week): the ε-NTU counter-current formula and the series-resistance form of U are standard and I am confident of them, but Mrinal's rule is "open sources, textbook-faithful", so someone should confirm the page references for the description box. The deposit conductivity (0.2 W/m·K) is an assumption, not a measured value, and the video must keep saying "illustrative".

## Drawings (this folder)

- `2026-10-27-diagram.png` / `.svg`: the main diagram (one idea, labelled, arrows, key values, TI tag bubbles, datasheet table, LWA watermark).
- `2026-10-27-storyboard.png` / `.svg`: four beats, 9:16 frames with timings.

Label check (diagram and storyboard against the script): 90 °C, 10 °C, 63 → 60 °C, 37 → 40 °C, 0.08 mm, 0.0020 + 0.0004 = 0.0024, U 500 → 417, NTU 2.00 → 1.67, ε 0.67 → 0.63, 94% duty ("about 6% less"), 6.4 mm stainless, "Next: why plates inside the shell" all match the script and the table above. Beat timings on the storyboard match the script headings.

## Decisions for Mrinal

1. **Episode numbering.** The website lists EP 02 as *Fluid Flow* (subject-based), but the 14 Oct plan makes the next episode *Fouling*. I used "EP 02" for Fouling. If the site's subject order wins, relabel this one and update the page list.
2. **Topic pick** (Fouling) and the **deposit assumption** (0.08 mm, k = 0.2).
3. **Voice.** Leandra recording is still needed (ElevenLabs website); retime captions to it.
4. Posting, uploading and the site page are all left to Mrinal.
