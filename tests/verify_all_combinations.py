import os
import sys
import json
import itertools
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# 1. Setup Environment Variables BEFORE imports to ensure proper config loading
os.environ["CEREBRAS_API_KEY"] = "mock-key-for-testing"
os.environ["CHROMA_PERSIST_PATH"] = "data/chroma_db"
os.environ["HF_HOME"] = "data/huggingface"

# Ensure root of project is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.api.routes import limiter

# 2. Disable Rate Limiting for Testing
limiter.enabled = False

# 3. Create Async Generator Mock for LLM streaming
async def mock_stream_completion(*args, **kwargs):
    yield "According "
    yield "to "
    yield "the "
    yield "retrieved "
    yield "context, "
    yield "the "
    yield "switch "
    yield "spanning "
    yield "tree "
    yield "is "
    yield "active."

@patch("backend.services.llm.LLMClient.stream_completion", side_effect=mock_stream_completion)
def run_combinations_sweep(mock_llm):
    print("=== Starting Exhaustive Sweep of All 256 Feature Combinations ===")
    
    # 7 Toggles
    feature_keys = [
        "hybrid",
        "remote_embed",
        "query_understanding",
        "metadata_aware",
        "multi_index",
        "hnsw",
        "stream_sources"
    ]
    
    # Generate all 2^7 = 128 toggle combinations
    combinations = list(itertools.product([False, True], repeat=len(feature_keys)))
    
    # We will test each combination with compare_with_baseline = True and False (total 256)
    compare_options = [False, True]
    
    total_runs = len(combinations) * len(compare_options)
    print(f"Total test cases to execute: {total_runs}")
    
    failures = 0
    passed = 0
    
    # Use TestClient with lifespan context manager to load embedding models and Chroma DB once
    with TestClient(app) as client:
        print("TestClient and lifespan services initialized successfully.")
        
        for idx, (toggle_values, compare) in enumerate(itertools.product(combinations, compare_options), 1):
            features = dict(zip(feature_keys, toggle_values))
            
            # Formulate query
            # We use a query that contains metadata terms (switch, E415) to trigger metadata filter extraction
            query = "What is error code E415 on the switch?"
            
            payload = {
                "query": query,
                "features": features,
                "compare_with_baseline": compare
            }
            
            try:
                response = client.post("/query", json=payload)
                
                if response.status_code != 200:
                    print(f"[{idx}/{total_runs}] FAILED: HTTP {response.status_code} for features={features}, compare={compare}")
                    failures += 1
                    continue
                
                # Parse SSE events from response
                lines = response.text.split("\n")
                events = []
                current_event = None
                for line in lines:
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:") and current_event:
                        try:
                            data_json = json.loads(line.split(":", 1)[1].strip())
                            events.append((current_event, data_json))
                        except json.JSONDecodeError:
                            pass
                        current_event = None
                
                event_types = [e[0] for e in events]
                
                # Verify standard events
                required_events = ["classification", "sources", "token", "metrics", "logs", "done"]
                missing = [req for req in required_events if req not in event_types]
                
                if missing:
                    print(f"[{idx}/{total_runs}] FAILED: Missing events {missing} for features={features}, compare={compare}")
                    failures += 1
                    continue
                
                # Verify baseline events when comparison is enabled
                if compare:
                    if "baseline_sources" not in event_types or "baseline_metrics" not in event_types:
                        print(f"[{idx}/{total_runs}] FAILED: Missing baseline events in comparison mode. features={features}")
                        failures += 1
                        continue
                else:
                    if "baseline_sources" in event_types or "baseline_metrics" in event_types:
                        print(f"[{idx}/{total_runs}] FAILED: Unexpected baseline events when comparison is disabled. features={features}")
                        failures += 1
                        continue
                
                passed += 1
                if idx % 20 == 0 or idx == total_runs:
                    print(f"Progress: Completed {idx}/{total_runs} test cases... (Passed: {passed}, Failed: {failures})")
                    
            except Exception as e:
                print(f"[{idx}/{total_runs}] CRASHED: {e} for features={features}, compare={compare}")
                failures += 1
                
    print("\n=== Sweep Results ===")
    print(f"Total executed: {total_runs}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    
    if failures > 0:
        print("❌ Sweeper sweep completed with errors.")
        sys.exit(1)
    else:
        print("✅ ALL 256 toggle combinations and baseline comparison combinations PASSED successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_combinations_sweep()
