<?php

// Run against two roots in separate processes to compare outputs AND diagnostics.
$root = $argv[1];
$library = $argv[2];
$autoload = $argv[3];
// An extracted package can use an independent immutable corpus without restoring data to its core.
$corpusRoot = isset($argv[4]) && $argv[4] !== '--signatures-only' ? $argv[4] : $root;
if ($library === 'UTF8') {
    require $root . '/src/voku/helper/Bootup.php';
}
require $root . '/src/voku/helper/' . $library . '.php';
require $autoload;
$class = 'voku\\helper\\' . $library;
$results = [];
$record = static function ($label, $method, array $args) use ($class, &$results): void {
    $warnings = [];
    set_error_handler(static function ($level, $message) use (&$warnings): bool {
        $warnings[] = [$level, $message];
        return true;
    });
    ob_start();
    try {
        $value = ['value', call_user_func_array([$class, $method], $args)];
    } catch (Throwable $error) {
        $value = ['exception', get_class($error), preg_replace('/, called in .* on line [0-9]+$/', ', called in <caller>', $error->getMessage())];
    } finally {
        restore_error_handler();
        $output = ob_get_clean();
    }
    $results[$label] = [base64_encode(serialize($value)), $warnings, base64_encode($output)];
};
$reflection = new ReflectionClass($class);
$signatures = [];
foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
    $parameters = [];
    foreach ($method->getParameters() as $parameter) {
        $parameters[] = [$parameter->getName(), (string) $parameter->getType(), $parameter->isPassedByReference(), $parameter->isVariadic(), $parameter->isDefaultValueAvailable() ? base64_encode(serialize($parameter->getDefaultValue())) : null];
    }
    $signatures[$method->getName()] = [$method->isStatic(), (string) $method->getReturnType(), $parameters];
}
ksort($signatures);
if (in_array('--signatures-only', $argv, true)) {
    echo json_encode($signatures, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
    exit(0);
}
$corpus = ['', "\0\1\x7f", 'Plain ASCII 123', 'Düsseldorf Straße déjà vu', 'Αυτή είναι μια δοκιμή', 'တတျနိုငျသ', '中文空白', "\xef\xbe\xa0", '😀👩‍👩‍👧‍👦🏳️‍🌈✈️', "\xc3", "\x80\xff", "\xe2\x28\xa1", "\xf0\x9f", "e\xcc\x81", '_-_PORTABLE_UTF8_-_308095726_-_627590803_-_8FTU_ELBATROP_-_ CHARACTER_OGRE'];
for ($i = 0; $i < 256; ++$i) {
    $corpus[] = chr($i);
}
if ($library === 'UTF8') {
    $record('support-before', 'getSupportInfo', []);
    $record('show-before-no-echo', 'showSupport', [false]);
    $record('show-before-echo', 'showSupport', [true]);
    foreach (array_merge(array_keys($class::getSupportInfo()), ['not-a-key', 'intl__transliterator_list_ids']) as $key) {
        $record('support-' . $key, 'getSupportInfo', [$key]);
        $record('show-after-' . $key . '-no-echo', 'showSupport', [false]);
        $record('show-after-' . $key . '-echo', 'showSupport', [true]);
        $record('support-after-' . $key, 'getSupportInfo', []);
    }
    foreach (array_merge(range(0, 255), [-1, PHP_INT_MIN, PHP_INT_MAX, 0x7ff, 0x800, 0xd800, 0xdfff, 0xffff, 0x10000, 0x10ffff, 0x110000, 0x3fffff, 0x400000, 256.5, '65', null, true]) as $i => $code) {
        foreach (['UTF-8', 'ISO-8859-1', 'WINDOWS-1252', 'CP850'] as $encoding) {
            $record('chr-' . $i . '-' . $encoding, 'chr', [$code, $encoding]);
        }
    }
    $map = include $corpusRoot . '/src/voku/helper/data/emoji.php';
    $corpus[] = implode(' ', array_values($map));
    $corpus[] = implode(' ', array_keys($map));
    foreach ($corpus as $i => $text) {
        foreach (['UTF-8', 'ISO-8859-1', 'WINDOWS-1252', 'CP850'] as $encoding) {
            $record('ord-' . $i . '-' . $encoding, 'ord', [$text, $encoding]);
        }
        foreach (['utf8_encode', 'to_utf8', 'fix_utf8', 'is_utf8'] as $method) {
            $record($method . '-' . $i, $method, [$text]);
        }
        foreach ([false, true] as $flag) {
            $record('decode-' . $i . '-' . (int) $flag, 'utf8_decode', [$text, $flag]);
            $record('emoji-encode-' . $i . '-' . (int) $flag, 'emoji_encode', [$text, $flag]);
            $record('emoji-decode-' . $i . '-' . (int) $flag, 'emoji_decode', [$text, $flag]);
        }
        foreach (['tr', 'de', 'el', 'invalid-locale'] as $locale) {
            foreach (['strtolower', 'strtoupper'] as $method) {
                $record($method . '-' . $i . '-' . $locale, $method, [$text, 'UTF-8', false, $locale]);
            }
        }
    }
    // Preserve the existing by-reference debug-output/cache interaction.
    $supportSnapshot = $class::getSupportInfo();
    $supportSnapshot['intl__transliterator_list_ids'] = ['caller-mutated-list'];
    $record('support-reference-mutated', 'getSupportInfo', []);
    $record('support-reference-key-reset', 'getSupportInfo', ['intl']);
    $record('support-reference-reset-full', 'getSupportInfo', []);
    // Exercise the validator branch normally bypassed by PCRE Unicode support.
    $support = new ReflectionProperty($class, 'SUPPORT');
    $support->setAccessible(true);
    $flags = $support->getValue();
    $flags['pcre_utf8'] = false;
    $support->setValue(null, $flags);
    foreach ($corpus as $i => $text) {
        $record('manual-validate-' . $i, 'is_utf8', [$text]);
    }
} else {
    foreach (glob($corpusRoot . '/src/voku/helper/data/x*.php') as $file) {
        $bank = hexdec(substr(basename($file), 1, -4));
        $text = '';
        foreach (include $file as $offset => $value) {
            $code = ($bank << 8) + $offset;
            $text .= $code < 0x80 ? chr($code) : ($code < 0x800 ? chr(0xc0 | ($code >> 6)) . chr(0x80 | ($code & 63)) : ($code < 0x10000 ? chr(0xe0 | ($code >> 12)) . chr(0x80 | (($code >> 6) & 63)) . chr(0x80 | ($code & 63)) : chr(0xf0 | ($code >> 18)) . chr(0x80 | (($code >> 12) & 63)) . chr(0x80 | (($code >> 6) & 63)) . chr(0x80 | ($code & 63))));
            $text .= '|';
        }
        $corpus[] = $text;
    }
    foreach ($corpus as $i => $text) {
        foreach ([false, true] as $strict) {
            foreach ([null, '?', '', '??', '[unknown]'] as $j => $unknown) {
                $record('transliterate-' . $i . '-' . (int) $strict . '-' . $j, 'to_transliterate', [$text, $unknown, $strict]);
            }
        }
        foreach (['en', 'de', 'el', 'my', 'tr', 'ru', 'unknown'] as $locale) {
            $record('ascii-' . $i . '-' . $locale, 'to_ascii', [$text, $locale]);
            $record('slug-' . $i . '-' . $locale, 'to_slugify', [$text, '-', $locale]);
        }
        $record('clean-' . $i, 'clean', [$text]);
    }
}
echo json_encode(['signatures' => $signatures, 'results' => $results], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
