"""Query OSV using resolved Maven, npm, and hosted Dart dependency versions.

Run Maven dependency:list with -DoutputFile=target/security-dependencies.txt first.
Only public package names and versions are sent to OSV; no source or credentials.
"""
import json
from pathlib import Path
import re
import urllib.request

root = Path(__file__).resolve().parents[2]
queries = []
maven = root / 'vikoba/target/security-dependencies.txt'
if maven.exists():
    for line in maven.read_text().splitlines():
        match = re.match(r'\s+([^: ]+):([^: ]+):jar:([^: ]+):(compile|runtime)', line)
        if match:
            queries.append({'package': {'ecosystem': 'Maven', 'name': f'{match[1]}:{match[2]}'}, 'version': match[3]})

lock = json.loads((root / 'vikoba-web/package-lock.json').read_text())
for path, package in lock['packages'].items():
    if 'node_modules/' not in path or 'version' not in package:
        continue
    queries.append({'package': {'ecosystem': 'npm', 'name': path.rsplit('node_modules/', 1)[1]}, 'version': package['version']})

text = (root / 'vikoba_app/pubspec.lock').read_text()
for match in re.finditer(r'^  ([\w]+):\n((?:    .*\n|      .*\n)+)', text, re.M):
    body = match[2]
    version = re.search(r'    version: "([^"]+)"', body)
    if '    source: hosted' in body and version:
        queries.append({'package': {'ecosystem': 'Pub', 'name': match[1]}, 'version': version[1]})

queries = list({json.dumps(q, sort_keys=True): q for q in queries}.values())
findings = []
for start in range(0, len(queries), 200):
    batch = queries[start:start + 200]
    request = urllib.request.Request('https://api.osv.dev/v1/querybatch',
            data=json.dumps({'queries': batch}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        results = json.load(response)['results']
    for query, result in zip(batch, results):
        if result.get('vulns'):
            findings.append({**query, 'vulnerabilities': result['vulns']})

# These npm advisories model every xlsx version as affected because patched
# releases are distributed outside npm. Keep the raw match as triaged evidence.
# Publisher guidance: https://docs.sheetjs.com/docs/getting-started/installation/nodejs/
triaged = []
for finding in findings:
    if (finding['package'] == {'ecosystem': 'npm', 'name': 'xlsx'}
            and tuple(map(int, finding['version'].split('.'))) >= (0, 20, 3)
            and lock['packages']['node_modules/xlsx'].get('resolved', '').startswith('file:vendor/xlsx-')
            and {v['id'] for v in finding['vulnerabilities']}
                <= {'GHSA-4r6h-8v6p-xvw6', 'GHSA-5pgg-2g8v-p4x9'}):
        triaged.append({**finding, 'reason': 'Publisher fixes are included in vendored SheetJS >= 0.20.3; npm advisory ranges have no fixed release.'})
findings = [f for f in findings if not any(f['package'] == t['package'] for t in triaged)]
output = root / 'security-dependency-audit.json'
output.write_text(json.dumps({'packages_checked': len(queries), 'findings': findings, 'triaged': triaged}, indent=2) + '\n')
print(f'Checked {len(queries)} dependency versions. {len(findings)} packages have OSV findings.')
for finding in findings:
    print(f"{finding['package']['ecosystem']} {finding['package']['name']} {finding['version']}: "
          + ', '.join(v['id'] for v in finding['vulnerabilities']))
print(f'{len(triaged)} publisher-patched package matches are recorded separately for review.')
