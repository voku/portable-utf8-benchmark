<?php

$root = $argv[1];
$library = $argv[2];
$autoload = $argv[3];
$scenario = $argv[4];
if ($library === 'UTF8') {
    require $root . '/src/voku/helper/Bootup.php';
}
require $root . '/src/voku/helper/' . $library . '.php';
require $autoload;
$class = 'voku\\helper\\' . $library;
$cases = [
    'ascii' => ['to_transliterate', ['中文空白 Straße 😀', '?', false]],
    'chr' => ['chr', [0x1f600]],
    'ord' => ['ord', ['😀']],
    'repair' => ['utf8_encode', [str_repeat("\x80\xff", 64)]],
    'emoji' => ['emoji_encode', ['foo 👹 👩‍👩‍👧‍👦 🏳️‍🌈 😀 ✈️', true]],
    'support' => ['getSupportInfo', ['intl']],
    'locale' => ['strtolower', ['İstanbul IĞDIR', 'UTF-8', false, 'tr']],
];
[$method, $arguments] = $cases[$scenario];
$warnings = [];
set_error_handler(static function ($level, $message) use (&$warnings): bool {
    $warnings[$level . ':' . $message] = [$level, $message];

    return true;
});
$beforeMemory = memory_get_usage();
$start = microtime(true);
$value = call_user_func_array([$class, $method], $arguments);
$cold = (microtime(true) - $start) * 1000000;
$retained = memory_get_usage() - $beforeMemory;
$samples = [];
$iterations = $scenario === 'emoji' ? 100 : 1000;
for ($round = 0; $round < 5; ++$round) {
    $start = microtime(true);
    for ($i = 0; $i < $iterations; ++$i) {
        call_user_func_array([$class, $method], $arguments);
    }
    $samples[] = (microtime(true) - $start) * 1000000 / $iterations;
}
sort($samples);
$metadata = [];
foreach (get_included_files() as $file) {
    if (basename($file) === 'transliterator_list.php') {
        $metadata[] = basename($file);
    }
}
echo json_encode(['cold_us' => $cold, 'warm_median_us' => $samples[2], 'iterations' => $iterations, 'rounds' => 5, 'retained_bytes' => $retained, 'peak_bytes' => memory_get_peak_usage(), 'output_sha256' => hash('sha256', serialize($value)), 'metadata_includes' => $metadata, 'warnings' => array_values($warnings)]), PHP_EOL;
