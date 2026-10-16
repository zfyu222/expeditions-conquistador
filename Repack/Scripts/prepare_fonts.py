"""Download pinned OFL fonts and build static, renamed Chinese subsets."""
import csv
import hashlib
import json
import urllib.request
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT.parents[1] / 'Tools/Fonts/NotoSC'
OUT = ROOT / 'Repack/Build/fonts'
LICENSES = ROOT / 'Repack/Licenses'
COMMIT = '1d0e46c7933245c8180fe83e47917961c913bbdb'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def download(url, dest):
    if dest.is_file():
        return
    print('download', dest.name, flush=True)
    with urllib.request.urlopen(url, timeout=120) as src, dest.open('wb') as dst:
        while data := src.read(1024 * 1024):
            dst.write(data)

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    LICENSES.mkdir(parents=True, exist_ok=True)
    chars = set(chr(i) for i in range(32, 127))
    for name in ['expeditions-conquistador_text.csv', 'expeditions-conquistador_text_translated.csv']:
        with (ROOT / name).open(encoding='utf-8-sig', newline='') as f:
            for row in csv.reader(f):
                chars.update(row[0])
    chars.update('\u3000\u200b\u2014\u2026\u00a0')
    supplement=ROOT/'TranslateFiles/tutorial_supplement/tutorial_captions_reviewed.json'
    if supplement.exists():
        for entry in json.loads(supplement.read_text('utf-8')): chars.update(entry['translation'])
    required = {ord(c) for c in chars if not c.isspace() or c==' '}
    report = {'source_commit': COMMIT, 'required_characters': len(required), 'fonts': []}
    for family in ['NotoSerifSC', 'NotoSansSC']:
        folder = family.lower()
        url = f'https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl/{folder}/'
        source = CACHE / (family + '-variable.ttf')
        download(url + family + '%5Bwght%5D.ttf', source)
        license_path = LICENSES / (family + '-OFL.txt')
        download(url + 'OFL.txt', license_path)
        for weight, style in [(400, 'Regular'), (700, 'Bold')]:
            path = OUT / f'ZFY{family}-{style}.ttf'
            rebuild=not path.is_file()
            if not rebuild:
                existing=TTFont(path)
                rebuild=not required.issubset(existing.getBestCmap())
                existing.close()
            if rebuild:
                print('instantiate/subset', family, style, flush=True)
                font = instantiateVariableFont(TTFont(source), {'wght': weight}, inplace=True)
                options = subset.Options()
                options.layout_features = ['*']
                options.name_IDs = ['*']
                sub = subset.Subsetter(options=options)
                sub.populate(unicodes=required)
                sub.subset(font)
                new_name = 'ZFY Conquistador ' + ('Serif' if 'Serif' in family else 'Sans')
                for record in font['name'].names:
                    values = {1: new_name, 2: style, 3: new_name + '-' + style,
                              4: new_name + ' ' + style, 6: new_name.replace(' ', '') + '-' + style,
                              16: new_name, 17: style}
                    if record.nameID in values:
                        record.string = values[record.nameID].encode(record.getEncoding(), errors='replace')
                font.save(path)
                font.close()
            font = TTFont(path)
            missing = sorted(required - set(font.getBestCmap()))
            # Formatting controls and original decorative characters are not glyph requirements.
            missing = [n for n in missing if n not in (0x200b, 0xfeff, 0xad)]
            if missing:
                raise ValueError(f'{path.name}: missing {missing}')
            assert 'fvar' not in font and 'glyf' in font
            report['fonts'].append({'file': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                'size': path.stat().st_size, 'source_url': url + family + '%5Bwght%5D.ttf',
                'source_sha256': sha(source), 'weight': weight, 'missing_characters': missing})
            font.close()
            print('ready', path.name, path.stat().st_size, flush=True)
    (ROOT / 'Repack/reports/font_build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
