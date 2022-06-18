#!/bin/bash
start_tag="span class=\"cyan \""
end_tag="/span"
awk -F'[<>]' -v taga="$start_tag" -v tagb="$end_tag" '{ i=1; while (i<=NF) { if ($(i)==taga && $(i+2)==tagb) { print $(i+1) }; i++} }'
