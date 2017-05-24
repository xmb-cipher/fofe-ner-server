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

if ($1 == "eng") then
	set mod1 = "eng2016"
	set mod2 = "gw128-case-insensitive.wordlist"
	set mod3 = "gw128-case-sensitive.wordlist"

port = $2

${THIS_DIR}/server.py \
	"${THIS_DIR}/model/$mod1" \
	"${THIS_DIR}/model/$mod2" \
	"${THIS_DIR}/model/$mod3" \
	--port "$port" \
	--KBP \
|& tee ${THIS_DIR}/logs/${timestamp}
