#!/usr/bin/env python3
"""S8 isolated mandatory-package prototype. Never edits a production manifest."""
import argparse, json, os, pathlib, subprocess, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--consumers', type=pathlib.Path, required=True)
parser.add_argument('--output', type=pathlib.Path, required=True)
parser.add_argument('--composer', default='composer')
parser.add_argument('--php', default='php')
args = parser.parse_args()
args.output = args.output.resolve()
args.output.mkdir(parents=True, exist_ok=True)


def footprint(root):
    values = {'logical_bytes': 0, 'allocated_bytes': 0, 'files': 0}
    for directory, _, names in os.walk(root):
        for name in names:
            path = pathlib.Path(directory) / name
            if not path.is_symlink():
                stat = path.stat()
                values['logical_bytes'] += stat.st_size
                values['allocated_bytes'] += stat.st_blocks * 512
                values['files'] += 1
    return values


original = json.loads((args.consumers / 'utf8-after-dist/composer.json').read_text())
packages = original['repositories'][0]['package']
for library, child in [('ascii', 'portable-ascii-mappings'), ('utf8', 'portable-utf8-emoji')]:
    package = next(p for p in packages if p['name'] == 'voku/portable-' + library)
    source = args.consumers / f'portable-{library}-after.zip'
    core_zip = args.output / f'portable-{library}-core.zip'
    child_zip = args.output / (child + '.zip')
    child_manifest = {'name': 'voku/' + child, 'version': '1.0.0', 'require': {'php': '>=7.1'}}
    moved = 0
    with zipfile.ZipFile(source) as archived, zipfile.ZipFile(core_zip, 'w', compression=zipfile.ZIP_DEFLATED) as core, zipfile.ZipFile(child_zip, 'w', compression=zipfile.ZIP_DEFLATED) as child_archive:
        child_archive.writestr('package/composer.json', json.dumps(child_manifest, indent=2) + '\n')
        for name in archived.namelist():
            if name.endswith('/'):
                continue
            contents = archived.read(name)
            filename = pathlib.PurePosixPath(name).name
            mapping = '/src/voku/helper/data/' in name and ((library == 'ascii' and filename.startswith('x') and filename.endswith('.php')) or (library == 'utf8' and filename == 'emoji.php'))
            if mapping:
                child_archive.writestr('package/data/' + filename, contents)
                moved += len(contents)
                continue
            if filename == 'composer.json':
                manifest = json.loads(contents)
                manifest['require']['voku/' + child] = '1.0.0'
                contents = (json.dumps(manifest, indent=2) + '\n').encode()
            if name.endswith('/' + ('ASCII' if library == 'ascii' else 'UTF8') + '.php'):
                text = contents.decode()
                if library == 'ascii':
                    old = "$file = __DIR__ . '/data/' . $file . '.php';"
                    replacement = "$file = \\dirname(__DIR__, 5) . '/voku/portable-ascii-mappings/data/' . $file . '.php';"
                else:
                    old = "return include __DIR__ . '/data/' . $file . '.php';"
                    replacement = "return include ($file === 'emoji' ? \\dirname(__DIR__, 5) . '/voku/portable-utf8-emoji/data/emoji.php' : __DIR__ . '/data/' . $file . '.php');"
                if text.count(old) != 1:
                    raise RuntimeError('Unexpected loader anchor')
                contents = text.replace(old, replacement).encode()
            core.writestr(name, contents)
    package['require']['voku/' + child] = '1.0.0'
    package['dist']['url'] = core_zip.as_uri()
    # This experiment is deliberately Dist-only; a Source publisher would add Git overhead.
    package.pop('source', None)
    child_manifest['dist'] = {'type': 'zip', 'url': child_zip.as_uri()}
    packages.append(child_manifest)
    print(library, 'mapping logical bytes merely relocated:', moved, flush=True)
(args.output / 'composer.json').write_text(json.dumps(original, indent=2) + '\n')
with (args.output / 'install.log').open('w') as log:
    subprocess.run([args.composer, 'update', '--no-dev', '--no-interaction', '--prefer-dist'], cwd=args.output, stdout=log, stderr=subprocess.STDOUT, check=True)
smoke = '''require 'vendor/autoload.php'; if (\\voku\\helper\\ASCII::to_transliterate('中文空白','?',false) !== 'Zhong Wen Kong Bai ' || \\voku\\helper\\UTF8::emoji_decode('CHARACTER_OGRE') !== '👹') {exit(1);}'''
subprocess.run([args.php, '-r', smoke], cwd=args.output, check=True)
result = {'candidate_vendor': footprint(args.consumers / 'utf8-after-dist/vendor'), 'mandatory_split_vendor': footprint(args.output / 'vendor'), 'decision': 'NO-GO: mandatory extraction moves mappings and adds overhead; intl cannot replace non-strict data.', 'scope': 'Dist prototype with unchanged data, required child packages, matching public consumer smoke. This is a local experimental package boundary, not an approved or published package.'}
(args.output / 'split-results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
