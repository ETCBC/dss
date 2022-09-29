import logging
import pytest

from tf.app import use
DSS = use('etcbc/dss:clone', checkout='clone', version='1.6', provenanceSpec=dict(moduleSpecs=[]))
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


if __name__ == "__main__":
    test_lexemes_nouns_ending()