<?php

require_once 'inc_globals.php';

\Patchwork\Utf8\Bootup::initAll(); // Enables the portablity layer and configures PHP for UTF-8
\Patchwork\Utf8\Bootup::filterRequestUri(); // Redirects to an UTF-8 encoded URL if it's not already the case
\Patchwork\Utf8\Bootup::filterRequestInputs(); // Normalizes HTTP inputs to UTF-8 NFC

function strripos_2() {
  return Patchwork\Utf8::strripos('DÉJÀ', 'à');
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('strripos_1', 'strripos_2');
$b->report('strripos_2', 'strripos_2');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * strripos_1    0.26573801ms      206.03125kb
 * strripos_2    0.22766900ms      64b
 */