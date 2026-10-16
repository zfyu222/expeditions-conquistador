"""Project-local entry for event-driven batch handoffs; keeps existing state."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'Tools' / 'localization'))
from translation_workflow import main

if __name__ == '__main__':
    project = Path(__file__).resolve().parents[2]
    sys.argv[1:1] = ['--project', str(project)]
    raise SystemExit(main())
