<?php

require_once 'inc_globals.php';

function stripos_1() {
  return voku\helper\UTF8::stripos('ABC-ÖÄÜ-中文空白-中文空白', "ö");
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('stripos_1', 'stripos_1');
$b->report('stripos_2', 'stripos_1');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * stripos_1     0.10732102ms      607.390625kb
 * stripos_2     0.08857107ms      64b
 */