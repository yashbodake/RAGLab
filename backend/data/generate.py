#!/usr/bin/env python3
"""Generate articles.json for the Industrial RAG Demonstrator."""

import json
import os
import random
import re
from collections import Counter

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

# Pre-generate unique error codes for each product type to ensure consistency
# Factual error codes range E100-E999
ERROR_CODES = {}
for range_key, (low, high) in ERROR_RANGES.items():
    # Generate a pool of error codes for this category
    codes = [f"E{i}" for i in range(low, high + 1)]
    random.shuffle(codes)
    ERROR_CODES[range_key] = codes

# Track error codes to reuse them 1-3 times
REUSABLE_ERRORS = {p: [] for p in PRODUCTS}

def get_error_code(product: str, index: int, total_assigned_errors: int) -> str | None:
    """Assign an error code based on product, deterministic pool, and target distribution."""
    # Approximately 120 of 200 should have error codes (60% probability)
    # To be precise, we want exactly 120 articles to have error codes.
    # Let's check how many articles we have generated so far and control it.
    if total_assigned_errors >= 120:
        return None
    # Let's say if we are in the last 80 articles and we need to fill up to 120, we assign.
    # But for a simple seeded random check, we can use probability. Let's make it deterministic.
    # We will pre-generate the error assignment mask.
    return None # Handled in main() instead

def build_title(product: str, source: str, error_code: str | None, terms: list[str]) -> str:
    """Build a realistic article title."""
    actions = {
        "maintenance_manual": ["Replacing", "Maintaining", "Inspecting", "Calibrating"],
        "troubleshooting_guide": ["Troubleshooting", "Diagnosing", "Resolving", "Debugging"],
        "release_notes": ["Updating", "Optimizing", "Improving", "Refining"],
        "safety_bulletin": ["Safety Audit of", "Mandatory Inspection of", "Hazard Mitigation for", "Compliance Standards on"],
        "installation_guide": ["Installing", "Configuring", "Commissioning", "Integrating"],
    }
    
    action = random.choice(actions[source])
    term = random.choice(terms)
    
    err_str = f" Error {error_code}" if error_code else ""
    
    contexts = [
        f"on Industrial {product.capitalize()} Units",
        f"in High-Reliability {product.capitalize()} Systems",
        f"for {product.capitalize()} Integration Projects",
        f"to Prevent System Shutdowns on {product.capitalize()} Modules",
        f"during Routine {product.capitalize()} Diagnostics",
    ]
    context = random.choice(contexts)
    
    return f"{action} {term}{err_str} {context}"

def build_body(product: str, source: str, error_code: str | None, terms: list[str]) -> str:
    """Build a realistic article body of 300-600 words covering the 6 required sections."""
    err_str = f"error code {error_code}" if error_code else f"a general {product} system alert"
    
    # 1. Problem Statement
    prob_templates = [
        f"The industrial facility experienced an operational anomaly involving the {product} module, specifically manifesting as a failure in the {terms[0]} interface. Under nominal operations, the {product} maintains strict duty cycles, but high thermal dissipation or electrical transients can degrade the {terms[1]} leading to unexpected fail-safe states. This behavior is documented under {err_str} and primarily affects deployments in harsh environmental conditions.",
        f"During active production cycles, technicians observed intermittent performance degradation on the {product} unit. This malfunction is localized to the {terms[0]} subsystem, resulting in communications dropouts and signal attenuation. When {err_str} is flagged by the supervisor watchdog, the system transitions to a degraded state to prevent permanent damage to the {terms[1]} circuitry."
    ]
    prob_part = random.choice(prob_templates)
    
    # 2. Symptoms
    symptom_templates = [
        f"The physical indicators on the {product} chassis present distinct visual alarms. The primary status LED blinks amber at 2 Hz, indicating a critical sub-system fault. Log outputs retrieved via console connections show frequent warnings related to {terms[0]} threshold violations and unexpected telemetry drift. Additionally, the control bus reports register read timeout exceptions, and remote telemetrics record high jitter or latency spikes.",
        f"Operational telemetry shows immediate indicators of the failure. The actuator or sensor feedback loops report raw values outside the standard 4-20mA range, fluctuating between 3.2mA and 21.8mA. For network modules, packet loss exceeds 12% across active VLAN channels. Diagnostic logs register {err_str} assertions, coupled with abnormal temperature readings near the main {terms[1]} heatsink interface."
    ]
    symptom_part = random.choice(symptom_templates)
    
    # 3. Root Causes
    root_templates = [
        f"A detailed forensic inspection identified two main root causes for this event. First, thermal fatigue on the {terms[0]} solder joints can cause micro-fractures, introducing transient open-circuits. Second, electromagnetic interference (EMI) from adjacent high-voltage power conduits induces noise on the ribbon cables, causing the onboard microcontroller to interpret the signal corruption as a hardware fault. Lastly, component aging of the electrolytic capacitors in the power stage can lead to voltage ripple exceeds the 5% tolerance threshold.",
        f"Engineers trace the malfunction to two potential origins. The most probable cause is a firmware mismatch in the {product} control block, which fails to accurately calibrate the {terms[0]} baseline under heavy polling loads. A secondary root cause is environmental ingress; high humidity levels in the NEMA enclosure accelerate contacts oxidation on the {terms[1]} terminal blocks, resulting in resistance drift and signal degradation."
    ]
    root_part = random.choice(root_templates)
    
    # 4. Resolution Steps
    res_manual_steps = [
        "1. De-energize the entire cabinet and verify zero voltage at all input terminal blocks using a calibrated digital multimeter.\n"
        "2. Carefully extract the faulty module from the DIN rail or rack mount, taking appropriate ESD safety precautions.\n"
        f"3. Perform a visual inspection of the {terms[0]} assembly, looking for signs of thermal stress, discoloration, or bulging components.\n"
        f"4. Replace the internal ribbon cable or connector assembly with an OEM replacement part certified for high-vibration environments.\n"
        f"5. Re-seat the module, restore primary line voltage, and monitor the {terms[1]} output level to ensure correct startup initialization sequence.",
        
        "1. Clean all contact surfaces using an approved electrical contact cleaner and a lint-free swab to remove oxidation layers.\n"
        "2. Check the torque on all terminal block screws, ensuring wire connections are secured to 0.5 Nm of torque.\n"
        f"3. Access the administrative console via a secure ssh connection and run the diagnostics self-test on the {terms[0]} controller.\n"
        f"4. If firmware version is below the recommended baseline, flash the latest stable firmware patch using the secure TFTP server.\n"
        "5. Force a hard reboot of the controller and verify that the startup self-test logs no active faults."
    ]
    res_part = "Resolution Steps:\n" + random.choice(res_manual_steps)
    
    # 5. Verification
    ver_templates = [
        f"To confirm the resolution was successful, initiate a 24-hour diagnostic burn-in loop. Monitor the {terms[0]} telemetry data points, ensuring drift remains within +/- 0.5% of the calibrated span. Check that no further {err_str} events are logged in the persistent memory buffer. Finally, measure the voltage stability at the test points to confirm ripple remains below 50mV peak-to-peak under full operational load.",
        f"Verification requires executing the standard operational check procedure. Verify that all status LEDs return to a solid green state, indicating normal operation. Run a ping loop or Modbus register scan for 1000 cycles, verifying 0% packet loss or register read errors. Inspect the {terms[1]} feedback values, ensuring they track the input command setpoint with minimal overshoot."
    ]
    ver_part = "Verification:\n" + random.choice(ver_templates)
    
    # 6. References
    ref_templates = [
        f"Refer to the general Industrial {product.capitalize()} Maintenance Guide, Section 4.2, for comprehensive troubleshooting diagrams. For related issues, consult safety bulletins regarding ESD precautions and installation standards for NEMA enclosures.",
        f"See release notes for firmware version v2.4.1 for related fixes. For further details on {terms[0]} calibration procedures, reference the standard calibration manual."
    ]
    ref_part = "References:\n" + random.choice(ref_templates)
    
    # Concatenate all parts with some filler text to ensure word count target is met (300-600 words)
    filler_p1 = "It is highly recommended that only qualified personnel perform these maintenance tasks. Always adhere to national electrical codes and plant-specific safety guidelines to prevent personal injury or equipment damage. Failure to follow the specified resolution steps can result in voiding the manufacturer warranty and may cause prolonged production downtime in the automated assembly lines."
    filler_p2 = "Note that environmental monitoring should be maintained continuously to log temperature and humidity variations inside the device cabinet. If environmental parameters exceed the specified limits, supplementary heating or cooling systems must be installed immediately to maintain system integrity."
    
    body = "\n\n".join([prob_part, symptom_part, root_part, res_part, ver_part, ref_part, filler_p1, filler_p2])
    
    # Verify word count and adjust if necessary
    word_count = len(body.split())
    if word_count < 300:
        body += f"\n\nAdditional operational notes: To ensure complete compliance with international standards, keep a written log of all servicing activities, including date, technician ID, and the exact serial numbers of any components replaced during the {product} unit overhaul. Regular inspection intervals should be scheduled every 6 months under light loads, or quarterly under extreme operating environments containing abrasive dust or corrosive chemical vapors."
    elif word_count > 600:
        # Truncate some filler if it's somehow too long (unlikely with this setup)
        words = body.split()
        body = " ".join(words[:550])
        
    return body

def main():
    articles = []
    
    # Build assignment lists
    product_assignments = []
    for product, info in PRODUCTS.items():
        product_assignments.extend([product] * info["count"])
    random.shuffle(product_assignments)
    
    source_assignments = []
    for source, count in SOURCES.items():
        source_assignments.extend([source] * count)
    random.shuffle(source_assignments)
    
    # We want exactly 120 articles to have error codes, and 80 to be null.
    error_mask = [True] * 120 + [False] * 80
    random.shuffle(error_mask)
    
    # Assign error codes deterministically to the 120 slots
    # To keep error codes appearing 1-3 times, we will create a pool of unique error codes
    # For 120 articles, if each appears 1.5 times on average, we need about 80 unique codes
    error_pools = {
        "server": ["E101", "E102", "E103", "E115", "E120", "E145", "E180", "E201", "E205", "E210", "E220", "E250", "E280", "E299"],
        "actuator": ["E105", "E110", "E130", "E150", "E190", "E230", "E240", "E260", "E270", "E290"],
        "sensor": ["E112", "E118", "E125", "E135", "E155", "E160", "E170", "E215", "E225", "E245", "E255", "E275"],
        "router": ["E301", "E302", "E305", "E310", "E320", "E350", "E380", "E401", "E410", "E420", "E450", "E480", "E499"],
        "switch": ["E303", "E315", "E325", "E340", "E360", "E405", "E415", "E425", "E430", "E460", "E470", "E490"],
        "gateway": ["E308", "E330", "E370", "E390", "E435", "E440", "E445", "E455", "E465", "E475", "E485"],
        "controller": ["E501", "E505", "E510", "E550", "E601", "E610", "E620", "E680", "E701", "E710", "E720", "E750", "E801", "E850", "E880"],
    }
    
    # Keep track of error code usages (to ensure 1-3 times usage)
    error_usage_counts = {}
    
    article_id = 1
    for product, source, has_error in zip(product_assignments, source_assignments, error_mask):
        error_code = None
        if has_error:
            # Select an error code for this product type
            possible_codes = error_pools.get(product, ["E901", "E902", "E905", "E910", "E920", "E950", "E980", "E999"])
            # Filter codes that have been used < 3 times
            available_codes = [c for c in possible_codes if error_usage_counts.get(c, 0) < 3]
            if not available_codes:
                available_codes = possible_codes
            
            error_code = random.choice(available_codes)
            error_usage_counts[error_code] = error_usage_counts.get(error_code, 0) + 1
            
        terms = PRODUCTS[product]["terms"]
        random.shuffle(terms)
        
        title = build_title(product, source, error_code, terms)
        body = build_body(product, source, error_code, terms)
        
        article = {
            "id": f"article_{article_id:03d}",
            "title": title,
            "body": body,
            "metadata": {
                "source": source,
                "error_code": error_code,
                "product": product,
            },
        }
        articles.append(article)
        article_id += 1
        
    # Validation checks
    assert len(articles) == 200, f"Expected 200 articles, got {len(articles)}"
    
    ids = [a["id"] for a in articles]
    assert len(set(ids)) == 200, "Duplicate article IDs found"
    
    for a in articles:
        wc = len(a["body"].split())
        assert wc >= 300, f"{a['id']} body too short: {wc} words"
        assert wc <= 600, f"{a['id']} body too long: {wc} words"
        assert a["metadata"]["source"] in SOURCES
        assert a["metadata"]["product"] in PRODUCTS
        if a["metadata"]["error_code"]:
            assert re.match(r"^E\d{3}$", a["metadata"]["error_code"]), f"Invalid error code format: {a['metadata']['error_code']}"
            
    # Check distributions
    source_counts = Counter(a["metadata"]["source"] for a in articles)
    product_counts = Counter(a["metadata"]["product"] for a in articles)
    error_count = sum(1 for a in articles if a["metadata"]["error_code"])
    
    print(f"Generated {len(articles)} articles.")
    print(f"Sources: {dict(source_counts)}")
    print(f"Products: {dict(product_counts)}")
    print(f"Articles with error codes: {error_count}/200")
    
    # Save to data/articles.json (root directory) and backend/data/articles.json
    os.makedirs("data", exist_ok=True)
    os.makedirs("backend/data", exist_ok=True)
    
    with open("data/articles.json", "w") as f:
        json.dump(articles, f, indent=2)
        
    with open("backend/data/articles.json", "w") as f:
        json.dump(articles, f, indent=2)
        
    print("Saved articles to data/articles.json and backend/data/articles.json")

if __name__ == "__main__":
    main()
