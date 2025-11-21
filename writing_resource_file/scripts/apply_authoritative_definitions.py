#!/usr/bin/env python3
"""
Apply authoritative one-line definitions to `bad_smells_info.json` for a set
of known smells/metrics. Creates a backup before writing.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "bad_smells_info.json"
BACKUP_PATH = ROOT / "bad_smells_info.json.bak.authoritative_defs"

if not JSON_PATH.exists():
    print(f"Error: {JSON_PATH} not found.")
    raise SystemExit(1)

shutil.copy2(JSON_PATH, BACKUP_PATH)

with JSON_PATH.open("r", encoding="utf-8") as f:
    data = json.load(f)

mapping = {
    # Code smells
    "Switch Statements": "A pattern of nested or long conditional branches that reduces clarity and maintainability.",
    "Temporary Field": "A field assigned only in certain contexts or used temporarily, indicating misplaced state that may belong elsewhere.",
    "Alternative Classes with Different Interfaces": "Sets of classes that provide similar behavior via different method names or signatures, suggesting duplicated roles and poor polymorphism.",
    "Potential Divergent Change": "A class that requires many unrelated changes for a single modification, indicating mixed responsibilities and low cohesion.",
    "Parallel Inheritance Hierarchies": "Two inheritance hierarchies that mirror each other, implying duplication across class families and a missed abstraction.",
    "Potential Shotgun Surgery": "When a single conceptual change requires edits across many classes or files, increasing maintenance cost and risk.",
    "Excessive Comments": "An unusually large amount of comments relative to code, often signaling confusing code or compensating explanations.",
    "Duplicate Code": "Identical or very similar code existing in multiple places, which makes maintenance error-prone and hinders refactoring.",
    "Data Class": "A class that holds data with little or no behavior, suggesting missing encapsulated behavior that should belong to the class.",
    "Dead Code": "Code (functions, classes, or branches) that is never executed or referenced, increasing maintenance burden and noise.",
    "Lazy Class": "A class that does too little to justify its existence and can be simplified or merged into collaborators.",
    "Speculative Generality": "Code designed to be generic or extensible for anticipated needs that never materialize, adding unnecessary complexity.",
    "Feature Envy": "A method that uses more features of other classes than of its own class, indicating behavior should be moved nearer to the data it uses.",
    "Inappropriate Intimacy": "Classes that access each other's internal details excessively, breaking encapsulation and increasing coupling.",
    "Message Chains": "Long chains of calls (a.b().c().d()) where client code navigates through multiple objects, making the code fragile.",
    "Middle Man": "A class whose methods simply delegate to another class, adding indirection without value and suggesting removal or inlining.",
    "Hub-like Dependency": "A module that many other modules depend on, creating a bottleneck and making changes risky.",
    "Scattered Functionality": "Related functionality spread across multiple places rather than localized, making changes and reasoning harder.",
    "Potential Redundant Abstractions": "Layers or abstractions added without concrete use, increasing indirection and reducing clarity.",
    "God Object": "A class that centralizes too many responsibilities or data, becoming large and hard to maintain.",
    "Potential Improper API Usage": "Patterns where APIs are used in ways likely to be incorrect or fragile, indicating misuse of the API contract.",
    "Orphan Module": "A module that is poorly connected or left isolated, often indicating dead code or misplacement.",
    "Cyclic Dependency": "Two or more modules/classes depend on each other in a cycle, complicating build, reuse, and testing.",
    "Unstable Dependency": "Depending on modules that change frequently or are volatile, increasing maintenance risk for dependents.",
    # Metrics / quantitative
    "High Number of Methods (NOM)": "A class with many methods, suggesting high responsibility and potential low cohesion.",
    "High Weighted Methods per Class (WMPC)": "A metric that weights methods by complexity to indicate class complexity; high values suggest a heavy class.",
    "Large Class (SIZE2)": "A class with a large size (lines or members), indicating multiple responsibilities or poor modularization.",
    "High Weight of a Class (WAC)": "A metric indicating overall class weight (e.g., lines, methods, complexity); high values imply maintenance risk.",
    "High Lack of Cohesion of Methods (LCOM)": "A metric showing how related methods are via shared fields; high LCOM means low cohesion and may indicate a need to split the class.",
    "High Response for a Class (RFC)": "Number of methods potentially executed in response to a message to a class; large RFC suggests complex interactions and testing difficulty.",
    "High Number of Classes per Module (NOCC)": "Many classes defined in a single module/file, indicating potential modularization issues.",
    "Deep Inheritance Tree (DIT)": "A large number of ancestor classes for a class, implying increased complexity and fragility from inherited behavior.",
    "High Lines of Code (LOC)": "Large code size measured in lines, often correlated with complexity and maintenance cost.",
    "High Message Passing Coupling (MPC)": "A count of method calls between classes; high MPC indicates heavy coupling via message passing.",
    "High Coupling Between Object Classes (CBO)": "Number of classes to which a class is coupled; high CBO implies tight coupling and lower modularity.",
    "High Number of Children (NOC)": "Many immediate subclasses, which can indicate heavy reuse but also testing and design complexity.",
    "High Cyclomatic Complexity": "High number of linearly independent paths through code, indicating complex control flow and higher testing effort.",
    "High Fan-out": "A function or module that calls many others; high fan-out increases change impact and testing scope.",
    "High Fan-in": "Many callers to a module/function; high fan-in can indicate a critical utility but also a bottleneck.",
    "Long File": "A source file with many lines of code, which can reduce navigability and increase maintenance overhead.",
    "Too Many Branches": "Functions or modules with many decision points (branches), increasing complexity and test burden."
}

changed = []
for metric in data.get("metrics", []):
    name = metric.get("name")
    if name in mapping:
        guidance = metric.get("guidance", {})
        old = guidance.get("definition", "")
        guidance["definition"] = mapping[name]
        metric["guidance"] = guidance
        changed.append((name, old, mapping[name]))

if changed:
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Applied authoritative definitions to {len(changed)} metrics. Backup at: {BACKUP_PATH}")
    for name, old, new in changed:
        print(f" - {name}")
else:
    print("No matching metrics found; no changes made.")
