import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def review_code(code: str, language: str, filename: str = "code") -> dict:
    from groq import Groq

    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set in your .env file. Get a free key at https://console.groq.com"
        )

    client = Groq(api_key=GROQ_API_KEY)

    prompt = (
        f"You are an expert senior software engineer performing a thorough code review.\n\n"
        f'Analyze the following {language} code from file "{filename}" and return ONLY a valid JSON object.\n\n'
        f"Code to review:\n{code}\n\n"
        f"Return this exact JSON structure:\n"
        "{{\n"
        '  "review_score": <integer 0-100>,\n'
        '  "summary": "<2-4 sentence overall assessment>",\n'
        '  "bugs": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "security_vulnerabilities": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "performance_issues": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "code_smells": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "best_practice_violations": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "maintainability_issues": [\n'
        "    {{\n"
        '      "title": "<short title>",\n'
        '      "description": "<detailed explanation>",\n'
        '      "line_number": <integer or null>,\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "suggestion": "<how to fix>"\n'
        "    }}\n"
        "  ],\n"
        '  "suggestions": [\n'
        '    "<actionable improvement suggestion 1>",\n'
        '    "<actionable improvement suggestion 2>",\n'
        '    "<actionable improvement suggestion 3>",\n'
        '    "<actionable improvement suggestion 4>",\n'
        '    "<actionable improvement suggestion 5>"\n'
        "  ],\n"
        '  "optimized_code": "<the full improved/refactored version of the code>"\n'
        "}}\n\n"
        "Rules:\n"
        "- review_score: 100 = perfect code, 0 = completely broken. Score realistically.\n"
        "- Each list can be empty [] if nothing found in that category.\n"
        "- optimized_code must be a complete working version with all fixes applied.\n"
        "- suggestions must be concrete, actionable recommendations.\n"
        "- Return ONLY the JSON object, nothing else."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse AI response: {raw[:300]}")

    categories = {
        "bugs": "Bug",
        "security_vulnerabilities": "Security",
        "performance_issues": "Performance",
        "code_smells": "Code Smell",
        "best_practice_violations": "Best Practice",
        "maintainability_issues": "Maintainability",
    }

    all_issues = []
    bug_count = 0
    issue_count = 0

    for key, label in categories.items():
        items = data.get(key, [])
        for item in items:
            all_issues.append(
                {
                    "category": label,
                    "severity": item.get("severity", "low"),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "line_number": item.get("line_number"),
                    "suggestion": item.get("suggestion", ""),
                }
            )
            if key == "bugs":
                bug_count += 1
            else:
                issue_count += 1

    return {
        "review_score": max(0, min(100, int(data.get("review_score", 50)))),
        "summary": data.get("summary", "Review completed."),
        "suggestions": data.get("suggestions", []),
        "optimized_code": data.get("optimized_code", code),
        "issues": all_issues,
        "bug_count": bug_count,
        "issue_count": issue_count,
    }
