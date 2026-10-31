from backend.app.agents.knowledge import find_company
from backend.app.core.skills import extract_skills


def test_skill_extraction_handles_symbols():
    s = extract_skills("Experienced in C++, C#, Node.js and CI/CD; used Go lang, not 'the rest of it'.")
    assert {"c++", "c#", "node.js", "ci/cd", "go"} <= set(s)
    assert "rest api" not in s


def test_company_lookup():
    assert find_company("TCS")["company"] == "TCS"
    assert find_company("Tata Consultancy Services")["company"] == "TCS"
    assert find_company("Some Unknown Startup XYZ")["company"] == "Generic"
