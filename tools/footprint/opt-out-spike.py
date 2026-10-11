#!/usr/bin/env python3
"""S8 follow-up: real Composer consumers, explicit replace and lazy providers in scratch only."""
import argparse
import copy
import hashlib
import itertools
import json
import os
import pathlib
import shutil
import subprocess
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
EMOJI = 'voku/portable-utf8-emoji-data'
BANKS = 'voku/portable-ascii-mapping-data'
VERSION = '1.0.0'
CASES = ['ascii-pass', 'language-map', 'utf8-length', 'utf8-repair', 'utf8-ord',
         'support-key', 'support-full', 'html-empty', 'emoji-encode', 'emoji-decode',
         'reverse-ascii', 'reverse-unicode', 'html-ascii', 'banks-direct',
         'banks-strict', 'utf8-ascii', 'ascii-filename', 'utf8-filename', 'utf8-filename-default', 'unmapped-bank']
EMOJI_CASES = {'emoji-encode', 'emoji-decode', 'reverse-ascii', 'reverse-unicode', 'html-ascii'}
BANK_CASES = {'banks-direct', 'utf8-ascii', 'ascii-filename', 'utf8-filename', 'unmapped-bank'}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def footprint(root):
    result = {'logical_bytes': 0, 'allocated_bytes': 0, 'files': 0}
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            result['logical_bytes'] += stat.st_size
            result['allocated_bytes'] += stat.st_blocks * 512
            result['files'] += 1
    return result


def tree_hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*')) if path.is_file() and not path.is_symlink()}


def write_zip(path, files):
    # Stable timestamps and permissions make the local archives reproducible.
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, value)
    return {'type': 'zip', 'url': path.as_uri(),
            'reference': hashlib.sha256(path.read_bytes()).hexdigest(),
            'shasum': hashlib.sha1(path.read_bytes()).hexdigest()}


def message(package):
    return ('Mappings are unavailable. Install ' + package + ' and remove its replacement '
            'declaration from your root composer.json.')


def provider(library):
    namespace = 'PortableUtf8EmojiData' if library == 'utf8' else 'PortableAsciiMappingData'
    cls = 'EmojiMap' if library == 'utf8' else 'BankMap'
    load = "return include __DIR__ . '/../data/emoji.php';" if library == 'utf8' else """$path = __DIR__ . '/../data/' . $bank . '.php';
        return \\is_file($path) ? include $path : [];"""
    argument = '' if library == 'utf8' else 'string $bank'
    return (f'<?php\n\nnamespace Voku\\{namespace};\n\nfinal class {cls}\n{{\n'
            f'    public static function load({argument}): array\n    {{\n        {load}\n    }}\n}}\n').encode()


def archives(args, original):
    packages = original['repositories'][0]['package']
    archives_evidence = []
    locked = {p['name']: p for p in json.loads((args.consumers / 'utf8-after-dist/composer.lock').read_text())['packages']}
    for library, name in [('ascii', BANKS), ('utf8', EMOJI)]:
        package = next(p for p in packages if p['name'] == 'voku/portable-' + library)
        source = args.consumers / ('portable-' + library + '-after.zip')
        child = {'name': name, 'version': VERSION, 'require': {'php': '>=7.1'},
                 'autoload': {'psr-4': {'Voku\\' + ('PortableUtf8EmojiData' if library == 'utf8' else 'PortableAsciiMappingData') + '\\': 'src/'}}}
        child_files = {'package/composer.json': json.dumps(child, indent=2).encode() + b'\n',
                       'package/src/' + ('EmojiMap' if library == 'utf8' else 'BankMap') + '.php': provider(library)}
        core_files = {}
        moved = 0
        with zipfile.ZipFile(source) as archive:
            for entry in archive.namelist():
                if entry.endswith('/'):
                    continue
                contents = archive.read(entry)
                filename = pathlib.PurePosixPath(entry).name
                mapping = '/src/voku/helper/data/' in entry and ((library == 'ascii' and filename.startswith('x') and filename.endswith('.php')) or (library == 'utf8' and filename == 'emoji.php'))
                if mapping:
                    child_files['package/data/' + filename] = contents
                    moved += len(contents)
                    continue
                if filename == 'composer.json':
                    manifest = json.loads(contents)
                    manifest['require'][name] = VERSION
                    contents = json.dumps(manifest, indent=2).encode() + b'\n'
                if entry.endswith('/' + ('ASCII' if library == 'ascii' else 'UTF8') + '.php'):
                    text = contents.decode()
                    if library == 'ascii':
                        old = """        $file = __DIR__ . '/data/' . $file . '.php';
        if (\\is_file($file)) {
            return include $file;
        }

        return [];"""
                        new = """        if (!\\class_exists(\\Voku\\PortableAsciiMappingData\\BankMap::class)) {
            throw new \\RuntimeException('%s');
        }

        return \\Voku\\PortableAsciiMappingData\\BankMap::load($file);""" % message(name)
                    else:
                        old = "        return include __DIR__ . '/data/' . $file . '.php';"
                        new = """        if ($file === 'emoji') {
            if (!\\class_exists(\\Voku\\PortableUtf8EmojiData\\EmojiMap::class)) {
                throw new \\RuntimeException('%s');
            }

            return \\Voku\\PortableUtf8EmojiData\\EmojiMap::load();
        }

%s""" % (message(name), old)
                    if text.count(old) != 1:
                        raise RuntimeError('Unexpected loader anchor in ' + library)
                    contents = text.replace(old, new).encode()
                core_files[entry] = contents
        package['require'][name] = VERSION
        package['dist'] = write_zip(args.output / (library + '-core.zip'), core_files)
        package.pop('source', None)
        child['dist'] = write_zip(args.output / (library + '-data.zip'), child_files)
        packages.append(child)
        archives_evidence.append({'library': library, 'input_reference': locked['voku/portable-' + library]['dist']['reference'], 'input_zip_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'mapping_bytes': moved, 'core': package['dist'], 'data': child['dist']})
    return archives_evidence


def repository_archives(args, original):
    """Use real committed cores/providers; aliases exist only in this local test registry."""
    packages = original['repositories'][0]['package']
    evidence = []
    for library, name in [('ascii', BANKS), ('utf8', EMOJI)]:
        core_name = 'voku/portable-' + library
        for package_name, version in [(core_name, '2.1.99' if library == 'ascii' else '6.1.99'), (name, VERSION)]:
            root = args.repository_workspace / package_name.split('/')[1]
            ref = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
            if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip():
                raise RuntimeError('Repository is not committed and clean: ' + str(root))
            path = args.output / (package_name.split('/')[1] + '.zip')
            subprocess.run(['git', '-C', str(root), 'archive', '--format=zip', '--prefix=package/', '--output', str(path), ref], check=True)
            manifest = json.loads(subprocess.check_output(['git', '-C', str(root), 'show', ref + ':composer.json'], text=True))
            package = {key: manifest[key] for key in ['name', 'description', 'type', 'license', 'authors', 'require', 'autoload', 'homepage'] if key in manifest}
            package['version'] = version
            package['dist'] = {'type': 'zip', 'url': path.as_uri(), 'reference': ref, 'shasum': hashlib.sha1(path.read_bytes()).hexdigest()}
            package['source'] = {'type': 'git', 'url': 'https://github.com/' + package_name + '.git', 'reference': ref}
            packages[:] = [p for p in packages if p['name'] != package_name]
            packages.append(package)
            evidence.append({'name': package_name, 'reference': ref, 'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                             'local_test_alias': version, 'published_version': False})
    return evidence


def composer(args, directory, operation, label, expect_failure=False, extra=()):
    with (directory / (label + '.log')).open('w') as log:
        process = subprocess.run([args.composer, operation, '--no-dev', '--no-interaction', '--prefer-dist', '--no-progress', *extra], cwd=directory, stdout=log, stderr=subprocess.STDOUT)
    if (process.returncode != 0) != expect_failure:
        raise RuntimeError('Unexpected Composer result: ' + str(directory / (label + '.log')))


def installed(directory):
    return json.loads((directory / 'vendor/composer/installed.json').read_text())['packages']


def verify_mapping_hashes(args, directory, omitted):
    for library, name in [('ascii', BANKS), ('utf8', EMOJI)]:
        if name in omitted:
            continue
        with zipfile.ZipFile(args.consumers / ('portable-' + library + '-after.zip')) as archive:
            for entry in archive.namelist():
                filename = pathlib.PurePosixPath(entry).name
                if '/src/voku/helper/data/' in entry and ((library == 'ascii' and filename.startswith('x') and filename.endswith('.php')) or (library == 'utf8' and filename == 'emoji.php')):
                    actual = directory / 'vendor' / name / 'data' / filename
                    if actual.read_bytes() != archive.read(entry):
                        raise RuntimeError('Installed data differs: ' + str(actual))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumers', type=pathlib.Path, required=True, help='Completed measure.py output')
    parser.add_argument('--output', type=pathlib.Path, required=True, help='New empty scratch directory')
    parser.add_argument('--composer', default='composer')
    parser.add_argument('--php', default='php', help='Real PHP executable; must honor -n')
    parser.add_argument('--extension-dir', type=pathlib.Path, required=True)
    parser.add_argument('--repository-workspace', type=pathlib.Path, help='Use four real committed repositories instead of rewriting prototype archives')
    args = parser.parse_args()
    args.consumers = args.consumers.resolve()
    args.output = args.output.resolve()
    if args.output.exists() and any(args.output.iterdir()):
        raise RuntimeError('Refusing to reuse output; use a new empty directory')
    args.output.mkdir(parents=True, exist_ok=True)
    original = json.loads((args.consumers / 'utf8-after-dist/composer.json').read_text())
    if args.repository_workspace:
        args.repository_workspace = args.repository_workspace.resolve()
    archive_evidence = repository_archives(args, original) if args.repository_workspace else archives(args, original)
    installations = {}
    modes = {'full': [], 'no-emoji': [EMOJI], 'no-banks': [BANKS], 'both': [EMOJI, BANKS]}
    for mode, omitted in modes.items():
        directory = args.output / mode
        directory.mkdir()
        manifest = copy.deepcopy(original)
        if omitted:
            manifest['replace'] = {name: VERSION for name in omitted}
        save(directory / 'composer.json', manifest)
        # Resolve first, then compare two clean installs from the same lock. Composer
        # 2.2 can choose a provisional autoloader suffix during update before lock write.
        composer(args, directory, 'update', 'resolve', extra=['--no-install'])
        composer(args, directory, 'install', 'initial-install')
        packages = installed(directory)
        if any(p['installation-source'] != 'dist' for p in packages):
            raise RuntimeError('Non-Dist install')
        names = [p['name'] for p in packages]
        for name in [EMOJI, BANKS]:
            if (name in names) == (name in omitted):
                raise RuntimeError('Composer did not honor replacement: ' + mode)
        verify_mapping_hashes(args, directory, omitted)
        first = footprint(directory / 'vendor')
        first_hashes = tree_hashes(directory / 'vendor')
        lock = (directory / 'composer.lock').read_bytes()
        shutil.rmtree(directory / 'vendor')
        composer(args, directory, 'install', 'reinstall')
        checks = {'lock_match': lock == (directory / 'composer.lock').read_bytes(), 'packages_match': packages == installed(directory), 'footprint_match': first == footprint(directory / 'vendor'), 'tree_match': first_hashes == tree_hashes(directory / 'vendor')}
        save(directory / 'reinstall-check.json', checks)
        if not all(checks.values()):
            raise RuntimeError('Lock reinstall changed package metadata or footprint: ' + mode + ': ' + str(checks))
        verify_mapping_hashes(args, directory, omitted)
        installations[mode] = {'omitted': omitted, 'vendor': first, 'packages': names,
                               'lock_sha256': hashlib.sha256(lock).hexdigest(), 'reinstall_match': True, 'vendor_tree_sha256': hashlib.sha256(json.dumps(first_hashes, sort_keys=True).encode()).hexdigest()}
        print(mode, first, flush=True)
    # A pinned lie cannot satisfy a future data contract. Providers remain available at 1.0.0 only.
    directory = args.output / 'future-version-guard'
    directory.mkdir()
    future = copy.deepcopy(original)
    future['replace'] = {EMOJI: VERSION}
    next(p for p in future['repositories'][0]['package'] if p['name'] == 'voku/portable-utf8')['require'][EMOJI] = '1.1.0'
    save(directory / 'composer.json', future)
    composer(args, directory, 'update', 'resolve', expect_failure=True)
    directory = args.output / 'unsafe-wildcard-control'
    directory.mkdir()
    future['replace'][EMOJI] = '*'
    save(directory / 'composer.json', future)
    composer(args, directory, 'update', 'resolve')
    if EMOJI in [p['name'] for p in installed(directory)]:
        raise RuntimeError('Wildcard control unexpectedly installed emoji data')
    baseline = args.consumers / 'utf8-after-dist'
    baseline_roots = {library: baseline / 'vendor/voku' / ('portable-' + library.lower()) for library in ['ASCII', 'UTF8']}
    matrix = []
    json_module = []
    if subprocess.run([args.php, '-n', '-r', 'exit(function_exists("json_encode") ? 0 : 1);']).returncode:
        json_module = ['-d', 'extension=json.so']
    polyfill = next(p for p in original['repositories'][0]['package'] if p['name'] == 'symfony/polyfill-mbstring')
    requires_iconv = 'ext-iconv' in polyfill.get('require', {})
    for flags in itertools.product([0, 1], repeat=3):
        profile = ''.join(map(str, flags))
        command = [args.php, '-n', '-d', 'extension_dir=' + str(args.extension_dir), '-d', 'memory_limit=512M', '-d', 'date.timezone=UTC', *json_module]
        for enabled, module in zip(flags, ['intl', 'mbstring', 'iconv']):
            if enabled:
                command += ['-d', 'extension=' + module + '.so']
        active = json.loads(subprocess.check_output(command + ['-r', "echo json_encode(array_map('extension_loaded', ['intl','mbstring','iconv']));"], text=True))
        if active != list(map(bool, flags)):
            raise RuntimeError('The executable does not honor -n: profile ' + profile)
        solver_results = {}
        for mode, omitted in modes.items():
            # Simulate absent consumer extensions in Composer's solver, while retaining
            # modules needed to run Composer itself. No ignore-platform-reqs shortcut.
            directory = args.output / ('solver-' + profile + '-' + mode)
            directory.mkdir()
            manifest = json.loads((args.output / mode / 'composer.json').read_text())
            manifest['config']['platform'] = {'ext-' + module: False for enabled, module in zip(flags, ['intl', 'mbstring', 'iconv']) if not enabled}
            if not manifest['config']['platform']:
                manifest['config'].pop('platform')
            save(directory / 'composer.json', manifest)
            # Pinned polyfill-mbstring 1.43 requires ext-iconv: this is inherited,
            # independent of data extraction and cannot be solved by replacing data.
            composer(args, directory, 'update', 'resolve', expect_failure=requires_iconv and not flags[2], extra=['--no-install'])
            resolves = not requires_iconv or bool(flags[2])
            if resolves:
                resolved = json.loads((directory / 'composer.lock').read_text())['packages']
                pinned = json.loads((args.output / mode / 'composer.lock').read_text())['packages']
                if resolved != pinned:
                    raise RuntimeError('Extension solver changed pinned packages')
            else:
                failure = (directory / 'resolve.log').read_text()
                if 'requires ext-iconv' not in failure:
                    raise RuntimeError('Unexpected missing-extension solver failure')
            solver_results[mode] = {'resolves': resolves, 'reason': None if resolves else 'Pinned symfony/polyfill-mbstring ' + polyfill['version'] + ' requires ext-iconv'}
        # Full provider installation must match the complete behavioral/diagnostic corpus.
        full_results = []
        for library in ['ASCII', 'UTF8']:
            root = baseline_roots[library]
            before = json.loads(subprocess.check_output(command + [str(HERE / 'contract.php'), str(root), library, str(baseline / 'vendor/autoload.php'), str(root)], text=True))
            after = json.loads(subprocess.check_output(command + [str(HERE / 'contract.php'), str(args.output / 'full/vendor/voku' / ('portable-' + library.lower())), library, str(args.output / 'full/vendor/autoload.php'), str(root)], text=True))
            if before != after:
                changed = [name for name in before['results'] if before['results'][name] != after['results'].get(name)]
                raise RuntimeError('Full contract differs: ' + profile + ' ' + library + ' ' + str(changed[:10]))
            full_results.append({'library': library, 'cases': len(before['results']), 'differences': []})
        results = {}
        for case in CASES:
            reference = json.loads(subprocess.check_output(command + [str(HERE / 'opt-out-probe.php'), str(baseline), case], text=True))
            for mode, omitted in modes.items():
                actual = json.loads(subprocess.check_output(command + [str(HERE / 'opt-out-probe.php'), str(args.output / mode), case], text=True))
                missing = EMOJI if EMOJI in omitted and case in EMOJI_CASES else (BANKS if BANKS in omitted and (case in BANK_CASES or (case == 'banks-strict' and not flags[0])) else None)
                expected = ['exception', 'RuntimeException', message(missing)] if missing else reference['result']
                if actual['result'] != expected or actual['warnings'] != reference['warnings'] or actual['output'] != reference['output']:
                    raise RuntimeError('Opt-out result differs: ' + profile + ' ' + mode + ' ' + case + ': ' + str(actual) + ' expected ' + str(expected))
                # Retained providers must not load for unrelated/early-return paths.
                if case in {'ascii-pass', 'language-map', 'utf8-length', 'utf8-repair', 'utf8-ord', 'support-key', 'support-full', 'html-empty', 'utf8-filename-default'} and any(actual['loaded_providers'].values()):
                    raise RuntimeError('Unrelated operation loaded a provider')
                results[mode + ':' + case] = actual
        matrix.append({'intl_mbstring_iconv': profile, 'full_contract': full_results, 'composer_solver': solver_results, 'opt_out_cases': results})
        print('Profile', profile, ': full contract and all opt-outs match', flush=True)
    baseline_size = footprint(baseline / 'vendor')
    full_size = installations['full']['vendor']
    for install in installations.values():
        install['saved_against_full'] = {key: full_size[key] - install['vendor'][key] for key in full_size}
        install['saved_against_in_place'] = {key: baseline_size[key] - install['vendor'][key] for key in full_size}
    result = {'scope': ('Real committed core/provider repositories, actual Dist installs, local version aliases only; no tags or Packagist versions.' if args.repository_workspace else 'Isolated Dist-only scratch prototype, not published packages or production dependency changes.'),
              'php_version': subprocess.check_output([args.php, '-n', '-r', 'echo PHP_VERSION;'], text=True),
              'composer_version': subprocess.check_output([args.composer, '--version', '--no-ansi'], text=True).strip(),
              'in_place_vendor': baseline_size, 'archives': archive_evidence,
              'installations': installations, 'future_version_pin_rejected': True, 'unsafe_wildcard_satisfies_future_contract': True, 'extension_matrix': matrix}
    save(args.output / 'opt-out-results.json', result)
    print('All checks passed:', args.output / 'opt-out-results.json', flush=True)


if __name__ == '__main__':
    main()
