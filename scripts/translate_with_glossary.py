"""
translate_with_glossary.py
--------------------------
LinguaAI — AI-Powered Translation Studio
INSPIRON 5.0 Hackathon | Problem Statement 02 | Team: Coder's Clique

Demonstrates:
  - Glossary enforcement (constrain LLM via prompt engineering)
  - Translation Memory lookup (exact match)
  - Style/tone profile injection into system prompt
  - Support for Claude, Gemini, GPT-4o, or Ollama

Usage:
  pip install -r requirements.txt
  python scripts/translate_with_glossary.py

Set ONE of these in your .env file:
  ANTHROPIC_API_KEY=your_key   (Claude — recommended)
  GEMINI_API_KEY=your_key      (Gemini — free tier)
  OPENAI_API_KEY=your_key      (GPT-4o)
  # Or use Ollama locally — no key needed
"""

import json, os, re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 1. GLOSSARY ────────────────────────────────────────────────────────────────

GLOSSARY_PATH = Path(__file__).parent.parent / "glossaries" / "en_es_glossary.json"

def load_glossary(path: Path) -> dict:
    if not path.exists():
        print(f"[WARNING] Glossary not found at {path}. Using empty glossary.")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}

# ── 2. TRANSLATION MEMORY ─────────────────────────────────────────────────────
# In Round 2 this will be ChromaDB with vector similarity search.
# For the demo, we use a simple in-memory dictionary (exact match only).

TRANSLATION_MEMORY = {
    "Please review the attached document.": "Por favor revise el documento adjunto.",
    "Hello, how are you?": "Hola, ¿cómo estás?",
    "Thank you for your time.": "Gracias por su tiempo.",
}

def tm_lookup(source: str):
    """Exact TM match — returns translation or None."""
    return TRANSLATION_MEMORY.get(source.strip())

# ── 3. GLOSSARY ENFORCEMENT ───────────────────────────────────────────────────

def build_glossary_prompt(text: str, glossary: dict) -> tuple:
    """
    Scan source text for glossary terms.
    Returns (prompt_instruction, list_of_matched_terms).
    """
    matches = []
    instructions = []
    for src_term, tgt_term in glossary.items():
        if re.search(re.escape(src_term), text, re.IGNORECASE):
            matches.append(src_term)
            instructions.append(f'  * "{src_term}" MUST be translated as "{tgt_term}"')

    if not instructions:
        return "", []

    prompt = "MANDATORY GLOSSARY TERMS (do not deviate from these):\n" + "\n".join(instructions)
    return prompt, matches

# ── 4. STYLE PROFILES ─────────────────────────────────────────────────────────
# Tone options from Problem Statement:
# Formal, Official, Conversational, Technical, Social, Friendly, Diplomatic

STYLE_PROFILES = {
    "formal":        "Use formal, professional register. Avoid contractions and colloquialisms. Use 'usted' (not 'tú') in Spanish.",
    "official":      "Use official, regulatory language. Precise and unambiguous. Suitable for legal and compliance documents.",
    "conversational":"Use a friendly, natural tone. Contractions are acceptable. Write as if speaking to a colleague.",
    "technical":     "Use precise technical vocabulary. Preserve all domain-specific terms exactly as they appear in the glossary.",
    "social":        "Use engaging, casual language suitable for social media and marketing content.",
    "friendly":      "Use a warm, approachable tone. Empathetic and easy to read.",
    "diplomatic":    "Use tactful, measured language. Balanced and considerate of multiple perspectives.",
}

# ── 5. LLM CALL ───────────────────────────────────────────────────────────────

def call_llm(prompt: str) -> str:
    """
    Try LLM providers in order of preference.
    Falls back gracefully if a key is not set.
    """

    # Option A: Claude (Anthropic) — recommended
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except ImportError:
            print("[INFO] anthropic package not installed. Run: pip install anthropic")

    # Option B: Gemini (Google)
    if os.getenv("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except ImportError:
            print("[INFO] google-generativeai not installed. Run: pip install google-generativeai")

    # Option C: OpenAI GPT-4o
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            print("[INFO] openai package not installed. Run: pip install openai")

    # Option D: Ollama (local, free, no API key needed)
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["response"].strip()
    except Exception:
        pass

    raise EnvironmentError(
        "\nNo LLM configured. Please set one of these in your .env file:\n"
        "  ANTHROPIC_API_KEY  (Claude — recommended)\n"
        "  GEMINI_API_KEY     (Gemini — free tier at aistudio.google.com)\n"
        "  OPENAI_API_KEY     (GPT-4o)\n"
        "Or install Ollama locally at https://ollama.ai (no key needed)"
    )

# ── 6. CORE TRANSLATE FUNCTION ────────────────────────────────────────────────

def translate(
    text: str,
    target_language: str = "Spanish",
    style: str = "formal",
    glossary: dict = None,
) -> dict:
    """
    Translate text with TM lookup, glossary enforcement, and style profile.
    This is the core function — in Round 2 it will be backed by ChromaDB RAG.
    """
    glossary = glossary or {}

    # Step 1: Check Translation Memory (exact match)
    # In Round 2: vector similarity search against ChromaDB
    tm_result = tm_lookup(text)
    if tm_result:
        print("  [TM HIT] Exact match found in Translation Memory.")
        return {
            "source": text,
            "target_language": target_language,
            "style": style,
            "tm_hit": True,
            "translation": tm_result,
            "glossary_terms_applied": [],
        }

    # Step 2: Build glossary enforcement instruction
    glossary_instruction, matched_terms = build_glossary_prompt(text, glossary)

    # Step 3: Build style instruction
    style_instruction = STYLE_PROFILES.get(style.lower(), STYLE_PROFILES["formal"])

    # Step 4: Build full prompt with glossary + style enforcement
    prompt = f"""You are a professional translator for an enterprise translation platform.

TASK: Translate the SOURCE TEXT from English to {target_language}.

STYLE PROFILE — {style.upper()}:
{style_instruction}

{glossary_instruction}

SOURCE TEXT:
\"\"\"{text}\"\"\"

OUTPUT RULES:
- Return ONLY the translated text, nothing else.
- Do not add explanations, notes, or quotation marks.
- Respect ALL glossary term mappings exactly — these are mandatory.
- Apply the style profile consistently throughout.
"""

    # Step 5: Call LLM
    translation = call_llm(prompt)

    return {
        "source": text,
        "target_language": target_language,
        "style": style,
        "tm_hit": False,
        "translation": translation,
        "glossary_terms_applied": matched_terms,
    }

# ── 7. DEMO ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    glossary = load_glossary(GLOSSARY_PATH)

    test_cases = [
        {
            "text": "The member enrollment process requires prior authorization from the health plan.",
            "target_language": "Spanish",
            "style": "formal",
        },
        {
            "text": "Please review the attached document.",  # TM hit
            "target_language": "Spanish",
            "style": "formal",
        },
        {
            "text": "Submit your claim form by the end of the benefit period.",
            "target_language": "French",
            "style": "official",
        },
        {
            "text": "Your deductible and copayment amounts are listed in your explanation of benefits.",
            "target_language": "Spanish",
            "style": "conversational",
        },
    ]

    print("=" * 65)
    print("  LINGUAAI — AI-POWERED TRANSLATION STUDIO  |  INSPIRON 5.0")
    print("  Team: Coder's Clique | Problem Statement 02")
    print("=" * 65)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n[Test {i}]")
        result = translate(
            text=tc["text"],
            target_language=tc["target_language"],
            style=tc["style"],
            glossary=glossary,
        )
        print(f"  Source     : {result['source']}")
        print(f"  Language   : {result['target_language']}  |  Style: {result['style']}")
        print(f"  TM Hit     : {result['tm_hit']}")
        if result["glossary_terms_applied"]:
            print(f"  Glossary   : {result['glossary_terms_applied']}")
        print(f"  Translation: {result['translation']}")
        print("-" * 65)
