# Data Generation Specification

## Purpose

Generate a realistic `articles.json` file containing 200 industrial support articles. This dataset serves as the knowledge base for the RAG system. The data must be deterministic (seeded random) so that retrieval metrics are reproducible.

## Output File

- **Path**: `/app/data/articles.json`
- **Format**: JSON array of 200 article objects.

## Article Schema

```json
{
  "id": "article_001",
  "title": "Resolving Power Supply Error E452 on Server Units",
  "body": "Error E452 indicates a power delivery fault detected by the onboard monitoring system...",
  "metadata": {
    "source": "maintenance_manual",
    "error_code": "E452",
    "product": "server"
  }
}
```

## Generation Rules

### ID Format
- `article_001` through `article_200` (zero-padded to 3 digits).

### Titles
- Format: `{Action} {Topic} {Context}`
- Action verbs: Resolving, Troubleshooting, Configuring, Installing, Calibrating, Replacing, Updating, Inspecting, Diagnosing, Maintaining
- Must include the error code (if applicable) and product name.
- Example: `"Troubleshooting Network Timeout Error E305 on Industrial Router"`

### Body Content
Each article body should be 300–600 words of realistic industrial documentation covering:

1. **Problem statement** — What the issue is and when it occurs.
2. **Symptoms** — Observable indicators (LED patterns, log messages, error displays).
3. **Root causes** — 2–3 possible causes ranked by likelihood.
4. **Resolution steps** — Numbered step-by-step procedure.
5. **Verification** — How to confirm the fix worked.
6. **References** — Related error codes or articles.

### Source Distribution

| Source Type | Count | Body Characteristics |
|------------|-------|---------------------|
| `maintenance_manual` | 60 | Formal, step-by-step procedures with safety warnings |
| `troubleshooting_guide` | 50 | Symptom → diagnosis → fix flow, decision trees |
| `release_notes` | 30 | Changelog format: version, date, fixes, known issues |
| `safety_bulletin` | 30 | Compliance language, severity ratings, mandatory actions |
| `installation_guide` | 30 | Prerequisites, wiring diagrams (described), commissioning |

### Product Distribution

| Product | Count | Technical Vocabulary |
|---------|-------|---------------------|
| `server` | 40 | PSU, DIMM, BMC, IPMI, RAID, thermal, fan RPM |
| `router` | 35 | OSPF, BGP, VLAN, latency, packet loss, firmware |
| `switch` | 30 | PoE, SFP, spanning tree, port mirroring, MAC table |
| `gateway` | 25 | Modbus, OPC-UA, protocol conversion, register mapping |
| `controller` | 25 | PLC, ladder logic, scan cycle, I/O module, watchdog |
| `sensor` | 25 | 4-20mA, calibration, drift, zero-point, span |
| `actuator` | 20 | Valve, stroke, positioner, feedback, deadband |

### Error Code Assignment

- ~120 of 200 articles include an error code.
- Error codes: `E100` through `E999` following the ranges in `08_data_model_and_chroma.md`.
- Each error code appears in 1–3 articles (different perspectives: manual, troubleshooting, release notes).
- ~80 articles have `error_code: null` (general procedures, installation, safety topics).

### Vocabulary & Realism

Use domain-specific technical language:

```
# Hardware terms
PSU, DIMM, SFP, PCB, heatsink, thermal paste, ribbon cable,
DIN rail, terminal block, junction box, conduit

# Network terms  
OSPF, BGP, VLAN, subnet, gateway, DHCP, DNS, NTP, SNMP,
packet loss, jitter, latency, throughput, MTU

# Industrial terms
4-20mA, 0-10V, Modbus RTU, Modbus TCP, OPC-UA, PROFINET,
ladder logic, function block, scan cycle, watchdog timer,
PID loop, setpoint, deadband, hysteresis

# Measurement
PSI, bar, °C, °F, RPM, Ohm, mA, VDC, VAC, Hz
```

## Generation Script

```python
#!/usr/bin/env python3
"""Generate articles.json for the Industrial RAG Demonstrator."""

import json
import random

SEED = 42
random.seed(SEED)

PRODUCTS = {
    "server": {"count": 40, "terms": ["PSU", "DIMM", "BMC", "IPMI", "RAID", "thermal", "fan RPM", "heatsink", "PCB"]},
    "router": {"count": 35, "terms": ["OSPF", "BGP", "VLAN", "latency", "packet loss", "firmware", "routing table"]},
    "switch": {"count": 30, "terms": ["PoE", "SFP", "spanning tree", "port mirroring", "MAC table", "VLAN"]},
    "gateway": {"count": 25, "terms": ["Modbus", "OPC-UA", "protocol conversion", "register mapping", "polling"]},
    "controller": {"count": 25, "terms": ["PLC", "ladder logic", "scan cycle", "I/O module", "watchdog timer"]},
    "sensor": {"count": 25, "terms": ["4-20mA", "calibration", "drift", "zero-point", "span", "transmitter"]},
    "actuator": {"count": 20, "terms": ["valve", "stroke", "positioner", "feedback", "deadband", "pneumatic"]},
}

SOURCES = {
    "maintenance_manual": 60,
    "troubleshooting_guide": 50,
    "release_notes": 30,
    "safety_bulletin": 30,
    "installation_guide": 30,
}

ERROR_RANGES = {
    "hardware": (100, 299),
    "network": (300, 499),
    "software": (500, 699),
    "config": (700, 899),
    "safety": (900, 999),
}

def generate_error_code(product: str) -> str | None:
    """Generate an error code appropriate for the product, or None."""
    if random.random() > 0.60:  # 60% chance of having an error code
        return None

    if product in ("server", "actuator", "sensor"):
        range_key = "hardware"
    elif product in ("router", "switch", "gateway"):
        range_key = "network"
    elif product in ("controller",):
        range_key = random.choice(["software", "config"])
    else:
        range_key = random.choice(list(ERROR_RANGES.keys()))

    low, high = ERROR_RANGES[range_key]
    return f"E{random.randint(low, high)}"


def generate_article(article_id: int, product: str, source: str) -> dict:
    """Generate a single article. Body is a placeholder template."""
    error_code = generate_error_code(product)
    terms = PRODUCTS[product]["terms"]

    title = build_title(product, source, error_code, terms)
    body = build_body(product, source, error_code, terms)

    return {
        "id": f"article_{article_id:03d}",
        "title": title,
        "body": body,
        "metadata": {
            "source": source,
            "error_code": error_code,
            "product": product,
        },
    }


def build_title(product, source, error_code, terms):
    """Build a realistic article title."""
    # ... (implementation generates context-appropriate titles)
    pass


def build_body(product, source, error_code, terms):
    """Build a realistic article body (300-600 words)."""
    # ... (implementation generates structured technical content)
    pass


def main():
    articles = []
    article_id = 1

    # Build assignment lists
    product_assignments = []
    for product, info in PRODUCTS.items():
        product_assignments.extend([product] * info["count"])
    random.shuffle(product_assignments)

    source_assignments = []
    for source, count in SOURCES.items():
        source_assignments.extend([source] * count)
    random.shuffle(source_assignments)

    for product, source in zip(product_assignments, source_assignments):
        article = generate_article(article_id, product, source)
        articles.append(article)
        article_id += 1

    with open("data/articles.json", "w") as f:
        json.dump(articles, f, indent=2)

    print(f"Generated {len(articles)} articles → data/articles.json")


if __name__ == "__main__":
    main()
```

> **Note**: The `build_title()` and `build_body()` functions should be implemented to produce realistic content. For the initial version, use an LLM (e.g., the Cerebras API itself) to batch-generate realistic industrial articles following the templates above, then save the output as a static `articles.json`.

## Validation Criteria

After generation, the dataset must pass these checks:

```python
def validate_articles(articles: list[dict]):
    assert len(articles) == 200, f"Expected 200 articles, got {len(articles)}"

    ids = [a["id"] for a in articles]
    assert len(set(ids)) == 200, "Duplicate article IDs found"

    for a in articles:
        assert len(a["body"].split()) >= 300, f"{a['id']} body too short"
        assert len(a["body"].split()) <= 600, f"{a['id']} body too long"
        assert a["metadata"]["source"] in SOURCES
        assert a["metadata"]["product"] in PRODUCTS
        if a["metadata"]["error_code"]:
            assert re.match(r"^E\d{3}$", a["metadata"]["error_code"])

    # Check distributions
    source_counts = Counter(a["metadata"]["source"] for a in articles)
    product_counts = Counter(a["metadata"]["product"] for a in articles)
    error_count = sum(1 for a in articles if a["metadata"]["error_code"])

    print(f"Sources: {dict(source_counts)}")
    print(f"Products: {dict(product_counts)}")
    print(f"Articles with error codes: {error_count}/200")
```
