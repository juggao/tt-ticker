#!/bin/bash
cyan_tag="span class=\"cyan \""
end_tag="/span"
green_tag="span class=\"green \""


awk -F'[<>]' -v taga="$green_tag" -v tagb="$cyan_tag" '{
    for (i = 1; i <= NF; i++) {
        field=$i
        if ($(i) == taga) {
            j=i+1
            field=$j
            sub(/[[:space:]]+$/, " ", field)
            sub(/^[[:space:]]+/, "", field)
            printf "%s  *** ", field
            next
        }
        if ($(i) == tagb) {
            j=i+1
            field=$j
            sub(/[[:space:]]+$/, " ", field)
            sub(/^[[:space:]]+/, "", field)
            if (sub(/\.$/, "", field)) {
                field = field " " 
            }
            gsub(/\./, ". ", field)
            printf "%s ", field
            next
        }
    } } '
