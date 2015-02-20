<?php

require_once 'inc_globals.php';

function isUtf8_1() {
  return voku\helper\UTF8::is_utf8("Iñtërnâtiônàlizætiøn\xF0\x90\x8C\xBCIñtërnâtiônàlizætiøn");
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('isUtf8_1', 'isUtf8_1');
$b->report('isUtf8_2', 'isUtf8_1');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * isUtf8_1      0.06521106ms      533.3203125kb
 * isUtf8_2      0.02959514ms      64b
 */