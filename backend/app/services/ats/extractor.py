import json
import os
import re
from typing import Any

from rapidfuzz import fuzz

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

REQUIRED_HEADERS = re.compile(
    r"(required\s+qualifications|minimum\s+qualifications|must\s+have|requirements|what\s+you['’]?ll\s+need)",
    re.IGNORECASE,
)
PREFERRED_HEADERS = re.compile(
    r"(preferred\s+qualifications|nice\s+to\s+have|bonus\s+qualifications|bonus\s+points|preferred\s+skills|desired)",
    re.IGNORECASE,
)

class SkillTaxonomyMatcher:
    def __init__(self):
        self.skills: list[dict[str, Any]] = []
        self.term_to_skill: dict[str, dict[str, Any]] = {}
        self.terms_by_ngram: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: []}
        self._load_taxonomy()

    def _load_taxonomy(self):
        tax_path = os.path.join(DATA_DIR, "skills_taxonomy.json")
        if not os.path.exists(tax_path):
            return
        
        with open(tax_path, encoding="utf-8") as f:
            self.skills = json.load(f)

        for skill in self.skills:
            all_terms = [skill["name"].lower()] + [a.lower() for a in skill.get("aliases", [])]
            for term in all_terms:
                clean_term = re.sub(r"[^\w\s\+#\./-]", "", term).strip()
                if not clean_term:
                    continue
                words = clean_term.split()
                n = min(4, max(1, len(words)))
                self.term_to_skill[clean_term] = skill
                self.terms_by_ngram[n].append(clean_term)

    def extract_skills_from_text(self, text: str) -> list[dict[str, Any]]:
        """
        Extracts skills with evidence snippet.
        Matches 1-4 grams, and rapidfuzz ratio >= 92 for near matches.
        """
        matched_skills: dict[str, dict[str, Any]] = {}

        # Tokenize lines to track context snippets
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            normalized_line = " " + re.sub(r"[^\w\s\+#\./-]", " ", line.lower()) + " "
            
            # Check terms
            for n in (4, 3, 2, 1):
                for term in self.terms_by_ngram[n]:
                    # Search exact boundary or substring
                    pattern = r"(?:^|\s|[.,;/])" + re.escape(term) + r"(?:$|\s|[.,;/])"
                    if re.search(pattern, normalized_line):
                        skill = self.term_to_skill[term]
                        skill_id = skill["id"]
                        if skill_id not in matched_skills:
                            matched_skills[skill_id] = {
                                "skill_id": skill_id,
                                "name": skill["name"],
                                "category": skill["category"],
                                "evidence": line[:160],  # Keep line snippet as evidence
                                "occurrences": 1,
                            }
                        else:
                            matched_skills[skill_id]["occurrences"] += 1

        # Near match fallback with rapidfuzz >= 92 on individual words/bigrams
        # for uncaptured skills
        words = re.findall(r"\b[a-zA-Z0-9\+#\./-]{3,}\b", text.lower())
        unique_words = set(words)
        
        for w in unique_words:
            for term, skill in self.term_to_skill.items():
                skill_id = skill["id"]
                if skill_id in matched_skills:
                    continue
                # Only compare words of similar length
                if abs(len(w) - len(term)) <= 2:
                    score = fuzz.ratio(w, term)
                    if score >= 92:
                        # Find snippet where word appears
                        snippet = ""
                        for line in lines:
                            if w in line.lower():
                                snippet = line[:160]
                                break
                        matched_skills[skill_id] = {
                            "skill_id": skill_id,
                            "name": skill["name"],
                            "category": skill["category"],
                            "evidence": snippet or f"Matched near '{w}'",
                            "occurrences": 1,
                        }

        return list(matched_skills.values())

    def extract_weighted_skills_from_jd(self, jd_text: str) -> list[dict[str, Any]]:
        """
        Extracts skills from Job Description with weighting:
        1.5 if in required section or repeated >= 3 times
        0.6 if in preferred section
        1.0 default
        """
        lines = jd_text.splitlines()
        current_weight_multiplier = 1.0
        
        # Partition lines by section
        line_weights = []
        for line in lines:
            clean = line.strip()
            if REQUIRED_HEADERS.search(clean):
                current_weight_multiplier = 1.5
            elif PREFERRED_HEADERS.search(clean):
                current_weight_multiplier = 0.6
            line_weights.append((clean, current_weight_multiplier))

        base_skills = self.extract_skills_from_text(jd_text)
        weighted_skills = []

        for skill in base_skills:
            skill_id = skill["skill_id"]
            name_lower = skill["name"].lower()
            
            # Count occurrences in raw text
            occurrences = skill.get("occurrences", 1)

            # Determine section weight
            max_sec_weight = 1.0
            for line, w in line_weights:
                if name_lower in line.lower():
                    if w > max_sec_weight:
                        max_sec_weight = w
                    elif w == 0.6 and max_sec_weight == 1.0:
                        max_sec_weight = 0.6

            # Apply rule: 1.5 if in required section OR repeated >= 3 times
            if occurrences >= 3 or max_sec_weight == 1.5:
                final_weight = 1.5
            elif max_sec_weight == 0.6:
                final_weight = 0.6
            else:
                final_weight = 1.0

            weighted_skills.append({
                "skill_id": skill_id,
                "name": skill["name"],
                "category": skill["category"],
                "weight": final_weight,
                "occurrences": occurrences,
            })

        # Sort descending by weight, then occurrences
        weighted_skills.sort(key=lambda x: (x["weight"], x["occurrences"]), reverse=True)
        return weighted_skills

_matcher_instance: SkillTaxonomyMatcher | None = None

def get_taxonomy_matcher() -> SkillTaxonomyMatcher:
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = SkillTaxonomyMatcher()
    return _matcher_instance
