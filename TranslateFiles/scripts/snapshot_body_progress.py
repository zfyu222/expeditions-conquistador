"""Save factual execution progress; never marks drafts as semantically approved."""
import difflib
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, write_json

project = Path(__file__).resolve().parents[2]
flow = Workflow(project)
status = flow.status()
with flow.db() as db:
    source_hash = flow.meta(db, 'source_hash')
    glossary = flow.meta(db, 'glossary')
report = {
    'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'revision': status['revision'], 'source_sha256': source_hash, 'glossary': glossary,
    'quality': status['quality'], 'records': status['records'],
    'production_tasks': [t for t in status['tasks'] if t['stage'] in ('translate','review','polish','final_review')],
    'attention': status['attention'],
    'note': 'translate counts are saved drafts, not full semantic approval; no formal CSV export or repack yet.',
}
write_json(flow.root / 'reports/body_execution_progress.json', report)
# Archive this narrow shared-tool fix, keeping source matching/protection unchanged.
path = Path(r'D:\StaticHanHua\Tools\localization\ainiee_bridge.py')
current = path.read_text(encoding='utf-8')
start = current.index('        originals = Counter', current.index('def structural_issues('))
end = current.index("            issues.append(name)", start)
before = current[:start] + (
    '        if Counter(m.group(0) for m in pattern.finditer(source)) != Counter(\n'
    '                m.group(0) for m in pattern.finditer(translation)):\n'
) + current[end:]
patch = ''.join(difflib.unified_diff(before.splitlines(True), current.splitlines(True),
    fromfile='a/Tools/localization/ainiee_bridge.py', tofile='b/Tools/localization/ainiee_bridge.py'))
(flow.root / 'scripts/identifier_boundary_fix.patch').write_text(patch, encoding='utf-8')
begin = current.index('def normalize_exception_sources(')
end = current.index('def structural_issues(', begin)
old_bridge = current[:begin] + current[end:]
workflow_path = Path(r'D:\StaticHanHua\Tools\localization\translation_workflow.py')
workflow = workflow_path.read_text(encoding='utf-8')
old_workflow = workflow.replace("                    exceptions = bridge.normalize_exception_sources(exceptions, terms, config['case_sensitive'])\n", '')
case_patch = ''.join(difflib.unified_diff(old_bridge.splitlines(True), current.splitlines(True),
    fromfile='a/Tools/localization/ainiee_bridge.py', tofile='b/Tools/localization/ainiee_bridge.py'))
case_patch += ''.join(difflib.unified_diff(old_workflow.splitlines(True), workflow.splitlines(True),
    fromfile='a/Tools/localization/translation_workflow.py', tofile='b/Tools/localization/translation_workflow.py'))
(flow.root / 'scripts/exception_key_case_fix.patch').write_text(case_patch, encoding='utf-8')
begin = current.index('    # Reuse literal/quote/boundary/overlap matching, but frozen rows are authoritative.')
end = current.index('                                    case_sensitive=', begin)
old_matcher = current[:begin] + '    matched = h.collect_matched_rows(rows, {str(i): t for i, t in enumerate(texts)},\n' + current[end:]
matcher_patch = ''.join(difflib.unified_diff(old_matcher.splitlines(True), current.splitlines(True),
    fromfile='a/Tools/localization/ainiee_bridge.py', tofile='b/Tools/localization/ainiee_bridge.py'))
(flow.root / 'scripts/frozen_matcher_fix.patch').write_text(matcher_patch, encoding='utf-8')
report['frozen_matcher_fix'] = {
    'scope': 'Preserve each frozen row translation; pending input packages refreshed without resetting attempts or drafts.',
    'refresh_report': 'frozen_matcher_refresh.json',
    'completed_drafts': 'Retained for the required full independent review after translation completes.',
}
report['validator_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
write_json(flow.root / 'reports/body_execution_progress.json', report)
print(json.dumps({'records': status['records'], 'production_tasks': report['production_tasks']},ensure_ascii=False))
