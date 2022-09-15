import logging
import pytest

from tf.app import use
DSS = use('etcbc/dss:clone', checkout='clone', version='1.5', provenanceSpec=dict(moduleSpecs=[]))
Fdss, Ldss, Tdss = DSS.api.F, DSS.api.L, DSS.api.T


logging.basicConfig(
    filename='./logs/test_data_dss.log',
    level = logging.INFO,
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s')

def test_lexemes_nouns_ending():
    
    try:
        assert [Fdss.sp_etcbc.v(w)[-1] == '/' for w in Fdss.otype.s('word') if Fdss.sp_etcbc.v(w)]
        logging.info("Testing lexemes_nouns_ending: SUCCES")
    except AssertionError as err:
        logging.error("Testing lexemes_nouns_ending: there is at least one word without '/' at the end")
        raise err

if __name__ == "__main__":
    test_lexemes_nouns_ending()