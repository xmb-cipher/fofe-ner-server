#!/eecs/research/asr/mingbin/python-workspace/hopeless/bin/python

import logging, cPickle, os
from fofe_mention_net import *
from io import BytesIO

logger = logging.getLogger( __name__ )



class fofe_ner_wrapper( object ):
    def __init__( self, args ):
        #####################
        # load 1st-pass model
        model1st = args.model1st
        config1 = mention_config()
        with open( '%s.config' % model1st, 'rb' ) as fp:
            config1.__dict__.update( cPickle.load(fp).__dict__ )
        mention_net_1st = fofe_mention_net( config1, None )
        mention_net_1st.fromfile( model1st )

        vocab1 = args.vocab1
        vocab2 = args.vocab2

        numericizer1_1st = vocabulary( 
            vocab1,
            config1.char_alpha, 
            False 
        )
        numericizer2_1st = vocabulary( 
            vocab2,
            config1.char_alpha, 
            True 
        )
        logger.info( '1st pass vocabulary loaded\n' )

        self.mention_net_1st = mention_net_1st
        self.config1st = config1
        self.numericizer1_1st = numericizer1_1st
        self.numericizer2_1st = numericizer2_1st

        #####################
        # load 2nd-pass model

        if args.model2nd is not None:
            # model2nd = os.path.join( this_dir, 'model', '2nd-pass-train-dev' )
            model2nd = args.model2nd
            config2 = mention_config()
            with open( '%s.config' % model2nd, 'rb' ) as fp:
                config2.__dict__.update( cPickle.load(fp).__dict__ )
            mention_net_2nd = fofe_mention_net( config2, None )
            mention_net_2nd.fromfile( model2nd )

            numericizer1_2nd = vocabulary( 
                vocab1,
                config2.char_alpha, 
                False,
                n_label_type = config2.n_label_type 
            )
            numericizer2_2nd = vocabulary( 
                vocab2,
                config2.char_alpha, 
                True,
                n_label_type = config2.n_label_type 
            )
            logger.info( '2nd pass vocabulary loaded\n' )

            self.has2nd = True
            self.mention_net_2nd = mention_net_2nd
            self.config2nd = config2
            self.numericizer1_2nd = numericizer1_2nd
            self.numericizer2_2nd = numericizer2_2nd 
            assert self.config1st.n_window == self.config2nd.n_window
            assert self.config1st.n_window == self.config2nd.n_window
            assert self.config1st.n_label_type == self.config2nd.n_label_type
        else:
            self.has2nd = False

        if args.gazetteer is None:
            self.gazetteer = [set()] * self.config1st.n_label_type
        else:
            pass


    def annotate( self, sentences, isDevMode = False ):
        # TODO ##
        # make decoding-algorithm and decoding-threshold as dev-option

        tbl_dev_1st = []
        raw1st = [ (s, [], [], []) for s in sentences ]
        data1st = batch_constructor( 
            raw1st,
            self.numericizer1_1st,
            self.numericizer2_1st,
            gazetteer = self.gazetteer,
            alpha = self.config1st.word_alpha,
            window = self.config1st.n_window,
            n_label_type = self.config1st.n_label_type,
            language = self.config1st.language
        )
        logger.info( 'data1st: ' + str(data1st) )

        prob1st = []
        for example in data1st.mini_batch_multi_thread( 
                            2560, False, 1, 1, self.config1st.feature_choice ):
            _, pi, pv = self.mention_net_1st.eval( example )
            prob1st.append(
                numpy.concatenate(
                    ( example[-1].astype(numpy.float32).reshape(-1, 1),
                      pi.astype(numpy.float32).reshape(-1, 1),
                      pv ),
                    axis = 1
                )
            )
        prob1st = numpy.concatenate( prob1st, axis = 0 )

        memory1st = BytesIO()
        numpy.savetxt( 
            memory1st, 
            prob1st, 
            fmt = '%d  %d' + '  %f' * (self.config1st.n_label_type + 1) 
        )
        memory1st.seek(0)
        logger.info( '1st-pass probability computed' )

        raw2nd = []
        for sent, table, estimate, actual in PredictionParser(
                iter(raw1st),
                memory1st,
                self.config1st.n_window,
                n_label_type = self.config1st.n_label_type
            ):
            estimate = sorted(
                decode( 
                    sent, 
                    estimate, 
                    table, 
                    [0.72, 0.72], # self.config1st.threshold,
                                # TODO: the threshold pair from dev-set doesn't seem good
                    self.config1st.algorithm
                )
            )

            if len(estimate) > 0:
                boe, eoe, coe = zip(*estimate)
            else:
                boe, eoe, coe = [], [], []
            tbl_dev_1st.append( table )
            raw2nd.append( (sent, boe, eoe, coe) )
        logger.info( 'result1st: %s' % str(raw2nd) )

        if not self.has2nd:
            if isDevMode:
                return raw2nd, [tbl_dev_1st]
            else:
                return raw2nd


        tbl_dev_2nd = []
        data2nd = batch_constructor( 
            raw2nd,
            self.numericizer1_2nd,
            self.numericizer2_2nd,
            gazetteer = [set()] * self.config2nd.n_label_type,
            alpha = self.config2nd.word_alpha,
            window = self.config2nd.n_window,
            is2ndPass = True,
            n_label_type = self.config2nd.n_label_type,
            language = self.config2nd.language
        )
        logger.info( 'data2nd: ' + str(data2nd) )

        prob2nd = []
        for example in data2nd.mini_batch_multi_thread( 
                            2560, False, 1, 1, self.config2nd.feature_choice ):
            _, pi, pv = self.mention_net_2nd.eval( example )
            prob2nd.append(
                numpy.concatenate(
                    ( example[-1].astype(numpy.float32).reshape(-1, 1),
                      pi.astype(numpy.float32).reshape(-1, 1),
                      pv ),
                    axis = 1
                )
            )
        prob2nd = numpy.concatenate( prob2nd, axis = 0 )
        prob2nd[:,2:] = 0.6 * prob1st[:,2:] + 0.4 * prob2nd[:,2:]
        prob2nd[:,1] = numpy.argmax( prob2nd[:,2:], axis = 1 ).astype( numpy.float32 )

        memory2nd = BytesIO()
        numpy.savetxt( 
            memory2nd, 
            prob2nd, 
            fmt = '%d  %d' + '  %f' * (self.config2nd.n_label_type + 1) 
        )
        memory2nd.seek(0)
        logger.info( '2nd-pass probability computed' )

        result = []
        for sent, table, estimate, actual in PredictionParser(
                iter(raw2nd),
                memory2nd,
                self.config2nd.n_window,
                n_label_type = self.config2nd.n_label_type
            ):
            estimate = sorted(
                decode( 
                    sent, 
                    estimate, 
                    table, 
                    0.4,
                    1 # highest first
                )
            )

            if len(estimate) > 0:
                boe, eoe, coe = zip(*estimate)
            else:
                boe, eoe, coe = [], [], []
            tbl_dev_2nd.append( table )
            result.append( (sent, boe, eoe, coe) )
        logger.info( 'result2nd: %s' % str(result) )

        if isDevMode:
            return result, [tbl_dev_1st, tbl_dev_2nd]
        else:
            return result


# Unit Test
if __name__ == '__main__':
    logging.basicConfig( format = '%(asctime)s : %(levelname)s : %(message)s', 
                         level = logging.INFO )
                         
    class test_args( object ):
        def __init__( self ):
            this_dir = '/eecs/research/asr/mingbin/ner-server'
            self.model1st = '%s/model/eng2016' % this_dir
            self.model2nd = None
            self.vocab1 = '%s/model/gw128-case-insensitive.wordlist' % this_dir
            self.vocab2 = '%s/model/gw128-case-sensitive.wordlist' % this_dir
            self.KBP = True
            self.gazetteer = None

    annotator = fofe_ner_wrapper( test_args() )

