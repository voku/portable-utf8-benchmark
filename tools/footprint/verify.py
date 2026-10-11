#!/usr/bin/env python3
"""Compare public outputs, diagnostic payloads and reflection signatures per active PHP profile."""
import argparse, json, pathlib, subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--workspace', type=pathlib.Path, default=pathlib.Path('/workspace'))
parser.add_argument('--baselines', type=pathlib.Path, required=True)
parser.add_argument('--output', type=pathlib.Path, required=True)
parser.add_argument('--php', default='php')
parser.add_argument('--autoload-root', type=pathlib.Path, help='An isolated production Composer consumer with vendor/autoload.php')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
probe = pathlib.Path(__file__).with_name('contract.php')
summary = []
for repo, library in [('portable-ascii', 'ASCII'), ('portable-utf8', 'UTF8')]:
    autoload = ((args.autoload_root / 'vendor/autoload.php') if args.autoload_root else (args.workspace / repo / 'vendor/autoload.php'))
    data = []
    for phase, root in [('before', args.baselines / (repo + '-baseline')), ('after', args.workspace / repo)]:
        process = subprocess.run([args.php, str(probe), str(root), library, str(autoload)], text=True, capture_output=True)
        if process.returncode:
            raise RuntimeError(f"{repo}/{phase}: PHP probe failed ({process.returncode})\n{process.stdout}\n{process.stderr}")
        (args.output / (repo + '-' + phase + '.json')).write_text(process.stdout)
        data.append(json.loads(process.stdout))
    signatures = [name for name in data[0]['signatures'] if data[0]['signatures'][name] != data[1]['signatures'].get(name)]
    signatures += list(data[1]['signatures'].keys() - data[0]['signatures'].keys())
    differences = [name for name in sorted(data[0]['results'].keys() | data[1]['results'].keys()) if data[0]['results'].get(name) != data[1]['results'].get(name)]
    summary.append({'repository': repo, 'cases': len(data[0]['results']), 'signature_differences': signatures, 'behavior_differences': differences})
    if signatures or differences:
        raise RuntimeError(f'{repo}: signatures={signatures}, behavior={differences[:20]}')
    print(repo, len(data[0]['results']), 'cases: outputs and diagnostics match')
(args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
