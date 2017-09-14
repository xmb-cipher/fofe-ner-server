#!/bin/bash

export THIS_DIR=$(cd $(dirname $0); pwd)
export CUDA_VISIBLE_DEVICES=''

[ ! -d ${THIS_DIR}/logs ] && mkdir -p ${THIS_DIR}/logs
timestamp=`date +"%Y-%m-%d-%H-%M-%S"`
pathtocorenlp="/eecs/research/asr/Shared/ner-toolkit/CoreNLP"

# ${THIS_DIR}/server.py \
# 	"${THIS_DIR}/model/1st-pass-train-dev" \
# 	"${THIS_DIR}/model/reuters256-case-insensitive.wordlist" \
# 	"${THIS_DIR}/model/reuters256-case-sensitive.wordlist" \
# 	--model2nd "${THIS_DIR}/model/2nd-pass-train-dev"
# |& tee ${THIS_DIR}/logs/${timestamp}

NextPort () {
	netstat -atn | perl -0777 -ne \
		'@ports = /tcp.*?\:(\d+)\s+/imsg ;
		for $port (32768..61000) {
			if (!grep(/^$port$/, @ports)) {
				print $port;
				last
			}
		}'
}

echo $(NextPort)
portused=$(NextPort)
cd $pathtocorenlp

java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port $(NextPort) -timeout 15000 &

if [[ $1 == 'eng' ]]
then
	echo English model being generated...
	${THIS_DIR}/server.py \
		"${THIS_DIR}/model/eng2016" \
		"${THIS_DIR}/model/gw128-case-insensitive.wordlist" \
		"${THIS_DIR}/model/gw128-case-sensitive.wordlist" \
		"/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
		$portused \
		--KBP \
		--port 20541 \
	|& tee ${THIS_DIR}/logs/${timestamp}
elif [[ $1 == 'spa' ]]
then
	echo Spanish model being generated...
	${THIS_DIR}/server.py \
		"${THIS_DIR}/model/spa2016v1-0" \
		"${THIS_DIR}/model/spa-gw-case-insensitive.wordlist" \
		"${THIS_DIR}/model/spa-gw-case-sensitive.wordlist" \
		"/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
		$portused \
		--KBP \
		--port 20542 \
	|& tee ${THIS_DIR}/logs/${timestamp}
else
	echo Chinese model being generated...
	${THIS_DIR}/server.py \
		"${THIS_DIR}/model/cmn2016" \
		"${THIS_DIR}/model/wiki-cmn-char.wordlist" \
		"${THIS_DIR}/model/wiki-cmn-word.wordlist" \
		"/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
		$portused \
		--KBP \
		--port 20543 \
	|& tee ${THIS_DIR}/logs/${timestamp}
fi
