#!/bin/bash
find . -name loadfile -exec echo {} \; -exec cat {} \;
