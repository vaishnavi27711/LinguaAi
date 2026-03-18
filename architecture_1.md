# Extended Architecture Notes — LinguaAI Translation Studio
**Team: Coder's Clique · INSPIRON 5.0 · Problem Statement 02**

---

## RAG Pipeline — Detailed Implementation Plan (Round 2)

The Translation Memory is powered by a full RAG (Retrieval-Augmented Generation) pipeline as described in the problem statement:

```
Source Document
      ↓
1. SEGMENT — Split into sentences/phrases using nltk or spaCy
      ↓
2. EMBED — Generate vector embeddings using sentence-transformers
           (all-MiniLM-L6-v2 — free, runs locally, no API needed)
      ↓
3. VECTOR SEARCH — Cosine similarity search against ChromaDB TM store
      ↓
4. CLASSIFY MATCHES:
   - Score >= 0.99  →  Exact Match (100%)   →  auto-fill from TM
   - Score 0.75-0.98 → Fuzzy Match (75-99%) →  show suggestion to linguist
   - Score < 0.75   →  New Segment          →  send to LLM
      ↓
5. LLM TRANSLATION (new segments only)
   - System prompt includes: glossary terms + style/tone rules
   - Glossary enforcement via prompt engineering
   - No fine-tuning needed for Round 1
```

---

## Glossary Enforcement Strategy

We constrain the LLM via **prompt engineering** — not fine-tuning.
Demonstrated in `scripts/translate_with_glossary.py`.

Example prompt injection:
```
MANDATORY GLOSSARY TERMS — do not deviate:
  * "health plan"  MUST be translated as "plan de salud"
  * "deductible"   MUST be translated as "deducible"
  * "copayment"    MUST be translated as "copago"

STYLE PROFILE — Formal:
  Use formal register. No contractions. Use "usted" not "tu".
```

---

## Style & Tone Profiles

All 7 tone options from the problem statement are supported:

| Tone | Description |
|---|---|
| **Formal** | Professional register, no contractions |
| **Official** | Regulatory and legal language |
| **Conversational** | Friendly, natural tone |
| **Technical** | Domain-specific precision |
| **Social** | Engaging, casual writing |
| **Friendly** | Warm, approachable language |
| **Diplomatic** | Tactful, measured language |

---

## Continuous Learning Loop

```
Linguist approves segment
        |
        v
1. Add (source, target) pair to ChromaDB
   with metadata: language pair, project, date
        |
        v
2. If new term detected
   suggest adding to glossary (human confirms)
        |
        v
3. Weekly: batch approved corrections
   optional incremental LLM fine-tuning
        |
        v
4. TM versioning snapshot created
   rollback available at any point
```

---

## Document Structure Preservation

**DOCX:** Use `python-docx` to iterate paragraphs and table cells individually.
Translate each text run and write back. Bold, italic, and fonts are preserved.

**PDF:** Use `pdfplumber` to extract text blocks with bounding boxes.
Translate and reconstruct using `reportlab` or `fpdf2`. Layout preserved.

---

## Source Quality Validation — Check Types

| Check | What It Validates |
|---|---|
| Spell Check | Context-aware with domain-specific terminology support |
| Consistency Analysis | Same term written differently within one document |
| Punctuation Validation | Missing spaces, double spaces, inconsistent comma usage |
| Formatting Checks | Date formats, number formats, capitalisation patterns |

---

## Post-Translation QA Checks

| Check | What It Validates |
|---|---|
| Tag consistency | All XML/HTML tags present in source exist in translation |
| Number accuracy | All figures, dates, amounts match source exactly |
| Length validation | Translation length is within 30% of source length |
| Cross-document consistency | Same source terms translated identically across all files |
| Glossary compliance | All enforced glossary terms appear in translation |

---

## Back-Translation Verification

1. Take the translated segment
2. Send it back to the LLM — translate back to original language
3. Display three-way comparison: Source vs Translation vs Back-Translated
4. Flag segments where back-translation diverges significantly
5. Flagged segments are candidates for manual review

---

## LLM Options Supported

| LLM | Cost | Notes |
|---|---|---|
| Claude (Anthropic) | Paid — very reasonable | Best quality, recommended |
| Gemini 1.5 Flash (Google) | Free tier available | Fast, good quality |
| GPT-4o (OpenAI) | Paid | Strong alternative |
| Ollama / Mistral | Completely free, runs locally | No API key needed, works offline |

---

## Analytics Dashboard Metrics

As specified in the problem statement bonus features:

- **TM Leverage Rate** — percentage of segments matched from memory (target: >70%)
- **Linguist Productivity** — segments reviewed per hour, approval rate
- **Quality Trends** — approval rate and error rate over time
- **Cost Savings Estimator** — manual translation cost vs AI-assisted cost

---

## Full Tech Stack (Round 2)

| Component | Technology |
|---|---|
| Document Parsing | python-docx, pdfplumber |
| Embeddings / RAG | sentence-transformers + ChromaDB |
| LLM | Claude, Gemini 1.5 Flash, GPT-4o, or Ollama |
| Glossary & Style | Prompt engineering — injected into LLM system prompt |
| Backend API | FastAPI (Python) |
| Frontend | React + TypeScript + TailwindCSS |
| Glossary Format | TBX, TMX, XLIFF for CAT tool interoperability |
| Deployment | Docker Compose, Vercel, Railway/Render |
