#!/usr/bin/env bash

# npm install -g aglio
# aglio -i api.apib -s

doc_path="$(dirname $(pwd))"

#aglio -i api.apib -o ${doc_path}/api.html

aglio -i api.apib -o api.html

find ${doc_path} -name '*.html' | xargs perl -pi -e 's|fonts.googleapis.com|fonts.lug.ustc.edu.cn|g'
find ${doc_path} -name '*.html' | xargs perl -pi -e 's|maxcdn.bootstrapcdn.com|cdn.bootcss.com|g'