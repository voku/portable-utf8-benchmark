#!/usr/bin/env python3
"""Actual locked no-dev Composer Dist/Source consumers, including full vendor trees."""
import argparse, json, os, pathlib, subprocess, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', type=pathlib.Path, default=pathlib.Path('/workspace'))
parser.add_argument('--output', type=pathlib.Path, required=True)
parser.add_argument('--composer', default='composer')
parser.add_argument('--php', default='php')
args = parser.parse_args()
base, output = args.workspace.resolve(), args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
baselines = {'portable-ascii': '180a8d12055eb350859b628c64066a90a895bd10', 'portable-utf8': '28cb685c22cd829aba819406295c0763204c5c09'}


def run(command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def footprint(root):
    logical = allocated = files = 0
    for directory, dirs, names in os.walk(root):
        for name in names:
            path = pathlib.Path(directory) / name
            if not path.is_symlink():
                stat = path.stat()
                logical += stat.st_size
                allocated += stat.st_blocks * 512
                files += 1
    return {'logical_bytes': logical, 'allocated_bytes': allocated, 'files': files}


# Pin all production dependencies from the already resolved checkout lock.
production = json.loads((base / 'portable-utf8/composer.lock').read_text())['packages']
rows = []
for phase in ['before', 'after']:
    packages = []
    versions = {'voku/portable-ascii': '2.1.99', 'voku/portable-utf8': '6.1.99'}
    refs = {}
    zips = {}
    for repo in ['portable-ascii', 'portable-utf8']:
        root = base / repo
        ref = baselines[repo] if phase == 'before' else run(['git', '-C', str(root), 'rev-parse', 'HEAD'])
        refs[repo] = ref
        archive = output / f'{repo}-{phase}.zip'
        subprocess.run(['git', '-C', str(root), 'archive', '--format=zip', '--prefix=package/', '--output', str(archive), ref], check=True)
        zips[repo] = archive.stat().st_size
        manifest = json.loads(run(['git', '-C', str(root), 'show', ref + ':composer.json']))
        package = {key: manifest[key] for key in ['name', 'require', 'autoload']}
        package.update(version=versions[manifest['name']], dist={'type': 'zip', 'url': archive.as_uri(), 'reference': ref}, source={'type': 'git', 'url': str(root), 'reference': ref})
        packages.append(package)
    for dependency in production:
        if dependency['name'] == 'voku/portable-ascii':
            continue
        package = {key: dependency[key] for key in ['name', 'version', 'require', 'autoload', 'dist', 'source'] if key in dependency}
        dist = package.get('dist', {})
        url = dist.get('url', '')
        if url.startswith('https://api.github.com/repos/') and '/zipball/' in url:
            repo, sha = url[len('https://api.github.com/repos/'):].split('/zipball/')
            dist['url'] = f'https://codeload.github.com/{repo}/legacy.zip/{sha}'
        packages.append(package)
    repository = {'type': 'package', 'package': packages}
    for target in ['ascii', 'utf8']:
        requirement = 'voku/portable-' + target
        manifest = {'name': 'footprint/consumer', 'require': {requirement: versions[requirement]}, 'repositories': [repository, {'packagist.org': False}], 'config': {'allow-plugins': False}}
        lock_root = output / f'{target}-{phase}-locked'
        lock_root.mkdir(exist_ok=True)
        (lock_root / 'composer.json').write_text(json.dumps(manifest, indent=2) + '\n')
        with (lock_root / 'resolve.log').open('w') as log:
            subprocess.run([args.composer, 'update', '--no-install', '--no-dev', '--no-interaction'], cwd=lock_root, stdout=log, stderr=subprocess.STDOUT, check=True)
        for preference in ['dist', 'source']:
            consumer = output / f'{target}-{phase}-{preference}'
            consumer.mkdir(exist_ok=True)
            for name in ['composer.json', 'composer.lock']:
                (consumer / name).write_bytes((lock_root / name).read_bytes())
            # An existing vendor directory must not turn a requested Source install into Dist.
            if (consumer / 'vendor').exists():
                raise RuntimeError(f'{consumer}/vendor already exists: use a fresh output directory')
            with (consumer / 'install.log').open('w') as log:
                subprocess.run([args.composer, 'install', '--no-dev', '--no-interaction', '--prefer-' + preference], cwd=consumer, stdout=log, stderr=subprocess.STDOUT, check=True)
            smoke = '''require 'vendor/autoload.php'; if (\\voku\\helper\\ASCII::to_ascii('Düsseldorf','de') !== 'Duesseldorf' || \\voku\\helper\\ASCII::to_transliterate('中文空白','?',false) !== 'Zhong Wen Kong Bai ') {exit(1);}'''
            if target == 'utf8':
                smoke += '''if (\\voku\\helper\\UTF8::chr(0x2603) !== '☃' || \\voku\\helper\\UTF8::ord('☃') !== 0x2603 || \\voku\\helper\\UTF8::emoji_decode('CHARACTER_OGRE') !== '👹') {exit(2);}'''
            subprocess.run([args.php, '-r', smoke], cwd=consumer, check=True)
            installed = json.loads((consumer / 'vendor/composer/installed.json').read_text())['packages']
            methods = {p['name']: p.get('installation-source') for p in installed}
            if any(method != preference for method in methods.values()):
                raise RuntimeError(f'Requested {preference}, actual methods: {methods}')
            row = {'phase': phase, 'target': target, 'preference': preference, 'refs': refs, 'vendor': footprint(consumer / 'vendor'), 'packages': {p['name']: {'version': p['version'], 'reference': p.get('source', {}).get('reference'), 'installation_source': p.get('installation-source')} for p in installed}, 'library': footprint(consumer / ('vendor/voku/portable-' + target)), 'library_zip_bytes': zips['portable-' + target]}
            rows.append(row)
            print(phase, target, preference, row['vendor'], flush=True)
(output / 'measurements.json').write_text(json.dumps({'php': run([args.php, '-v']), 'extensions': run([args.php, '-m']), 'composer': run([args.composer, '--version']), 'note': '2.1.99/6.1.99 are temporary consumer aliases, never published requirements. Git archives honor existing export-ignore rules. Source includes Git metadata/tests. Dependencies are pinned to exact lock versions/references. Allocated bytes depend on filesystem.', 'rows': rows}, indent=2) + '\n')
