#!/bin/bash
start_tag="span class=\"cyan \""
end_tag="/span"
intarget=0
linestring=""
awk -F'[<>]' -v taga="$start_tag" -v tagb="$end_tag" '{
    for (i = 1; i <= NF; i++) {
        if ($(i) == taga) {
            linestring = $(i+1)
            if (match($(i+2), /a class="cyan" href="\/webplus\?/)) {
                linestring = linestring $(i+3)
                linestring = linestring $(i+5)
            }    
            print linestring
            next
        } 
    }}'