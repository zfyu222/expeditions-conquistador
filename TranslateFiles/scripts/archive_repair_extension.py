"""Archive only this turn's explicitly authorized shared-tool changes."""
import difflib
from pathlib import Path

folder = Path(r'D:\StaticHanHua\Tools\localization')
flow = (folder / 'translation_workflow.py').read_text(encoding='utf-8')
quality = (folder / 'workflow_quality.py').read_text(encoding='utf-8')
start = flow.index("            if stage.startswith('pilot_'):\n                limit = config.get('pilot_call_limit', 6)", flow.index('    def claim('))
end = flow.index("            if json.loads(task['payload']).get('context'):", start)
before_flow = flow[:start] + (
    "            if stage.startswith('pilot_') and self.pilot_spent(db) + (1 if stage == 'pilot_translate' else 0) >= config.get('pilot_call_limit', 6):\n"
    "                raise ValueError('Pilot execution budget exhausted; stop spawning agents and let Sol inspect existing results')\n"
) + flow[end:]
start = quality.index('    def pilot_claim_limit(')
end = quality.index('    def pilot_spent(', start)
before_quality = quality[:start] + quality[end:]
start = before_quality.index("            grant = self.meta(db, 'pilot_repair_grant', {})", before_quality.index('    def pilot_plan('))
end = before_quality.index("            return {'sample_records'", start)
before_quality = before_quality[:start] + before_quality[end:]
before_quality = before_quality.replace(
    'No agent spawned; all claims/retries count across revisions. Explicit repair grant, if present, applies only to its tasks.',
    'No agent spawned; all claims/retries after policy activation count across revisions.')
before_quality = before_quality.replace(
    "            approved = self.pilot_approved(db, config)\n"
    "            untranslated = [] if approved else [r for r in scope if r['stage'] not in ('pilot_translate', 'pilot_review')]\n"
    "            unreviewed = [] if approved else [r for r in scope if r['stage'] != 'pilot_review']\n",
    "            untranslated = [r for r in scope if r['stage'] not in ('pilot_translate', 'pilot_review')]\n"
    "            unreviewed = [r for r in scope if r['stage'] != 'pilot_review']\n")
patch = ''
for name, old, new in [('translation_workflow.py', before_flow, flow), ('workflow_quality.py', before_quality, quality)]:
    patch += ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile='a/Tools/localization/'+name, tofile='b/Tools/localization/'+name))
Path(__file__).with_name('pilot_scoped_repair_tool.patch').write_text(patch, encoding='utf-8')
print('Archived authorized budget guard patch; no runtime mutation.')
