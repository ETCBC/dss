import os
import pytest

from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype lex_etcbc sp_etcbc gn_etcbc vt_etcbc vs_etcbc lang_etcbc glyphe type g_cons
''')
api.loadLog()
api.makeAvailableIn(globals())

Fdss, Ldss = api.F, api.L

def test_word_count():
    assert len([w for w in F.otype.s('word')]) > 500_000

def test_lexemes_adjv_subs_verb_endings():
    assert all(Fdss.lex_etcbc.v(w)[-1] == '/' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) in {'adjv', 'subs', 'nmpr'})
    assert all(Fdss.lex_etcbc.v(w)[-1] == '[' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) == 'verb')

        
def test_lexemes_verb_endings_reversed():
    assert all((Fdss.sp_etcbc.v(w) == 'verb' for w in Fdss.otype.s('word') if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) and Fdss.lex_etcbc.v(w)[-1] == '['))


def test_allowed_values_for_feature_gn_etcbc():
    assert {Fdss.gn_etcbc.v(w) for w in Fdss.otype.s('word') if Fdss.gn_etcbc.v(w)} == {'NA', 'f', 'm', 'unknown'}

        
def test_allowed_values_for_feature_sp_etcbc():
    """Test for legal values of feature sp_etcbc."""
    assert {Fdss.sp_etcbc.v(w) for w in Fdss.otype.s('word')} == {'', 'adjv', 'advb', 'art', 'conj', 'inrg', 'intj', 'nega',
                                                                      'nmpr', 'prde', 'prep', 'prin', 'prps', 'subs', 'verb'}

        
def test_allowed_values_for_feature_vt_etcbc():
    """Test for legal values of feature vt_etcbc."""
    assert {Fdss.vt_etcbc.v(w) for w in Fdss.otype.s('word')} == {'NA', 'impf', 'impv', 'infa', 'infc', 'perf',
                                                                  'ptca', 'ptcp', 'unknown', 'wayq'}
 
      
def test_allowed_values_for_feature_vs_etcbc_hebrew():
    """Test for legal values of feature vt_etcbc."""
    assert {Fdss.vs_etcbc.v(w) for w in Fdss.otype.s('word') if Fdss.lang_etcbc.v(w) == 'Hebrew'} == {'NA', 'hif',
                            'hit', 'hitopel', 'hitpalpel', 'hof', 'hotp', 'hpealal', 'hsht', 'htpo', 'nif', 'nit',
                            'palel', 'pasq', 'peal', 'piel', 'pilpel', 'poal', 'poel', 'polal', 'polel', 'pual',
                            'pulal', 'qal', 'tif', 'unknown'}


def test_g_cons_is_equal_to_individual_cons():
    glued_cons_values = (''.join([Fdss.glyphe.v(s).upper() if Fdss.type.v(s) == 'cons' else '' for s in Ldss.d(w, 'sign')]) for w in Fdss.otype.s('word'))
    g_cons_values = (Fdss.g_cons.v(w) if Fdss.g_cons.v(w) else '' for w in Fdss.otype.s('word')) 
    for glued, g_cons in zip(glued_cons_values, g_cons_values):
        if glued and g_cons:
            assert len(glued) == len(g_cons)


if __name__ == '__main__':
    test_lexemes_adjv_subs_verb_endings()
