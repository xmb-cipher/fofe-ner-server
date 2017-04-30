#!/eecs/research/asr/mingbin/python-workspace/hopeless/bin/python

from flask import Flask, render_template,request, json, jsonify
from subprocess import Popen, PIPE, call
from pandas import DataFrame
from nltk.tokenize import sent_tokenize, word_tokenize
from fofe_ner_wrapper import fofe_ner_wrapper

import argparse, logging, pandas
logger = logging.getLogger( __name__ )


app = Flask(__name__)

def doc2json( doc ):
    cls2ner = [ 'PER', 'LOC', 'ORG', 'MISC' ]
    text, entities, offset, n_entities = '', [], 0, 0
    comments = []
    for sent, boe, eoe, coe in doc:
        acc_len = [ offset ]
        for w in sent:
            acc_len.append( acc_len[-1] + len(w) + 1 )

        for i in xrange(len(coe)):
            entities.append( [ 'T%d' % n_entities,
                               cls2ner[coe[i]],
                               [[ acc_len[boe[i]], acc_len[eoe[i]] - 1 ]] ] )
            comments.append( [ 'T%d' % n_entities,
                               'AnnotatorNotes',
                               'Feng is working on it' ] )
            n_entities += 1

        text += u' '.join( sent ) + u'\n'
        offset = acc_len[-1]

    return { 'text': text.encode('ascii', 'ignore'), 'entities': entities, 'comments' : comments }



@app.route('/', methods = ['GET'])
def homePage():
    print render_template( 'ner-home.html' )
    return render_template( 'ner-home.html' )


@app.route('/', methods = ['POST'] )
def annotate():
    mode = request.form['mode']

    text = request.form['text']
    logger.info( 'text-received: %s' % text )

    text = text.encode('ascii', 'ignore').strip()
    text = sent_tokenize( text )
    text = [ word_tokenize(t.strip()) for t in text ]
    logger.info( 'text after ssplit & tokenize: %s' % str(text) )

    if mode == 'demo':
        result = doc2json( annotator.annotate( text ) )
        logger.info( result )

    elif mode == 'dev':
        inference, score1st, score2nd = annotator.annotate( text, isDevMode = True )
        # TODO: show inference step by step
        for i, s1, s2 in zip( inference, score1st, score2nd ):
            n = len(i[0])
            pandas.set_option('display.width', 256)
            pandas.set_option('max_rows', n + 1)
            pandas.set_option('max_columns', n + 1)

            logger.info( '\n%s' % str(i) )
            logger.info( '\n%s' % str(DataFrame(
                data = s1,
                index = range(n),
                columns = range(1, n + 1)
            ) ) )
            logger.info( '\n%s' % str(DataFrame(
                data = s2,
                index = range(n),
                columns = range(1, n + 1)
            ) ) )

        result = doc2json( inference )
        logger.info( result )
    else:
        result = { 
            'text': 'SOMETHING GOES WRONG. PLEASE CONTACT XMB. ',
            'entities' : []
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

    return jsonify( result )



if __name__== '__main__':
    logging.basicConfig( format = '%(asctime)s : %(levelname)s : %(message)s', 
                         level = logging.INFO )

    # parser = argparse.ArgumentParser()
    # parser.add_argument( 'model1st', type = str, 
    #                      help = 'basename of model trained for 1st pass' )
    # parser.add_argument( 'model2nd', type = str,
    #                      help = 'basename of model trained for 2nd pass' )
    # args = parser.parse_args()
    # logger.info( str(args) + '\n' )

    annotator = fofe_ner_wrapper()

    app.run( '0.0.0.0', 20540 )
