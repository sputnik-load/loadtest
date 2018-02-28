cat $1 | grep -vF '"POST' | sed -e "s/^.*\"\(GET [^=]*=*\).*HTTP\/1.*$/\1/g" | sort | uniq -c | sort -rn > "$1-top.log"
