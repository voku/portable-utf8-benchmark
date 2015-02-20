<?php

require_once 'inc_globals.php';

\Patchwork\Utf8\Bootup::initAll(); // Enables the portablity layer and configures PHP for UTF-8
\Patchwork\Utf8\Bootup::filterRequestUri(); // Redirects to an UTF-8 encoded URL if it's not already the case
\Patchwork\Utf8\Bootup::filterRequestInputs(); // Normalizes HTTP inputs to UTF-8 NFC

function substr_2() {
  return Patchwork\Utf8::substr('Iñ\ntërnâtiônàlizætiøn', 1, 5);
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('stripos_1', 'substr_2');
$b->report('stripos_2', 'substr_2');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * stripos_1     0.16444492ms      206.0078125kb
 * stripos_2     0.13729095ms      64b
 */