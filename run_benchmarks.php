<?php

declare(strict_types=1);

require_once __DIR__ . '/inc_globals.php';

use Composer\InstalledVersions;
use Patchwork\Utf8 as PatchworkUtf8;
use voku\helper\UTF8;

/**
 * @return array<string, mixed>
 */
function parseOptions(array $argv): array
{
    $options = array(
        'json' => false,
        'output' => null,
        'iterations' => 5000,
    );

    foreach (array_slice($argv, 1) as $argument) {
        if ($argument === '--json') {
            $options['json'] = true;
            continue;
        }

        if (strpos($argument, '--output=') === 0) {
            $options['output'] = substr($argument, 9);
            continue;
        }

        if (strpos($argument, '--iterations=') === 0) {
            $iterations = (int) substr($argument, 13);

            if ($iterations > 0) {
                $options['iterations'] = $iterations;
            }
        }
    }

    return $options;
}

function formatDurationMilliseconds(float $seconds): string
{
    return number_format($seconds * 1000, 4) . ' ms';
}

function formatAverageMicroseconds(float $seconds, int $iterations): string
{
    return number_format(($seconds / $iterations) * 1000000, 4) . ' µs';
}

function formatBytes(int $bytes): string
{
    if ($bytes < 1024) {
        return $bytes . ' b';
    }

    $units = array('kb', 'mb', 'gb', 'tb');
    $value = $bytes / 1024;
    $unit = 0;

    while ($value >= 1024 && isset($units[$unit + 1])) {
        $value /= 1024;
        ++$unit;
    }

    return number_format($value, 2) . ' ' . $units[$unit];
}

/**
 * @return array<string, mixed>
 */
function benchmarkCallable(callable $callback, int $iterations): array
{
    gc_collect_cycles();

    if (function_exists('memory_reset_peak_usage')) {
        memory_reset_peak_usage();
    }

    $memoryStart = memory_get_usage(true);
    $peakMemoryStart = memory_get_peak_usage(true);
    $start = hrtime(true);

    for ($index = 0; $index < $iterations; ++$index) {
        $callback();
    }

    $elapsed = (hrtime(true) - $start) / 1000000000;
    $memoryDelta = max(memory_get_usage(true) - $memoryStart, 0);
    $peakMemoryDelta = max(memory_get_peak_usage(true) - $peakMemoryStart, 0);

    return array(
        'iterations' => $iterations,
        'total_seconds' => $elapsed,
        'average_microseconds' => ($elapsed / $iterations) * 1000000,
        'memory_usage_bytes' => $memoryDelta,
        'peak_memory_usage_bytes' => $peakMemoryDelta,
    );
}

/**
 * @param array<int, array<string, mixed>> $results
 */
function printTable(array $results): void
{
    $headers = array('BENCHMARK', 'LIBRARY', 'ITERATIONS', 'TOTAL', 'AVG', 'PEAK MEMORY');
    $widths = array_map('strlen', $headers);

    foreach ($results as $result) {
        $values = array(
            $result['benchmark'],
            $result['library'],
            (string) $result['iterations'],
            formatDurationMilliseconds($result['total_seconds']),
            formatAverageMicroseconds($result['total_seconds'], $result['iterations']),
            formatBytes($result['peak_memory_usage_bytes']),
        );

        foreach ($values as $index => $value) {
            $widths[$index] = max($widths[$index], strlen($value));
        }
    }

    $mask = sprintf(
        "%%-%ds  %%-%ds  %%-%ds  %%-%ds  %%-%ds  %%-%ds\n",
        $widths[0],
        $widths[1],
        $widths[2],
        $widths[3],
        $widths[4],
        $widths[5]
    );

    printf($mask, $headers[0], $headers[1], $headers[2], $headers[3], $headers[4], $headers[5]);

    foreach ($results as $result) {
        printf(
            $mask,
            $result['benchmark'],
            $result['library'],
            (string) $result['iterations'],
            formatDurationMilliseconds($result['total_seconds']),
            formatAverageMicroseconds($result['total_seconds'], $result['iterations']),
            formatBytes($result['peak_memory_usage_bytes'])
        );
    }
}

/**
 * @param array<string, array<int, array<string, mixed>>> $groupedResults
 *
 * @return array<int, array<string, mixed>>
 */
function buildComparisons(array $groupedResults): array
{
    $comparisons = array();

    foreach ($groupedResults as $benchmarkName => $entries) {
        if (count($entries) < 2) {
            continue;
        }

        usort(
            $entries,
            static function (array $left, array $right): int {
                return $left['total_seconds'] <=> $right['total_seconds'];
            }
        );

        $winner = $entries[0];
        $runnerUp = $entries[1];

        $comparisons[] = array(
            'benchmark' => $benchmarkName,
            'winner' => $winner['library'],
            'loser' => $runnerUp['library'],
            'speedup_ratio' => $runnerUp['total_seconds'] > 0 ? $runnerUp['total_seconds'] / $winner['total_seconds'] : 0.0,
        );
    }

    return $comparisons;
}

/**
 * @return array<int, array<string, mixed>>
 */
function benchmarkDefinitions(): array
{
    $multibyteText = "Iñtërnâtiônàlizætiøn — Καλημέρα κόσμε — こんにちは世界";
    $searchHaystack = 'ABC-ÖÄÜ-中文空白-emoji-😀-中文空白';
    $trimInput = " \t\n\r\0\x0B«ÄÖÜ ß 😀 中文» \n\t ";

    return array(
        array(
            'name' => 'is_utf8',
            'voku' => static function () use ($multibyteText): bool {
                return UTF8::is_utf8($multibyteText);
            },
            'patchwork' => static function () use ($multibyteText): bool {
                return PatchworkUtf8::isUtf8($multibyteText);
            },
        ),
        array(
            'name' => 'substr',
            'voku' => static function () use ($multibyteText): string {
                return UTF8::substr($multibyteText, 3, 18);
            },
            'patchwork' => static function () use ($multibyteText): string {
                return PatchworkUtf8::substr($multibyteText, 3, 18);
            },
        ),
        array(
            'name' => 'strlen',
            'voku' => static function () use ($multibyteText): int {
                return UTF8::strlen($multibyteText);
            },
            'patchwork' => static function () use ($multibyteText): int {
                return PatchworkUtf8::strlen($multibyteText);
            },
        ),
        array(
            'name' => 'strpos',
            'voku' => static function () use ($searchHaystack): int {
                return (int) UTF8::strpos($searchHaystack, '中文');
            },
            'patchwork' => static function () use ($searchHaystack): int {
                return (int) PatchworkUtf8::strpos($searchHaystack, '中文');
            },
        ),
        array(
            'name' => 'stripos',
            'voku' => static function () use ($searchHaystack): int {
                return (int) UTF8::stripos($searchHaystack, 'ö');
            },
            'patchwork' => static function () use ($searchHaystack): int {
                return (int) PatchworkUtf8::stripos($searchHaystack, 'ö');
            },
        ),
        array(
            'name' => 'strripos',
            'voku' => static function () use ($searchHaystack): int {
                return (int) UTF8::strripos($searchHaystack, '中文');
            },
            'patchwork' => static function () use ($searchHaystack): int {
                return (int) PatchworkUtf8::strripos($searchHaystack, '中文');
            },
        ),
        array(
            'name' => 'strtolower',
            'voku' => static function () use ($multibyteText): string {
                return UTF8::strtolower($multibyteText);
            },
            'patchwork' => static function () use ($multibyteText): string {
                return PatchworkUtf8::strtolower($multibyteText);
            },
        ),
        array(
            'name' => 'strtoupper',
            'voku' => static function () use ($multibyteText): string {
                return UTF8::strtoupper($multibyteText);
            },
            'patchwork' => static function () use ($multibyteText): string {
                return PatchworkUtf8::strtoupper($multibyteText);
            },
        ),
        array(
            'name' => 'trim',
            'voku' => static function () use ($trimInput): string {
                return UTF8::trim($trimInput);
            },
            'patchwork' => static function () use ($trimInput): string {
                return PatchworkUtf8::trim($trimInput);
            },
        ),
    );
}

$options = parseOptions($argv);
$results = array();
$groupedResults = array();

foreach (benchmarkDefinitions() as $definition) {
    foreach (array('voku', 'patchwork') as $library) {
        $result = benchmarkCallable($definition[$library], $options['iterations']);
        $result['benchmark'] = $definition['name'];
        $result['library'] = $library;
        $results[] = $result;
        $groupedResults[$definition['name']][] = $result;
    }
}

usort(
    $results,
    static function (array $left, array $right): int {
        return array($left['benchmark'], $left['total_seconds']) <=> array($right['benchmark'], $right['total_seconds']);
    }
);

$payload = array(
    'generated_at' => gmdate(DATE_ATOM),
    'php_version' => PHP_VERSION,
    'dependencies' => array(
        'voku/portable-utf8' => InstalledVersions::getPrettyVersion('voku/portable-utf8'),
        'patchwork/utf8' => InstalledVersions::getPrettyVersion('patchwork/utf8'),
    ),
    'benchmarks' => $results,
    'comparisons' => buildComparisons($groupedResults),
);

if ($options['json']) {
    $json = json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);

    if ($json === false) {
        fwrite(STDERR, "Failed to encode benchmark results.\n");
        exit(1);
    }

    if ($options['output'] !== null) {
        $directory = dirname($options['output']);

        if (!is_dir($directory) && !mkdir($directory, 0777, true) && !is_dir($directory)) {
            fwrite(STDERR, "Failed to create output directory.\n");
            exit(1);
        }

        file_put_contents($options['output'], $json . PHP_EOL);
        echo 'Wrote benchmark results to ' . $options['output'] . PHP_EOL;
    } else {
        echo $json . PHP_EOL;
    }

    exit(0);
}

echo 'PHP ' . PHP_VERSION . PHP_EOL;
echo 'voku/portable-utf8: ' . InstalledVersions::getPrettyVersion('voku/portable-utf8') . PHP_EOL;
echo 'patchwork/utf8: ' . InstalledVersions::getPrettyVersion('patchwork/utf8') . PHP_EOL . PHP_EOL;

printTable($results);

echo PHP_EOL . 'Fastest library per benchmark:' . PHP_EOL;

foreach ($payload['comparisons'] as $comparison) {
    echo sprintf(
        '- %s: %s (%.2fx faster than %s)%s',
        $comparison['benchmark'],
        $comparison['winner'],
        $comparison['speedup_ratio'],
        $comparison['loser'],
        PHP_EOL
    );
}
