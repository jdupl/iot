#/bin/bash
bower install

npm install
mv node_modules/n3-charts/ public/bower_components/n3-charts/
rmdir node_modules
