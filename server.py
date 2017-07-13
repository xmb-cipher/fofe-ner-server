#!/eecs/research/asr/mingbin/python-workspace/hopeless/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from subprocess import call
import os, time, sys, argparse, logging, pandas
from subprocess import Popen
from pandas import DataFrame
from fofe_ner_wrapper import fofe_ner_wrapper
from langdetect import detect
from pycorenlp import StanfordCoreNLP
import pprint

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

cls2ner = ['PER', 'LOC', 'ORG', 'MISC']
app = Flask(__name__)

def inference_to_json(inference, score_matrix, non_escaped):
    """
    Converts the inference information into a JSON convertible data structure.
    :param inference: [(sentence, beginning of entity, end of entity,
                         entity names), (...)]
    :type inference: array, [(string, array of indices, array of indices,
                             array of strings), (...)]
    :param score_matrix: matrix containing either None or a tuple
                         (enitty name, score)
    :type score_matrix: array
    :param non_escaped: an array of arrays containing the non-escaped version
                        of the sentences
    :type non_escaped: 2d array
    :return: Returns the infomation in inference as a dictionary
    :rtype: dict
    """
    text, entities_new, offset, n_entities, comments, m = '', [], 0, 0, [], 0

    for sent, boe, eoe, coe in inference:
        acc_len = [offset]
        # non-escaped sentence
        out_sent = non_escaped[m]
        s = score_matrix[m]

        for w in out_sent:
            acc_len.append(acc_len[-1] + len(w) + 1)  # last exclusive

        text += u' '.join(out_sent) + u'\n'

        for i in range(len(boe)):
            word_slice = [acc_len[boe[i]], acc_len[eoe[i]] - 1]
            ent_score = s[boe[i]][eoe[i] - 1]
            if ent_score is not None:
                entities_new.append(['T%d' % n_entities,
                                     ent_score[0],
                                     [word_slice],
                                     "{0:.2f}".format(ent_score[1])  # score
                                     ])
                n_entities += 1

        # for the next sentence in the text
        offset = acc_len[-1]
        m += 1

    return {'text': text, 'entities': entities_new, 'comments': comments}

#===============================================================================
# FUNCTIONS FOR DEVELOPER MODE (not clean) - To remove later
#===============================================================================

def inference_to_json_dev_demo(inference, score_matrix):
    """
    Converts the inference information into a JSON convertible data structure.
    Same as inference_to_json() but does not convert to non-escaped.
    """
    text, entities, offset, n_entities = '', [], 0, 0
    comments = []

    n_entities = 0
    entities_new = []
    scores = []  # (slice, score)
    m = 0
    for sent, boe, eoe, coe in inference:
        # boe - beginning of entity (index)
        # eoe - end of entity (index)
        # coe - entity name
        acc_len = [offset]  # slice

        for w in sent:
            acc_len.append(acc_len[-1] + len(w) + 1)  # last exclusive

        s = score_matrix[m]
        logger.info("matrix: " + str(s))

        text += u' '.join(sent) + u'\n'

        for i in range(len(boe)):
            word_slice = [acc_len[boe[i]], acc_len[eoe[i]] - 1]
            logger.info("word slice: " + str(text[word_slice[0]:word_slice[1]]))
            ent_score = s[boe[i]][eoe[i] - 1]
            if ent_score is not None:
                logger.info("ent score : " + str(ent_score))
                entities_new.append(['T%d' % n_entities,
                                     ent_score[0],
                                     [word_slice],
                                     # ent_score[1]
                                     "{0:.2f}".format(ent_score[1])  # score
                                     ])
                scores.append([word_slice, "{0:.2f}".format(ent_score[1])])
                n_entities += 1


        # for the next sentence in the text
        offset = acc_len[-1]

        m += 1

    return {'text': text, 'entities': entities_new, 'comments': comments}



def inference_to_json_dev(inference, score_matrix):
    """
    Converts the inference information into a JSON convertible data structure.
    Returns all of the mentions detected without filtering by confidence.
    """
    text, entities, offset, n_entities = '', [], 0, 0
    comments = []

    n_entities = 0
    entities_new = []
    m = 0
    for sent, boe, eoe, coe in inference:
        # boe - beginning of entity (index)
        # eoe - end of entity (index)
        # coe - entity name
        acc_len = [offset]  # slice
        for w in sent:
            acc_len.append(acc_len[-1] + len(w) + 1)  # last exclusive

        text += u' '.join(sent) + u'\n'
        offset = acc_len[-1]

        # indices that contain a non-None value
        s = score_matrix[m]
        for i in range(len(s)):
            for j in range(len(s[i])):
                ent_score = s[i][j]  # tuple
                if ent_score is not None:
                    word_slice = [acc_len[i], acc_len[j + 1] - 1]
                    entities_new.append(['T%d' % n_entities,
                                         ent_score[0],
                                         [word_slice],
                                         # ent_score[1]
                                         "{0:.2f}".format(ent_score[1])  # score
                                         ])
                    n_entities += 1
        m += 1

    return {'text': text, 'entities': entities_new, 'comments': comments}

#===============================================================================

@app.route('/', methods=['GET'])
def home_page():
    """
    Renders the home page.
    """
    print(render_template(u"ner-home.html"))
    return render_template(u"ner-home.html")


@app.route('/', methods=['POST'])
def annotate():
    """
    Responds to the ajax request fired when user submits the text to be detected.
    Returns a JSON object: {'text': text, 'entities': entity info,
                             'lang': language of the text, 'notes': error notes}
    """

    mode = request.form['mode']
    text = request.form['text'].strip()
    selected = request.form['lang']
    notes = ""

    language = "eng"
    if selected == "Spanish":
        language = "spa"

    elif selected == "Chinese":
        language = "cmn"

    #-------------------------- Language detector ------------------------------
    elif selected == "Automatic":
        lang_detect = detect(text)
        if lang_detect not in ['en', 'es']: #Chinese (later): 'zh-cn', 'zh-tw'
            return jsonify({'text': "Language not found", 'entities': [],
                            'notes': "Language not supported."})

        english = (lang_detect == 'en') and (language == "eng")
        spanish = (lang_detect == 'es') and (language == "spa")
        chinese = (lang_detect[0:2] == "zh") and (language == "cmn")

        selected = "Chinese"
        if lang_detect == "en":
                selected, language = "English", "eng"
        elif lang_detect == "es":
                selected, language = "Spanish", "spa"

        notes = "Language detected: " + selected + "." 

    # =====================================================================================
    # Stanford CoreNLP
    # =====================================================================================

    nlp = StanfordCoreNLP('http://localhost:' + args.coreNLP_port)

    properties = {'annotators': 'tokenize,ssplit',
                  'outputFormat': 'json'}

    if language == 'cmn':
        properties['customAnnotatorClass.tokenize'] = 'edu.stanford.nlp.pipeline.ChineseSegmenterAnnotator'
        properties['tokenize.model'] = 'edu/stanford/nlp/models/segmenter/chinese/ctb.gz'
        properties['tokenize.sighanCorporaDict'] = 'edu/stanford/nlp/models/segmenter/chinese'
        properties['tokenize.serDictionary'] = 'edu/stanford/nlp/models/segmenter/chinese/dict-chris6.ser.gz'
        properties['tokenize.sighanPostProcessing'] = 'true'
        properties['ssplit.boundaryTokenRegex'] = urllib.quote_plus('[!?]+|[。]|[！？]+')
    elif language == 'spa':
        properties['tokenize.language'] = 'es'

    output = nlp.annotate(text, properties=properties)

    text_array = []
    non_esc_array = []
    sentences = output['sentences']
    for sent in sentences:
        new = []
        non_esc = []
        tokens = sent['tokens']
        for word in tokens:
            new.append(word['word'])
            non_esc.append(word['originalText'])
        text_array.append(new)
        non_esc_array.append(non_esc)

    # =====================================================================================

    text = text_array
    logger.info('text after split & tokenize: %s' % str(text))

    # DEMO MODE
    if mode == 'demo':
        # retrieve the MIDs from the csv file
        inference, score = annotator.annotate(text, isDevMode=True)

        logger.info("inference: " + str(inference))

        # Replace the offsets from the annotator with the offsets from Stanford



        if len(score) > 1:
            result = inference_to_json(inference, score[1], non_esc_array)
        else:
            result = inference_to_json(inference, score[0], non_esc_array)

        result['notes'] = notes

        result['mids'] = {}

    # DEVELOPER MODE
    elif mode == 'dev':
        inference, score = annotator.annotate(text, isDevMode=True)

        # contains the first pass info for sentences -  {"0": {text: ..., entities: ..., comments: ...}, "1": {...}}
        first_pass_shown = {}
        shown_contains = []
        first_pass_hidden = {}
        
        # First pass shown
        for i in range(len(inference)):
            inf = [inference[i]]
            matrix = [score[0][i]]
            fp = inference_to_json_dev_demo(inf, matrix)
            first_pass_shown[str(i)] = fp
            shown_contains.append(fp['entities'])

        # First pass hidden
        for i in range(len(inference)):
            inf = [inference[i]]
            matrix = [score[0][i]]
            fp = inference_to_json_dev(inf, matrix)

            if not all(x in first_pass_shown[str(i)]['entities'] for x in fp['entities']):
                shown = first_pass_shown[str(i)]['entities']
                hidden = fp['entities']
                inter = []
                for entity in hidden:
                    if entity not in shown:
                        inter.append(entity)
                fp['entities'] = inter
            first_pass_hidden[str(i)] = fp

        for i in range(len(first_pass_shown)):
            shown = first_pass_shown[str(i)]['entities']
            hid = first_pass_hidden[str(i)]['entities']
            print("first pass hidden: " + str(first_pass_hidden[str(i)]['entities']))
            for entity in shown:
                for hidden in hid:
                    if entity[1:] == hidden[1:]:
                        first_pass_hidden[str(i)]['entities'].remove(hidden)

        for i in range(len(first_pass_hidden)):
            [first_pass_hidden[str(i)]['entities'].remove(x) for x in first_pass_hidden[str(i)]['entities'] if len(x) == 0]

        # Second pass
        second_pass = "N/A"
        if len(score) > 1:
            second_pass_shown = {}
            second_pass_hidden = {}
            for i in range(len(inference)):
                inf = [inference[i]]
                matrix = [score[1][i]]
                fp = inference_to_json(inf, matrix)
                second_pass[str(i)] = fp

            # TODO: show inference step by step
            for j, i in enumerate(inference):
                n = len(i[0])
                pandas.set_option('display.width', 256)
                pandas.set_option('max_rows', n + 1)
                pandas.set_option('max_columns', n + 1)

                for s in score:
                    logger.info('\n%s' % str(DataFrame(
                        data=s[j],
                        index=range(n),
                        columns=range(1, n + 1)
                    )))

        result = {'first_pass_shown': first_pass_shown, 'first_pass_hidden': first_pass_hidden, 'second_pass': second_pass}

    # SOMETHING WENT WRONG
    else:
        result = {
            'text': 'SOMETHING GOES WRONG. PLEASE CONTACT XMB. ',
            'entities': []
        }

    return jsonify(result)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('model1st', type=str,
                        help='basename of model trained for 1st pass')
    parser.add_argument('vocab1', type=str,
                        help='case-insensitive word-vector for {eng,spa} or word-vector for cmn')
    parser.add_argument('vocab2', type=str,
                        help='case-sensitive word-vector for {eng,spa} or char-vector for cmn')
    parser.add_argument('coreNLP_path', type=str, help='Path to the Stanford CoreNLP folder.')
    parser.add_argument('coreNLP_port', type=str, help='set the localhost port to coreNLP_port.')
    parser.add_argument('--model2nd', type=str, default=None,
                        help='basename of model trained for 2nd pass')
    parser.add_argument('--KBP', action='store_true', default=False)
    parser.add_argument('--gazetteer', type=str, default=None)
    parser.add_argument('--port', type=int, default=20541)

    args = parser.parse_args()

    print(args)

    # cwd = os.getcwd() # current directory
    # os.chdir(args.coreNLP_path)
    # logger.info(args.coreNLP_path)
    # logger.info(args.coreNLP_port)

    # Popen(['java', '-mx4g', '-cp', '"*"',
    #  'edu.stanford.nlp.pipeline.StanfordCoreNLPServer', '-port',
    #   args.coreNLP_port, '-timeout', '15000'])

    # os.spawnl(os.P_NOWAIT, 'java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port ' + args.coreNLP_port + ' -timeout 15000')

    # os.chdir(cwd)

    if args.KBP:
        cls2ner = ['PER-NAME', 'ORG-NAME', 'GPE-NAME', 'LOC-NAME', 'FAC-NAME',
                   'PER-NOMINAL', 'ORG-NOMINAL', 'GPE-NOMINAL', 'LOC-NOMINAL', 'FAC-NOMINAL']

    annotator = fofe_ner_wrapper(args)

    app.run('0.0.0.0', args.port)


    