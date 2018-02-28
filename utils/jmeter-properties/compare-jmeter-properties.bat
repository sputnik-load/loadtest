mkdir props-original
mkdir props-current
rm -f props-original\* props-current\*
cp -av C:\apache-jmeter-2.12-orig\bin\*.properties props-original
cp -av C:\apache-jmeter-2.12-orig\bin\*.parameters props-original
cp -av C:\apache-jmeter-2.12\bin\*.properties props-current
cp -av C:\apache-jmeter-2.12\bin\*.parameters props-current
diff -ruN props-original props-current > jmeter-properties.diff
rm -rf props-original props-current
