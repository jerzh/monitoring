"""Git clean filter: strip outputs and execution counts from a notebook on stdin.

Keeps MALT transcript text out of the repo while the local notebook keeps its outputs.
Enable in a fresh clone with:
    git config filter.nbstrip.clean "python3 scripts/strip_nb_outputs.py"
    git config filter.nbstrip.smudge cat
"""

import json
import sys

nb = json.load(sys.stdin)
for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        cell["outputs"] = []
        cell["execution_count"] = None
nb.get("metadata", {}).pop("widgets", None)
json.dump(nb, sys.stdout, indent=1, ensure_ascii=False)
sys.stdout.write("\n")
