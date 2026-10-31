import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# isolate test data + force offline mode (deterministic, no network)
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="pp_test_")
os.environ["GROQ_API_KEY"] = ""
os.environ["EMBEDDING_BACKEND"] = "hash"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"
