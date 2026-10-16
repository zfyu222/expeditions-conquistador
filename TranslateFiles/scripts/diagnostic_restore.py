"""Collect all protected-token errors without weakening submission validation."""
import re


def diagnostic_restore(value, mapping):
    issues = []
    known = {item['placeholder'] for item in mapping}
    for item in mapping:
        count = value.count(item['placeholder'])
        if count != 1:
            issues.append({'token': item['placeholder'], 'expected': 1, 'actual': count})
    for token in set(re.findall(r'⟪SHH_[^⟫]*⟫', value)) - known:
        issues.append({'token': token, 'expected': 0, 'actual': value.count(token)})
    # Partial restoration is for collecting other diagnostics only; never submitted.
    restored = value
    for item in mapping:
        restored = restored.replace(item['placeholder'], item['original'])
    return restored, issues
