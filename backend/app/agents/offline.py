"""Rule-based generators used when no Groq key is configured (or an LLM call fails).

They keep the whole pipeline demo-able offline; output is templated but still driven by the
student's real skill gaps, the company knowledge base and the job description.
"""
from __future__ import annotations

import re

INTERVIEW_BANK = {
    "python": "Explain the difference between a list, tuple, set and dict in Python, and when you would use each.",
    "java": "What is the difference between an abstract class and an interface in Java? When would you pick each?",
    "c++": "Explain RAII and smart pointers in C++. Why are they preferred over raw pointers?",
    "sql": "Explain INNER vs LEFT JOIN and write a query to find the second highest salary.",
    "javascript": "What are closures and how does the event loop work in JavaScript?",
    "react": "Explain how React's virtual DOM and reconciliation work, and when you would use useMemo/useCallback.",
    "node.js": "How does Node.js handle concurrency with a single thread? What blocks the event loop?",
    "fastapi": "How does FastAPI use Pydantic and dependency injection? How would you structure a larger FastAPI app?",
    "rest api": "What makes an API RESTful? Explain idempotency and when you would use PUT vs POST vs PATCH.",
    "docker": "What is the difference between an image and a container? How do you keep a Docker image small?",
    "kubernetes": "Explain pods, deployments and services in Kubernetes and how a rolling update works.",
    "aws": "Compare EC2, Lambda and ECS. When would you choose serverless over VMs?",
    "git": "Explain merge vs rebase and how you would resolve a conflict in a shared branch.",
    "machine learning": "Explain the bias-variance trade-off and how you would detect overfitting.",
    "deep learning": "Explain backpropagation and why vanishing gradients occur. How do residual connections help?",
    "nlp": "How do word embeddings differ from contextual embeddings such as BERT?",
    "rag": "Explain how Retrieval-Augmented Generation works and how you would evaluate retrieval quality.",
    "llm": "What causes LLM hallucinations and what techniques reduce them in production?",
    "langchain": "What problem do LangChain/LangGraph solve, and when is a graph-based agent better than a simple chain?",
    "faiss": "How does FAISS perform similarity search? Compare flat, IVF and HNSW indexes.",
    "mongodb": "When would you choose MongoDB over a relational database? How do indexes work in it?",
    "redis": "What are common Redis use cases and data structures? How does persistence (RDB vs AOF) work?",
    "data structures": "Compare arrays, linked lists, hash maps and heaps: operations, complexity and typical use cases.",
    "algorithms": "Explain how you would choose between BFS, DFS, and Dijkstra for a graph problem.",
    "oop": "Explain the four OOP pillars with a real example from one of your projects.",
    "operating systems": "Explain processes vs threads, deadlock conditions, and how a scheduler works.",
    "computer networks": "What happens when you type a URL in the browser and press Enter?",
    "system design": "How would you design a URL shortener? Cover storage, ID generation and scaling reads.",
    "database design": "Explain normalization (1NF-3NF) and when denormalization is justified.",
    "networking": "Explain the difference between TCP and UDP, and how a router decides where to forward a packet.",
    "linux": "Which Linux commands do you use to debug a slow or failing service?",
    "ci/cd": "Describe a CI/CD pipeline you would set up for a web service and what each stage verifies.",
    "testing": "What is the difference between unit, integration and end-to-end tests? What would you mock and why?",
}

CODING_BANK = [
    {"title": "Two Sum", "topics": ["arrays", "hashing"], "difficulty": "Easy",
     "statement": "Given an integer array and a target, return indices of the two numbers that add up to the target. Assume exactly one solution.",
     "example": "nums=[2,7,11,15], target=9 -> [0,1]", "complexity": "O(n) time, O(n) space",
     "hint": "Store value -> index in a hash map while scanning."},
    {"title": "Valid Parentheses", "topics": ["stack", "strings"], "difficulty": "Easy",
     "statement": "Given a string containing ()[]{}, determine whether the brackets are balanced and correctly nested.",
     "example": "\"({[]})\" -> true, \"(]\" -> false", "complexity": "O(n) time, O(n) space",
     "hint": "Push opening brackets; on a closing bracket the top of the stack must match."},
    {"title": "Longest Substring Without Repeating Characters", "topics": ["sliding window", "hashing"], "difficulty": "Medium",
     "statement": "Return the length of the longest substring of a string that contains no repeated characters.",
     "example": "\"abcabcbb\" -> 3", "complexity": "O(n) time, O(k) space",
     "hint": "Maintain a window [l, r] and a map of last-seen indexes."},
    {"title": "Merge Intervals", "topics": ["arrays", "sorting"], "difficulty": "Medium",
     "statement": "Given a list of intervals, merge all overlapping intervals and return the result.",
     "example": "[[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]", "complexity": "O(n log n) time",
     "hint": "Sort by start, then extend the last merged interval while overlapping."},
    {"title": "Number of Islands", "topics": ["graphs", "bfs/dfs"], "difficulty": "Medium",
     "statement": "Given a 2D grid of '1' (land) and '0' (water), count the number of islands.",
     "example": "A 3x3 grid with two separate land groups -> 2", "complexity": "O(R*C) time",
     "hint": "Run DFS/BFS from each unvisited land cell and mark visited cells."},
    {"title": "LRU Cache", "topics": ["design", "hash map", "linked list"], "difficulty": "Medium",
     "statement": "Design a cache with get(key) and put(key, value) in O(1) that evicts the least recently used key at capacity.",
     "example": "cap=2: put(1,1), put(2,2), get(1), put(3,3) evicts key 2", "complexity": "O(1) per operation",
     "hint": "Combine a hash map with a doubly linked list (or OrderedDict)."},
    {"title": "Reverse a Linked List", "topics": ["linked list"], "difficulty": "Easy",
     "statement": "Reverse a singly linked list iteratively and recursively.",
     "example": "1->2->3 -> 3->2->1", "complexity": "O(n) time, O(1) space iteratively",
     "hint": "Track prev, curr and next pointers."},
    {"title": "Binary Tree Level Order Traversal", "topics": ["trees", "bfs"], "difficulty": "Medium",
     "statement": "Return the level-order traversal of a binary tree's node values as a list of lists.",
     "example": "[3,9,20,null,null,15,7] -> [[3],[9,20],[15,7]]", "complexity": "O(n) time",
     "hint": "BFS with a queue, processing one level (queue length) at a time."},
    {"title": "Coin Change", "topics": ["dynamic programming"], "difficulty": "Medium",
     "statement": "Given coin denominations and an amount, return the fewest coins needed to make that amount, or -1.",
     "example": "coins=[1,2,5], amount=11 -> 3", "complexity": "O(amount * coins)",
     "hint": "dp[a] = 1 + min(dp[a - c]) over coins c."},
    {"title": "Top K Frequent Elements", "topics": ["heap", "hashing"], "difficulty": "Medium",
     "statement": "Return the k most frequent elements of an integer array.",
     "example": "nums=[1,1,1,2,2,3], k=2 -> [1,2]", "complexity": "O(n log k)",
     "hint": "Count with a hash map, then keep a min-heap of size k."},
    {"title": "SQL: Second Highest Salary", "topics": ["sql"], "difficulty": "Easy",
     "statement": "Write a SQL query to return the second highest distinct salary from an Employee table, or NULL if none.",
     "example": "salaries 100,200,300 -> 200", "complexity": "n/a",
     "hint": "Use DISTINCT with ORDER BY ... LIMIT 1 OFFSET 1 inside a subquery, or DENSE_RANK()."},
    {"title": "Rate Limiter", "topics": ["design", "queue"], "difficulty": "Medium",
     "statement": "Implement a sliding-window rate limiter that allows at most N requests per user per minute.",
     "example": "N=3: 4th request inside 60s is rejected", "complexity": "O(1) amortised per request",
     "hint": "Keep a deque of timestamps per user and drop expired ones."},
]

TOPIC_TO_SKILL = {
    "sql": "sql", "design": "system design", "dynamic programming": "algorithms", "graphs": "algorithms",
    "trees": "data structures", "heap": "data structures", "linked list": "data structures", "stack": "data structures",
    "hashing": "data structures", "arrays": "data structures", "sliding window": "algorithms",
}

RESOURCE_HINTS = {
    "data structures": "NeetCode 150 / LeetCode Top Interview 150 (arrays, hashing, stacks, trees)",
    "algorithms": "NeetCode roadmap: graphs, DP, binary search, greedy",
    "sql": "LeetCode SQL 50 and practice joins, window functions, group by/having",
    "system design": "System design primer on GitHub; design a URL shortener, cache and rate limiter",
    "docker": "Official Docker 'Get started' guide; containerise one of your own projects",
    "kubernetes": "Kubernetes basics tutorial; deploy a small app on minikube/kind",
    "aws": "AWS Skill Builder / Academy labs; deploy an app on EC2 or Lambda + S3",
    "react": "Official React docs 'Learn React'; build a small dashboard with hooks",
    "python": "Official Python tutorial + practice problems on collections, generators and decorators",
    "machine learning": "Andrew Ng's ML Specialization notes + one end-to-end scikit-learn project",
    "rag": "Build a small RAG app with FAISS + sentence-transformers and evaluate retrieval hit-rate",
    "git": "Learn Git branching (interactive) and practise PR workflow on GitHub",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def offline_interview_questions(company: str, role: str, missing: list[str], matched: list[str],
                                kb: dict | None, projects: list[str], n: int = 8) -> list[dict]:
    qs: list[dict] = []
    for skill in missing[:3]:
        if skill in INTERVIEW_BANK:
            qs.append({"question": INTERVIEW_BANK[skill], "category": "skill gap", "difficulty": "Medium",
                       "focus_skill": skill, "why": f"'{skill}' appears in the job description but is missing from your resume."})
    for skill in matched[:8]:
        if skill in INTERVIEW_BANK and len(qs) < n - 3:
            qs.append({"question": INTERVIEW_BANK[skill], "category": "resume skill", "difficulty": "Medium",
                       "focus_skill": skill, "why": f"You list '{skill}' on your resume, so expect a depth check."})
    if projects:
        qs.append({"question": "Walk me through your strongest project: the problem, your design decisions, the hardest bug and what you would improve.",
                   "category": "project", "difficulty": "Medium", "focus_skill": "projects",
                   "why": "Project deep-dives are asked in almost every technical round."})
    for t in (kb or {}).get("themes", [])[:2]:
        qs.append({"question": t if t.endswith("?") else t + ".", "category": f"{company} theme", "difficulty": "Medium",
                   "focus_skill": "company", "why": f"Commonly seen theme for {company}-style hiring."})
    qs.append({"question": "Tell me about a time you worked under a tight deadline or resolved a conflict in a team.",
               "category": "behavioral", "difficulty": "Easy", "focus_skill": "communication",
               "why": "Behavioral rounds look for ownership and teamwork (use the STAR format)."})
    seen, out = set(), []
    for q in qs:
        if q["question"] not in seen:
            seen.add(q["question"]); out.append(q)
    for generic in ["Explain the difference between processes and threads.", "What are ACID properties in databases?"]:
        if len(out) < n and generic not in seen:
            out.append({"question": generic, "category": "fundamentals", "difficulty": "Easy",
                        "focus_skill": "cs fundamentals", "why": "Core CS fundamentals are common filters."})
    return out[:n]


def offline_coding_questions(company: str, missing: list[str], kb: dict | None, n: int = 4) -> list[dict]:
    want = set(missing)
    focus_text = " ".join((kb or {}).get("focus", [])).lower()
    scored = []
    for p in CODING_BANK:
        s = 0
        for t in p["topics"]:
            if TOPIC_TO_SKILL.get(t) in want:
                s += 2
            if t.split()[0] in focus_text:
                s += 1
        s += {"Easy": 0.3, "Medium": 0.2}.get(p["difficulty"], 0)
        scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    out = []
    for _, p in scored[:n]:
        out.append({"title": p["title"], "statement": p["statement"], "difficulty": p["difficulty"],
                    "topics": p["topics"], "example": p["example"], "hint": p["hint"],
                    "expected_complexity": p["complexity"],
                    "why": f"Targets {', '.join(p['topics'])} for {company or 'your target'} style rounds."})
    return out


def offline_roadmap(missing: list[str], weak_areas: list[str], company: str, role: str,
                    weeks: int = 6, hours_per_week: int = 10) -> dict:
    """Deterministic week-by-week plan from missing skills + standard placement prep blocks."""
    focus = (missing[:6] or ["data structures"]) 
    plan_weeks = []
    skill_cycle = focus + ["data structures", "algorithms", "sql", "system design"]
    for w in range(1, weeks + 1):
        skill = skill_cycle[(w - 1) % len(skill_cycle)]
        tasks = [
            {"title": f"Learn core concepts of {skill}", "type": "learn", "skill": skill, "est_hours": 3,
             "resource": RESOURCE_HINTS.get(skill, f"Official docs / a structured course on {skill}")},
            {"title": f"Build or extend a mini-project using {skill} and add it to your resume", "type": "project", "skill": skill, "est_hours": 3},
            {"title": "Solve 6 coding problems (2 easy, 3 medium, 1 hard) and write down patterns", "type": "practice",
             "skill": "data structures" if w % 2 else "algorithms", "est_hours": 3},
            {"title": "Do one timed mock HR/technical interview in PlacementPilot and review feedback", "type": "interview",
             "skill": "communication", "est_hours": 1},
        ]
        if w == 1:
            tasks.append({"title": "Rewrite resume bullets with action verbs + metrics and add missing keywords honestly", "type": "resume",
                          "skill": "resume", "est_hours": 2})
        if w == weeks:
            tasks.append({"title": f"Full mock round simulating {company or 'the company'} process; revise weak topics", "type": "interview",
                          "skill": "mock", "est_hours": 3})
        plan_weeks.append({"week": w, "theme": f"{skill.title()} + problem solving", "goals": [
            f"Be able to explain {skill} in an interview", "Finish all tasks and log your scores"], "tasks": tasks})
    return {"weeks": plan_weeks, "summary": f"{weeks}-week plan for {role or 'your target role'} at {company or 'your target company'} "
                                              f"focused on: {', '.join(focus)}."}


def offline_evaluate(answer: str) -> dict:
    words = answer.split()
    n = len(words)
    low = answer.lower()
    star = sum(k in low for k in ["situation", "task", "action", "result", "because", "so that", "learned", "outcome"])
    has_num = bool(re.search(r"\d", answer))
    first_person = len(re.findall(r"\b(i|my|we|our)\b", low))
    fillers = len(re.findall(r"\b(um+|uh+|like|basically|actually|you know)\b", low))
    clarity = max(0, min(10, 4 + (2 if 40 <= n <= 220 else 0) - min(3, fillers) + (1 if n > 20 else -3)))
    structure = max(0, min(10, 3 + star + (1 if "first" in low or "then" in low or "finally" in low else 0)))
    impact = max(0, min(10, 3 + (3 if has_num else 0) + min(3, first_person // 3)))
    relevance = max(0, min(10, 5 + (2 if n >= 30 else -2)))
    overall = round((clarity + structure + impact + relevance) / 4, 1)
    improvements = []
    if n < 40: improvements.append("Answer is short: add context, your specific actions and the outcome.")
    if structure < 6: improvements.append("Use the STAR structure (Situation, Task, Action, Result).")
    if not has_num: improvements.append("Quantify impact with numbers (time saved, users, accuracy, performance).")
    if fillers > 2: improvements.append("Reduce filler words; pause briefly instead.")
    return {"clarity": clarity, "structure": structure, "impact": impact, "relevance": relevance, "overall": overall,
            "strengths": ["Clear first-person ownership"] if first_person >= 3 else [],
            "improvements": improvements or ["Good answer: add one concrete example to make it memorable."],
            "followup": "Can you give a specific example with measurable results?" if (n < 60 or not has_num) else ""}
