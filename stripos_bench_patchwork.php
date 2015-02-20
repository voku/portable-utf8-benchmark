<?php

require_once 'inc_globals.php';

\Patchwork\Utf8\Bootup::initAll(); // Enables the portablity layer and configures PHP for UTF-8
\Patchwork\Utf8\Bootup::filterRequestUri(); // Redirects to an UTF-8 encoded URL if it's not already the case
\Patchwork\Utf8\Bootup::filterRequestInputs(); // Normalizes HTTP inputs to UTF-8 NFC

function stripos_2() {
  return Patchwork\Utf8::stripos('ABC-ÖÄÜ-中文空白-中文空白', "ö");
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('stripos_1', 'stripos_2');
$b->report('stripos_2', 'stripos_2');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * stripos_1     0.28511405ms      206.09375kb
 * stripos_2     0.29652214ms      64b
 */