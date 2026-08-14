# Interview Mode

Write Interview blobs for an existing breakdown. You receive a numbered breakdown and must produce only the Interview-style blobs, preserving original numbers.

## Voice & POV

First person throughout — the named NPC speaks. **The main character (the protagonist necromancer) is always the interviewer**; the bolded prompts are their abbreviated questions, never spoken aloud by any other party. The main character ("you") **never** answers and is never the interviewee. The reader eavesdrops rather than being addressed directly.

If the breakdown header names the protagonist as the interviewee, that header is wrong — flag it and skip the blob, or convert it into Essay before writing.

Register is **candid and colloquial** — transcribed speech, not composed prose. This is the key split from Essay: Essay is the scholarly necromancer-author reasoning in public; Interview is any NPC talking in their own voice, tics and all. The register shifts per character (learned, blunt, broken, etc.).

Tense is anchored in the present (the moment of answering), with past-tense excursions for anecdote and occasional future for speculation.

## Hard Rules

### Structure
1. Each blob has **2–4 Q/A exchanges**, matching the `(N)` in the breakdown header exactly.
2. Each exchange is: **bolded prompt** on its own line, then response paragraph below.
3. Prompt is **1–6 words**, typically a fragment: `**Sources?**`, `**And after?**`, `**The fourth dive**`. Statement fragments and single nouns are legal.
4. Response is **1–80 words**, 1–4 sentences.
5. **Total blob word count: 20–200 words.**

### Length Variety
6. If 3+ exchanges, at least two responses must differ by **15+ words**. Mix a long candid turn with clipped ones. Do not write three near-identical-length answers.

### Content
7. **First person mandatory.** Never drift to third-person omniscient.
8. **At least one verbal tic, hesitation, or digression per blob.** "Well," "I mean," "in sooth," trailing off, self-interruption, an aside that wanders before returning. The blob must read as *spoken*.
9. **The NPC must have an agenda.** Confession, complaint, boast, warning, evasion, pitch.
10. **The main character is always the interviewer, never the interviewee.** The bolded prompts represent the protagonist's abbreviated questions; the answering voice belongs to a named NPC. If a beat requires the protagonist to speak at length (confess, persuade, lie, monologue), use Essay, not Interview.
11. **The main character never speaks aloud on the page.** No quoted speech from "you" — the bolded prompts are the only intrusion.
12. **No stage directions or narration.** No "he said," no action beats, no description of the speaker between lines.
13. **No meta-dialogue.** No "as I was saying," "let me explain," "listen carefully." The NPC just speaks.
14. **"I" dominates over "you."** The respondent is revealing themselves or the world, not addressing the interviewer as the subject.

## What Interview Blobs Cover

Interview is the most character-driven blob. Use it for:

- **Confessions & revelations**: Something an NPC has been holding back.
- **Backstory & motive**: Personal history conveyed through voice, not exposition.
- **Lore through personality**: World detail filtered through a specific speaker's biases.
- **Aftermath reactions**: An NPC's response to events the reader has just witnessed.
- **Breather beats**: Placed after Verse or heavy Essay to slow the pulse.

Interview is **not** for:
- The narrator-necromancer's reasoning (that is Essay)
- Environmental or canonical description (Lemma)
- In-the-moment action (Verse)
- Inscribed stone-voice (Memorials)

## Tone

The NPC should sound like a *person* — with *excrutiatingly-specific* verbal habits, priorities, and a way of speaking.

Avoid:
- All responses at the same length or emotional register
- Prompts as full polite questions ("Could you tell me about...") — keep them fragmentary
- Generic interviewee-speak ("That's a great question. Well, it all began...")

## Workflow

1. **Read the full breakdown** to understand the scene arc and where Interview blobs sit.
2. **Identify the named NPC and circumstance** from the breakdown header.
3. **Determine the NPC's agenda and voice.** What do they want from this exchange? How do they speak?
4. **For each blob**, use the breakdown bullets as a content guide. The bullets say *what* is conveyed; you decide *how* — vocabulary, cadence, tics, digressions.
5. **Verify every hard rule**: exchange count matches header, word counts per response and total, length variety, first person, verbal tic present, no stage directions, prompt formatting.
6. **Output only the Interview blobs** under their original numbered headers.

## Output Format

```markdown
# [Scene Title] — Interview Blobs

## 4. INTERVIEW (3) — [Character Name], [optional circumstance]

**Prompt fragment**
Response paragraph in candid first-person voice, 15–80 words.

**Next prompt**
Next response.

**Third prompt**
Third response.
```

Name the output file `[Scene-Title]-Interview-Blobs.md`.

**CRITICAL:** Output ONLY Interview blobs. Do not write other blob types. Do not renumber.