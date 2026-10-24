import re
import string
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import translators as ts
    HAS_TRANSLATORS = True
except ImportError:
    HAS_TRANSLATORS = False

from deep_translator import GoogleTranslator, MyMemoryTranslator

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_FILE = DATA_DIR / "dictionary_cache.json"

# Core Hollow Knight and gaming lore vocabulary
CORE_VOCAB: Dict[str, str] = {
    # Hollow Knight specific lore
    "higher": "superior / más elevado",
    "beings": "seres",
    "vessel": "vasija / receptáculo",
    "void": "vacío / abismo",
    "hallownest": "Hallownest (el reino subterráneo)",
    "ancient": "ancestral / antiguo",
    "basin": "cuenca / hondonada",
    "slumber": "sueño profundo / reposo",
    "pale": "pálido / rey pálido",
    "nail": "aguijón (la espada)",
    "soul": "alma / energía espiritual",
    "charm": "amuleto",
    "stag": "ciervo / escarabajo de viaje",
    "geo": "geo (moneda de Hallownest)",
    "quill": "pluma para dibujar mapas",
    "knight": "caballero",
    "shade": "sombra",
    "husk": "cáscara / cuerpo vacío",
    "grub": "larva / oruga",
    "shell": "caparazón",
    "bench": "banco de descanso",
    "mask": "máscara / vida",
    "shard": "fragmento",
    "notch": "ranura de amuleto",
    "wyrm": "dragón antiguo / gusano gigante",
    "radiance": "el destello / resplandor",
    "hollow": "hueco / vacío",
    "pure": "puro",
    "dreamer": "soñador",
    "relic": "reliquia",
    "wanderer": "vagabundo / caminante",
    "elderbug": "bicho anciano (NPC)",
    "sly": "astuto / Sly (comerciante)",
    "cornifer": "Cornifer (el cartógrafo)",
    "isent": "Iselda (esposa de Cornifer)",
    "hornet": "Hornet (protectora de Hallownest)",
    # Essential gaming & action terms
    "press": "presionar",
    "interact": "interactuar",
    "strike": "golpear",
    "dash": "desplazamiento rápido",
    "jump": "saltar",
    "focus": "concentrar (curar alma)",
    "spell": "hechizo",
    "cast": "lanzar / conjurar",
    "heal": "curar",
    "damage": "daño",
    "acquire": "adquirir / conseguir",
    "reveal": "revelar",
    "path": "camino",
    "danger": "peligro",
    "gate": "puerta / portón",
    "key": "llave",
    "lock": "cerradura",
}

class LearningTranslator:
    def __init__(self, source: str = "en", target: str = "es"):
        self.source = source
        self.target = target
        self.cache: Dict[str, str] = dict(CORE_VOCAB)
        self.sentence_cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.cache.update(saved)
            except Exception as e:
                print(f"[Translator] Error loading cache: {e}")

    def _save_cache(self) -> None:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Translator] Error saving cache: {e}")

    def clean_word(self, raw_token: str) -> str:
        cleaned = raw_token.strip(string.punctuation + "“”‘’—–…")
        return cleaned.lower()

    def translate_full_sentence(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        if text in self.sentence_cache:
            return self.sentence_cache[text]

        # 1. Try 'translators' library
        if HAS_TRANSLATORS:
            try:
                trans = ts.translate_text(text, from_language=self.source, to_language=self.target)
                if trans and trans.strip():
                    self.sentence_cache[text] = trans.strip()
                    return self.sentence_cache[text]
            except Exception as e:
                print(f"[Translator] translators.translate_text failed: {e}")

        # 2. Try GoogleTranslator from deep_translator
        try:
            gt = GoogleTranslator(source=self.source, target=self.target)
            trans = gt.translate(text)
            if trans:
                self.sentence_cache[text] = trans
                return trans
        except Exception as e:
            print(f"[Translator] GoogleTranslator failed: {e}")

        # 3. Fallback to MyMemory
        try:
            mm = MyMemoryTranslator(source=self.source, target=self.target)
            trans = mm.translate(text)
            if trans:
                self.sentence_cache[text] = trans
                return trans
        except Exception as e:
            print(f"[Translator] MyMemory failed: {e}")

        return text

    def batch_translate_words(self, words: List[str]) -> Dict[str, str]:
        """Translates multiple unknown words in a single combined request."""
        clean_words = [w for w in words if w and w not in self.cache]
        if not clean_words:
            return {}

        results: Dict[str, str] = {}
        batch_text = "\n".join(clean_words)

        translated_lines = []
        if HAS_TRANSLATORS:
            try:
                res_text = ts.translate_text(batch_text, from_language=self.source, to_language=self.target)
                translated_lines = [line.strip().lower() for line in res_text.split("\n") if line.strip()]
            except Exception as e:
                print(f"[Translator] Batch ts.translate_text error: {e}")

        if len(translated_lines) == len(clean_words):
            for orig, trans in zip(clean_words, translated_lines):
                self.cache[orig] = trans
                results[orig] = trans
        else:
            # Fallback one-by-one with Google or MyMemory
            gt = GoogleTranslator(source=self.source, target=self.target)
            for w in clean_words:
                try:
                    tr = gt.translate(w)
                    self.cache[w] = tr.lower()
                    results[w] = tr.lower()
                except Exception:
                    self.cache[w] = w
                    results[w] = w

        self._save_cache()
        return results

    def analyze_learning_block(self, text: str) -> Dict[str, Any]:
        """
        Parses full text into tokens, gets full translation and per-word meanings.
        """
        clean_full = text.strip()
        if not clean_full:
            return {
                "original_text": "",
                "full_translation": "",
                "tokens": []
            }

        # 1. Full translation for the reveal card
        full_trans = self.translate_full_sentence(clean_full)

        # 2. Tokenize keeping punctuation and whitespace
        raw_parts = re.findall(r"[\w']+|[^\w\s]|\s+", clean_full)

        tokens: List[Dict[str, Any]] = []
        needed_words: List[str] = []

        for part in raw_parts:
            is_word = bool(re.match(r"^[\w']+$", part)) and not part.isdigit()
            clean = self.clean_word(part) if is_word else ""
            
            cached_trans = self.cache.get(clean, "") if is_word else ""
            tokens.append({
                "raw": part,
                "clean": clean,
                "is_word": is_word,
                "translation": cached_trans
            })
            if is_word and clean and clean not in self.cache and clean not in needed_words:
                needed_words.append(clean)

        # Translate missing words in batch
        if needed_words:
            new_translations = self.batch_translate_words(needed_words)
            for tok in tokens:
                if tok["is_word"] and tok["clean"] in new_translations:
                    tok["translation"] = new_translations[tok["clean"]]

        return {
            "original_text": clean_full,
            "full_translation": full_trans,
            "tokens": tokens
        }
