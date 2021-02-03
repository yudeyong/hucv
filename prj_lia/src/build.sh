/usr/local/Cellar/python@3.7/3.7.8_1/bin/python3 setup.py sdist
cd dist

ls -r -F |grep -v "/$" | head -n 1 | xargs /usr/local/Cellar/python@3.7/3.7.8_1/bin/pip3 install --upgrade 


cd ..
