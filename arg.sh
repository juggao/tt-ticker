#!/bin/bash

echo "${@}"
BACKUPALL=""
BACKUPBIN=""
for arg in "${@}" ; do
  if [[ "${arg}" =~ "bin" ]] ; then
    echo "bin supplied"
    BACKUPALL=""
    BACKUPBIN="1"
  fi
done

echo $BACKUPALL


if [ -n "$BACKUPALL" ] || [ -n "$BACKUPBIN" ]; then
     echo "backup"
fi
 
while getopts ":a:" opt; do
  case $opt in
     a)
      echo "-a was triggered, Parameter: $OPTARG" >&2
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done
