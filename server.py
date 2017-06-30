#!/eecs/research/asr/mingbin/python-workspace/hopeless/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from subprocess import Popen, PIPE
import os, time, sys, argparse, logging, pandas
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

PATH = "/local/scratch/nana/EL-GUI/ELdata/file_gen/"
FILENAME = "ENG_NW_0000"
FILE_EXT = ".nw.xml"
FILE_LIST = "/local/scratch/nana/EL-GUI/ELdata/src/eng.all.list"
INFO_PATH = "/local/scratch/nana/EL-GUI/ELdata/src/test.el.iflytek.eng.tab"
OUTPUT_PATH = "/local/scratch/nana/EL-GUI/ELdata/rst/edl.iNCML.tsv.name"
CANDIDATE_FILE = "/local/scratch/nana/EL-GUI/ELdata/rst/out.candidate.txt"


def inference_to_json(inference, score_matrix):
    """
    Converts the inference information into a JSON convertible data structure.
    :param inference: [(sentence, beginning of entity, end of entity, entity names), (...)]
    :type inference: array, [(string, array of indices, array of indices, array of strings), (...)]
    :param score_matrix: matrix containing either None or a tuple (enitty name, score)
    :type score_matrix: array
    :return: Returns the infomation in inference as a dictionary
    :rtype: dict
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
                    scores.append([word_slice, "{0:.2f}".format(ent_score[1])])
                    n_entities += 1
        m += 1

    return {'text': text, 'entities': entities_new, 'comments': comments}


def write_sentence_to_file(inference):
    """
    Writes the sentences from inference into the file FILE. Adds the path of the file into eng.all.list .
    :param inference: [(sentence, beginning of entity, end of entity, entity names), (...)]
    :type inference: array, [(string, array of indices, array of indices, array of strings), (...)]
    """
    filename = PATH + FILENAME + FILE_EXT
    file = open(filename, "w")

    for item in inference:
        sentence = " ".join(item[0]) + '\n'
        file.write(sentence.encode("utf8"))
    file.close()

    # Add filename into the eng.all.list
    file = open(FILE_LIST, "w")
    file.write(filename + '\n')
    file.close()


def add_spaces(text):
    """
    (Helper) Add spaces between commas and periods.
    """
    return text.replace(". ", " . ").replace(", ", " , ")


def write_info_to_file(text, entities):
    """
    Used to generate input for entity linking. Using text and the list of entities, write to INFO_PATH in the format:
    LDC     TEDL15_EVAL_000     mention     file_offset     ID_XXX     entity type      NAM     1.0     N   N   N:
    """
    text = add_spaces(text)
    file = open(INFO_PATH, "w")
    for item in entities:
        offset = item[2][0]
        etype = item[1]
        mention = text[offset[0]: offset[1]]
        file_offset = FILENAME + ":" + str(offset[0]) + "-" + str(offset[1])
        final = "LDC\tTEDL15_EVAL_0000" + "\t" + mention.encode(
            'utf8') + "\t" + file_offset + "\tID_XXX\t" + etype + "\tNAM\t1.0\tN\tN\tN\n"
        file.write(final)
    file.close()


def retrieve_linking_info():
    """
    After running the linking code, retrieve the output info, including mid, full mention, candidate mids and summary
    for each mention.
    :return: linking information for each mention
    :rtype: dict (mention: [mid: string, full_mention: string, candidates: array of strings, summary: string])
    """
    linking_info = {}
    file = open(OUTPUT_PATH, "r")

    for line in file:
        info = line.split("\t")
        text_mention = info[2]
        full_mention = info[8]
        if len(info) > 9:
            summary = info[9].strip('\n')
            summary = summary.strip()
        else:
            summary = "N/A"
        mid = info[4]
        if "NIL" in mid:
            mid = "Unknown"
        if "N/A" in full_mention:
            full_mention = text_mention
        candidates = retrieve_candidate_mids(text_mention)

        linking_info[text_mention] = [mid, full_mention, candidates, summary]
    return linking_info


def retrieve_candidate_mids(mention):
    """
    Retrieve the candidate MIDs for the given mention. They are located in CANDIDATE_FILE in a certain format.
    :param mention: The mention
    :type mention: str
    :return: The candidate MIDs
    :rtype: array of strings
    """
    file = open(CANDIDATE_FILE, "r")
    candidates = []
    for line in file:
        info = line.split("\t")
        text_mention = info[1]
        if mention == text_mention:
            candidates = info[5].strip('\n')
            candidates = candidates.split(" || ")
            candidates = [c.strip("[") for c in candidates]
            candidates = [c.strip("]") for c in candidates]
    return candidates


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
    Returns a JSON object: {'text': text, 'entities': entity info, 'lang': language of the text, 'notes': error notes}
    """
    start_time = time.time()
    mode = request.form['mode']
    text = request.form['text'].strip()
    selected = request.form['lang']
    notes = ""

    sentence = text

    language = "eng"
    if selected == "Spanish":
        language = "spa"

    elif selected == "Chinese":
        language = "cmn"

    # -------------------------- Language detector ---------------------------------

    lang_detect = detect(text)
    if lang_detect not in ['en', 'es', 'zh-cn', 'zh-tw']:
        return jsonify({'text': "Language not found", 'entities': [], 'notes': "Language not supported."})

    english = ((lang_detect == 'en') and (language == "eng"))
    spanish = ((lang_detect == 'es') and (language == "spa"))
    chinese = ((lang_detect[0:2] == "zh") and (language == "cmn"))

    if not (english or spanish or chinese):
        selected = "Chinese"
        if lang_detect == "en":
            selected = "English"
            language = "eng"
        elif lang_detect == "es":
            selected = "Spanish"
            language = "spa"

        notes = "Your selected language does not seem to match the language of the text." \
                " We will be assuming that the text is in " + selected + "."

    # =====================================================================================
    # Stanford CoreNLP
    # =====================================================================================

    nlp = StanfordCoreNLP('http://localhost:9000')

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

    pprint.pprint(output)

    text_array = []
    text_to_offset = {}
    sentences = output['sentences']
    for sent in sentences:
        new = []
        tokens = sent['tokens']
        for word in tokens:
            new.append(word['originalText'])
        if word['originalText'] not in text_to_offset:
            text_to_offset
        text_array.append(new)

    # =====================================================================================
    text = text_array
    logger.info('text after split & tokenize: %s' % str(text))

    # DEMO MODE
    if mode == 'demo':
        # retrieve the MIDs from the csv file
        start_time1 = time.time()
        inference, score = annotator.annotate(text, isDevMode=True)

        logger.info(inference)

        # Replace the offsets from the annotator with the offsets from Stanford



        print("ANNOTATOR.ANNOTATE TAKES %s SECONDS" % (time.time() - start_time1))

        # Linking part: Uncomment to use 
        # =============
        # if language == "eng":
        #     start_time2 = time.time()
        #     write_sentence_to_file(inference)
        #     print("WRITE_SENTENCE_TO_FILE TAKES %s SECONDS" % (time.time() - start_time2))

        start_time3 = time.time()
        if len(score) > 1:
            result = inference_to_json(inference, score[1])
        else:
            result = inference_to_json(inference, score[0])

        result['notes'] = notes
        print("DOC2JSONDEMO TAKES %s SECONDS" % (time.time() - start_time3))

        # Linking part: Uncomment to use 
        # =============
        # if language == "eng":
        #     start_time4 = time.time()
        #     write_info_to_file(sentence, result['entities'])
        #     print("WRITE INFO TO FILE TAKES %s SECONDS" % (time.time() - start_time4))

        #     # *******************************************************
        #     # UNCOMMENT TO GENERATE MID
        #     # *******************************************************
        #     # Delete the files in rst

        #     folder = '/local/scratch/nana/EL-GUI/ELdata/rst'
        #     for the_file in os.listdir(folder):
        #         file_path = os.path.join(folder, the_file)
        #         try:
        #             if os.path.isfile(file_path):
        #                 os.unlink(file_path)
        #         except Exception as e:
        #             print(e)

        #     os.chdir('/local/scratch/nana/EL-GUI/bin')

        #     # Run : sh /local/scratch/nana/EL-GUI/bin/run.sh
        #     command = ["csh", "/local/scratch/nana/EL-GUI/bin/run.sh"]

        #     p = Popen(command, stdout=PIPE, bufsize=1)
        #     while p.poll() is None:
        #         line = p.stdout.readline()
        #         print(line)

        #     os.chdir('/local/scratch/nana/fofe-ner-server')

        #     # *******************************************************

        #     # Retrieve MID
        #     start_time5 = time.time()
        #     mention_to_mid = retrieve_linking_info()
        #     print("RETRIEVE MIDS TAKES %s SECONDS" % (time.time() - start_time5))

        #     result['mids'] = mention_to_mid
        # else:
        #     result['mids'] = {}

        result['mids'] = {}

    # DEVELOPER MODE
    elif mode == 'dev':
        inference, score = annotator.annotate(text, isDevMode=True)

        # contains the first pass info for sentences -  {"0": {text: ..., entities: ..., comments: ...}, "1": {...}}
        first_pass = {}
        # First pass
        for i in range(len(inference)):
            inf = [inference[i]]
            matrix = [score[0][i]]
            fp = inference_to_json(inf, matrix)
            first_pass[str(i)] = fp

        # Second pass
        second_pass = "N/A"
        if len(score) > 1:
            second_pass = {}
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

        result = {'first_pass': first_pass, 'second_pass': second_pass}

    # SOMETHING WENT WRONG
    else:
        result = {
            'text': 'SOMETHING GOES WRONG. PLEASE CONTACT XMB. ',
            'entities': []
        }

    # # example output
    # result = jsonify({
    #     'text'     : "Ed O'Kelley was the man who shot the man who shot Jesse James.",
    #     'entities' : [
    #         ['T1', 'PER', [[0, 11]]],
    #         ['T2', 'PER', [[20, 23]]],
    #         ['T3', 'PER', [[37, 40]]],
    #         ['T4', 'PER', [[50, 61]]],
    #     ],
    # })

    print("TOTAL TAKES %s SECONDS" % (time.time() - start_time))
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
    parser.add_argument('--model2nd', type=str, default=None,
                        help='basename of model trained for 2nd pass')
    parser.add_argument('--KBP', action='store_true', default=False)
    parser.add_argument('--gazetteer', type=str, default=None)
    parser.add_argument('--port', type=int, default=20540)

    args = parser.parse_args()

    print(args)

    if args.KBP:
        cls2ner = ['PER-NAME', 'ORG-NAME', 'GPE-NAME', 'LOC-NAME', 'FAC-NAME',
                   'PER-NOMINAL', 'ORG-NOMINAL', 'GPE-NOMINAL', 'LOC-NOMINAL', 'FAC-NOMINAL']

    annotator = fofe_ner_wrapper(args)

    app.run('0.0.0.0', args.port)
