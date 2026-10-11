<?php

// Every invocation is a fresh process: earlier calls cannot prewarm missing-data caches.
require $argv[1] . '/vendor/autoload.php';
$case = $argv[2];
$providers = ['Voku\\PortableUtf8EmojiData\\EmojiMap', 'Voku\\PortableAsciiMappingData\\BankMap'];
foreach ($providers as $provider) {
    if (class_exists($provider, false)) {
        throw new RuntimeException('Mapping provider was loaded eagerly during bootstrap');
    }
}
$calls = [
    'ascii-pass' => ['voku\\helper\\ASCII', 'to_transliterate', ['Plain ASCII 123']],
    'language-map' => ['voku\\helper\\ASCII', 'to_ascii', ['Düsseldorf Straße', 'de', false]],
    'utf8-length' => ['voku\\helper\\UTF8', 'strlen', ['Düsseldorf']],
    'utf8-repair' => ['voku\\helper\\UTF8', 'fix_utf8', ["\xc3"]],
    'utf8-ord' => ['voku\\helper\\UTF8', 'ord', ['ö']],
    'support-key' => ['voku\\helper\\UTF8', 'getSupportInfo', ['intl']],
    'support-full' => ['voku\\helper\\UTF8', 'getSupportInfo', []],
    'html-empty' => ['voku\\helper\\UTF8', 'is_html', ['']],
    'emoji-encode' => ['voku\\helper\\UTF8', 'emoji_encode', ['👹']],
    'emoji-decode' => ['voku\\helper\\UTF8', 'emoji_decode', ['CHARACTER_OGRE']],
    'reverse-ascii' => ['voku\\helper\\UTF8', 'strrev', ['hello']],
    'reverse-unicode' => ['voku\\helper\\UTF8', 'strrev', ['Düsseldorf 👹']],
    'html-ascii' => ['voku\\helper\\UTF8', 'is_html', ['<b>hello</b>']],
    'banks-direct' => ['voku\\helper\\ASCII', 'to_transliterate', ['中文空白', '?', false]],
    'banks-strict' => ['voku\\helper\\ASCII', 'to_transliterate', ['中文空白', '?', true]],
    'utf8-ascii' => ['voku\\helper\\UTF8', 'to_ascii', ['中文空白']],
    'ascii-filename' => ['voku\\helper\\ASCII', 'to_filename', ['中文.txt']],
    'utf8-filename' => ['voku\\helper\\UTF8', 'to_filename', ['中文.txt', true]],
    'utf8-filename-default' => ['voku\\helper\\UTF8', 'to_filename', ['中文.txt']],
    'unmapped-bank' => ['voku\\helper\\ASCII', 'to_transliterate', ["\xf4\x8f\xbf\xbf", '?', false]],
];
if (!isset($calls[$case])) {
    throw new InvalidArgumentException('Unknown probe: ' . $case);
}
$warnings = [];
set_error_handler(static function ($level, $message) use (&$warnings): bool {
    $warnings[] = [$level, $message];
    return true;
});
ob_start();
try {
    $call = $calls[$case];
    $result = ['value', base64_encode(serialize(call_user_func_array([$call[0], $call[1]], $call[2])))];
} catch (Throwable $error) {
    $result = ['exception', get_class($error), $error->getMessage()];
}
$output = ob_get_clean();
restore_error_handler();
$loaded = [];
foreach ($providers as $provider) {
    $loaded[$provider] = class_exists($provider, false);
}
echo json_encode(['result' => $result, 'warnings' => $warnings, 'output' => base64_encode($output), 'loaded_providers' => $loaded], JSON_UNESCAPED_SLASHES), PHP_EOL;
