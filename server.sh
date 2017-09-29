#!/bin/bash

set -e

export THIS_DIR=$(cd $(dirname $0); pwd)
export CUDA_VISIBLE_DEVICES=''

[ ! -d ${THIS_DIR}/logs ] && mkdir -p ${THIS_DIR}/logs
timestamp=`date +"%Y-%m-%d-%H-%M-%S"`
pathtocorenlp="/eecs/research/asr/Shared/ner-toolkit/CoreNLP"

# ${THIS_DIR}/server.py \
#   "${THIS_DIR}/model/1st-pass-train-dev" \
#   "${THIS_DIR}/model/reuters256-case-insensitive.wordlist" \
#   "${THIS_DIR}/model/reuters256-case-sensitive.wordlist" \
#   --model2nd "${THIS_DIR}/model/2nd-pass-train-dev"
# |& tee ${THIS_DIR}/logs/${timestamp}

function NextPort {
    netstat -atn | perl -0777 -ne \
        '@ports = /tcp.*?\:(\d+)\s+/imsg ;
        for $port (32768..61000) {
            if (!grep(/^$port$/, @ports)) {
                print $port;
                last
            }
        }'
}


portused=$(NextPort)

cd ${pathtocorenlp}
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port ${portused} -timeout 15000 &
corenlp_pid=$!
trap "kill -9 ${corenlp_pid} &> /dev/null" EXIT

if [[ $1 == 'eng' ]]
then
    echo English model being generated...
    ${THIS_DIR}/server.py \
        "${THIS_DIR}/model/eng2017v1-0" \
        "${THIS_DIR}/model/eng2017v1-0-case-insensitive.wordlist" \
        "${THIS_DIR}/model/eng2017v1-0-case-sensitive.wordlist" \
        "/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
        ${portused} \
        --KBP \
        --port 20541 \
        --gazetteer "${THIS_DIR}/model/gaz.pkl" \
    |& tee ${THIS_DIR}/logs/eng-${timestamp}
elif [[ $1 == 'spa' ]]
then
    echo Spanish model being generated...
    ${THIS_DIR}/server.py \
        "${THIS_DIR}/model/spa2017v1-0" \
        "${THIS_DIR}/model/spa2017v1-0-case-insensitive.wordlist" \
        "${THIS_DIR}/model/spa2017v1-0-case-sensitive.wordlist" \
        "/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
        ${portused} \
        --KBP \
        --port 20542 \
        --gazetteer "${THIS_DIR}/model/gaz.pkl" \
    |& tee ${THIS_DIR}/logs/spa-${timestamp}
else
    echo Chinese model being generated...
    ${THIS_DIR}/server.py \
        "${THIS_DIR}/model/cmn2017v1-0" \
        "${THIS_DIR}/model/cmn2017v1-0-char.wordlist" \
        "${THIS_DIR}/model/cmn2017v1-0-word.wordlist" \
        "/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
        ${portused} \
        --KBP \
        --port 20543 \
        --gazetteer "${THIS_DIR}/model/gaz.pkl" \
        --wubi "${THIS_DIR}/model/cmn2017v1-0.wubi" \
    |& tee ${THIS_DIR}/logs/cmn-${timestamp}
fi
