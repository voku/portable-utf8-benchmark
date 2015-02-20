<?php

require_once 'inc_globals.php';

function substr_1() {
  return voku\helper\UTF8::substr('Iñ\ntërnâtiônàlizætiøn', 1, 5);
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('stripos_1', 'substr_1');
$b->report('stripos_2', 'substr_1');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * stripos_1     0.15090108ms      607.25kb
 * stripos_2     0.05396914ms      64b
 */