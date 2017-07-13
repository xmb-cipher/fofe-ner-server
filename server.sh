#!/bin/bash

export THIS_DIR=$(cd $(dirname $0); pwd)
export CUDA_VISIBLE_DEVICES=''

[ ! -d ${THIS_DIR}/logs ] && mkdir -p ${THIS_DIR}/logs
timestamp=`date +"%Y-%m-%d-%H-%M-%S"`

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

${THIS_DIR}/server.py \
	"${THIS_DIR}/model/eng2016" \
	"${THIS_DIR}/model/gw128-case-insensitive.wordlist" \
	"${THIS_DIR}/model/gw128-case-sensitive.wordlist" \
	"/eecs/research/asr/Shared/ner-toolkit/CoreNLP" \
	"7000" \
	--KBP \
|& tee ${THIS_DIR}/logs/${timestamp}
