<?php

require_once 'inc_globals.php';

function isUtf8_2() {
  return Patchwork\Utf8::isUtf8("Iñtërnâtiônàlizætiøn\xF0\x90\x8C\xBCIñtërnâtiônàlizætiøn");
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('isUtf8_1', 'isUtf8_2');
$b->report('isUtf8_2', 'isUtf8_2');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * isUtf8_1      0.02108097ms      165.9296875kb
 * isUtf8_2      0.02009106ms      64b
 */