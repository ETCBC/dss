import logging
import pytest

from tf.app import use
DSS = use('etcbc/dss:clone', checkout='clone', version='1.7.7', provenanceSpec=dict(moduleSpecs=[]))
Fdss, Ldss, Tdss = DSS.api.F, DSS.api.L, DSS.api.T


logging.basicConfig(
    filename='./logs/test_data_dss.log',
    level = logging.INFO,
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s')


def test_lexemes_adjv_subs_verb_endings():
    try:
        assert all(Fdss.lex_etcbc.v(w)[-1] == '/' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) in {'adjv', 'subs'})
        assert all(Fdss.lex_etcbc.v(w)[-1] == '[' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) == 'verb')
        logging.info("Testing adjv_subs_verb_endings: SUCCES")
    except AssertionError as err:
        logging.error("Testing lexemes_nouns_ending: there is at least one word without '/' or '[' at the end")
        raise err
        
def test_lexemes_verb_endings_reversed():
    try:
        assert all((Fdss.sp_etcbc.v(w) == 'verb' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) and Fdss.lex_etcbc.v(w)[-1] == '['))
        logging.info("Testing verb_endings_reversed: SUCCES")
    except AssertionError as err:
        logging.error("Testing lexemes_verbs_ending_reversed: there is at least one word '[' at the end that is not a verb in sp_etcbc")
        raise err
        
def test_allowed_values_for_feature_gn_etcbc():
    try:
        assert {Fdss.gn_etcbc.v(w) for w in Fdss.otype.s('word') if Fdss.gn_etcbc.v(w)} == {'NA', 'f', 'm', 'unknown'}
        logging.info("Testing allowed_values_for_feature_gn_etcbc: SUCCES")
    except AssertionError as err:
        logging.error("Testing allowed_values_for_feature_gn_etcbc: there is at least one illegal value")
        raise err
        
def test_allowed_values_for_feature_sp_etcbc():
    """Test for legal values of feature sp_etcbc."""
    try:
        assert {Fdss.sp_etcbc.v(w) for w in Fdss.otype.s('word')} == {'', 'adjv', 'advb', 'art', 'conj', 'inrg', 'intj', 'nega',
                                                                      'nmpr', 'prde', 'prep', 'prin', 'prps', 'subs', 'verb'}
        logging.info("Testing allowed_values_for_feature_sp_etcbc: SUCCES")
    except AssertionError as err:
        logging.error("Testing allowed_values_for_feature_sp_etcbc: there is at least one illegal value")
        raise err
        
def test_allowed_values_for_feature_vt_etcbc():
    """Test for legal values of feature vt_etcbc."""
    try:
        assert {Fdss.vt_etcbc.v(w) for w in Fdss.otype.s('word')} == {'NA', 'impf', 'impv', 'infa', 'infc', 'perf',
                                                                      'ptca', 'ptcp', 'unknown', 'wayq'}
        logging.info("Testing allowed_values_for_feature_vt_etcbc: SUCCES")
    except AssertionError as err:
        logging.error("Testing allowed_values_for_feature_vt_etcbc: there is at least one illegal value")
        raise err
      
def test_allowed_values_for_feature_vs_etcbc_hebrew():
    """Test for legal values of feature vt_etcbc."""
    try:
        assert {Fdss.vs_etcbc.v(w) for w in Fdss.otype.s('word') if Fdss.lang_etcbc.v(w) == 'Hebrew'} == {'NA', 'hif',
                            'hit', 'hitopel', 'hitpalpel', 'hof', 'hotp', 'hpealal', 'hsht', 'htpo', 'nif', 'nit',
                            'palel', 'pasq', 'peal', 'piel', 'pilpel', 'poal', 'poel', 'polal', 'polel', 'pual',
                            'pulal', 'qal', 'tif', 'unknown'}
        logging.info("Testing allowed_values_for_feature_vs_etcbc: SUCCES")
    except AssertionError as err:
        logging.error("Testing allowed_values_for_feature_vs_etcbc: there is at least one illegal value")
        raise err

if __name__ == "__main__":
    test_lexemes_adjv_subs_verb_endings()
    test_lexemes_verb_endings_reversed()
    test_allowed_values_for_feature_gn_etcbc()
    test_allowed_values_for_feature_sp_etcbc()
    test_allowed_values_for_feature_vt_etcbc()
    test_allowed_values_for_feature_vs_etcbc_hebrew()