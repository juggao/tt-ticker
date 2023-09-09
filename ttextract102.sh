#!/bin/bash
start_tag="span class=\"yellow \""
end_tag="/span"
linestring=""
awk -F'[<>]' -v taga="$start_tag" -v tagb="$end_tag" '{
    for (i = 1; i <= NF; i++) {
        if ($(i) == taga) {
            linestring = $(i+1)
            if (match($(i+2), /a class="yellow" href="\/webplus\?/)) {
                linestring = linestring $(i+3)
            }    
            print linestring
            next
        } 
    }}'