"""PDF text extraction + lightweight resume structuring."""
from __future__ import annotations

import io
import re

from pypdf import PdfReader

from .skills import extract_skills

SECTION_HEADERS = {
    "summary": r"(summary|objective|profile|about me)",
    "education": r"(education|academic|qualification)",
    "skills": r"(technical skills|skills|technologies|tech stack|core competencies)",
    "projects": r"(projects?|personal projects?|academic projects?)",
    "experience": r"(experience|internships?|work history|employment)",
    "certifications": r"(certifications?|certificates?|courses)",
    "achievements": r"(achievements?|awards?|honou?rs|positions of responsibility|extra[- ]?curricular)",
}


class ResumeParseError(ValueError):
    pass


def extract_text_from_pdf(data: bytes) -> str:
    if not data.startswith(b"%PDF"):
        raise ResumeParseError("File does not look like a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ResumeParseError("PDF is password-protected.")
        pages = [(p.extract_text() or "") for p in reader.pages]
    except ResumeParseError:
        raise
    except Exception as e:  # pypdf raises many types on malformed files
        raise ResumeParseError(f"Could not read PDF: {e}")
    text = "\n".join(pages)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 80:
        raise ResumeParseError(
            "Very little text found. If this is a scanned/image PDF, export a text-based PDF instead."
        )
    return text


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        stripped = line.strip().strip(":|-–• ").strip()
        matched = None
        if 0 < len(stripped) <= 40:
            for name, pat in SECTION_HEADERS.items():
                if re.fullmatch(pat, stripped, flags=re.I):
                    matched = name
                    break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def parse_resume(text: str) -> dict:
    sections = _split_sections(text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?\d{1,3}[\s-]?)?\d{10}|\+?\d[\d\s-]{9,14}\d", text)
    links = sorted(set(re.findall(r"(?:https?://)?(?:www\.)?(?:github\.com|linkedin\.com)/[\w\-./]+", text, flags=re.I)))
    skills = extract_skills(text)

    def bullets(section: str) -> list[str]:
        body = sections.get(section, "")
        return [re.sub(r"^[•\-*▪●\u2022]\s*", "", l.strip()) for l in body.splitlines() if l.strip()]

    projects_lines = bullets("projects")
    metrics = re.findall(r"\b\d+(?:\.\d+)?\s?(?:%|x|k\b|\+|ms|users|requests|lpa)|\b\d{2,}\b", text)
    action_verbs = len(re.findall(
        r"\b(built|developed|designed|implemented|created|optimi[sz]ed|led|deployed|automated|reduced|improved|integrated|engineered)\b",
        text, flags=re.I))

    return {
        "name": lines[0] if lines else "",
        "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "",
        "links": links,
        "sections_found": [s for s in sections if s != "header"],
        "sections": sections,
        "skills": dict(skills),
        "projects": projects_lines[:25],
        "education": bullets("education")[:10],
        "experience": bullets("experience")[:20],
        "certifications": bullets("certifications")[:15],
        "word_count": len(text.split()),
        "metric_count": len(metrics),
        "action_verb_count": action_verbs,
    }
