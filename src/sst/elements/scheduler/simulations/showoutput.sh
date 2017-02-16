#!/bin/bash
find . -name "*.sim.time" -exec echo {} \; -exec cat {} \;
