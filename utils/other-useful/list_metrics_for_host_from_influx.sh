HostName="<DEFAULT_HOSTNAME>"
InfluxDB_host="<INFLUXDB_HOST>"
InfluxDB_port=8086
influx_db_name="<DB_NAME>"
tag_name=type
[ ! -z $1 ] && HostName=$1
ofile=metrics_from_${HostName}.json

curl -s -o $ofile "http://${InfluxDB_host}:${InfluxDB_port}/query?q=SHOW+TAG+VALUES+WITH+KEY+=+%22${tag_name}%22+WHERE+host+=+%27${HostName}%27&db=${influx_db_name}"

sed -i 's/],/]\n/g' $ofile && sed -ir 's/\[\|]\|{\|"\|}//g' $ofile && sed -ir 's/values://' $ofile

[ -z "$2" -a ! "$2" == "-s" ] && echo -e "Raw metrics list for host $HostName in InfluxDB (${InfluxDB_host}):\n----" && grep -v "results:series:name" $ofile

