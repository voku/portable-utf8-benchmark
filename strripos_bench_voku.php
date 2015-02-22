<?php

require_once 'inc_globals.php';

function strripos_1() {
  return voku\helper\UTF8::strripos('DÉJÀ', 'à');
}

$b = new Benchmark;
$b->setIterations(1000);
$b->report('strripos_1', 'strripos_1');
$b->report('strripos_2', 'strripos_1');
$b->bench();

/**
 * IDENTIFIER    EXECUTION TIME    MEMORY USAGE
 * strripos_1    0.05818987ms      607.5703125kb
 * strripos_2    0.04428697ms      64b
 */