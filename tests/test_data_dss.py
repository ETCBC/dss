import os
import re
import pytest

from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype lex_etcbc sp_etcbc gn_etcbc vt_etcbc vs_etcbc lang_etcbc glyphe type g_cons g_lex_etcbc g_nme_etcbc g_prs_etcbc g_vbe_etcbc g_pfm_etcbc g_vbs_etcbc uvf_etcbc morph_etcbc
    scroll lex_utf8_etcbc
''')
api.loadLog()
api.makeAvailableIn(globals())

Fdss, Ldss = api.F, api.L

PARSED_SCROLLS = ('11Q19', '1Qisaa', '1QpHab', '1QS', '1QM', '1QHa')
MORPHEME_FEATURES = ('g_cons', 'g_pfm_etcbc', 'g_vbs_etcbc', 'g_lex_etcbc', 'g_vbe_etcbc',
                     'g_nme_etcbc', 'uvf_etcbc', 'g_prs_etcbc')


def parsed_scroll_words():
    for s in Fdss.otype.s('scroll'):
        if Fdss.scroll.v(s) in PARSED_SCROLLS:
            yield from Ldss.d(s, 'word')


def cons_signs(w):
    return ''.join(Fdss.glyphe.v(s).upper() for s in Ldss.d(w, 'sign') if Fdss.type.v(s) == 'cons')

def test_word_count():
    assert len([w for w in Fdss.otype.s('word')]) > 500_000

def test_lexemes_adjv_subs_verb_endings():
    bad = [w for w in Fdss.otype.s('word')
            if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) in {'adjv', 'subs', 'nmpr'}
            and Fdss.lex_etcbc.v(w)[-1] != '/']

    assert not bad, f"Failing word nodes: {bad}"
    bad = [w for w in Fdss.otype.s('word')
            if Fdss.lex_etcbc.v(w) and Fdss.sp_etcbc.v(w) == 'verb'
            and Fdss.lex_etcbc.v(w)[-1] != '[']

    assert not bad, f"Failing word nodes: {bad}"

        
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
    """Test for legal values of feature vs_etcbc.

    Since 2.0.4 the stems follow the BHSA: polel, pilpel, hitpolel etc. are piel, hitpael etc.
    """
    assert {Fdss.vs_etcbc.v(w) for w in Fdss.otype.s('word') if Fdss.lang_etcbc.v(w) == 'Hebrew'} <= {'NA', 'hif',
                            'hit', 'hof', 'hotp', 'hpealal', 'hsht', 'htpo', 'nif', 'nit',
                            'pasq', 'peal', 'piel', 'poal', 'poel', 'pual', 'qal', 'tif', 'unknown'}


def test_g_cons_is_equal_to_individual_cons():
    glued_cons_values = (''.join([Fdss.glyphe.v(s).upper() if Fdss.type.v(s) == 'cons' else '' for s in Ldss.d(w, 'sign')]) for w in Fdss.otype.s('word'))
    g_cons_values = (Fdss.g_cons.v(w) if Fdss.g_cons.v(w) else '' for w in Fdss.otype.s('word')) 
    for glued, g_cons in zip(glued_cons_values, g_cons_values):
        if glued and g_cons:
            assert len(glued) == len(g_cons)

def test_morphemes_add_up_to_g_cons():
    for w in Fdss.otype.s('word'):
        g_cons = Fdss.g_cons.v(w)
        lex_etcbc = Fdss.lex_etcbc.v(w)
        morph_etcbc = Fdss.morph_etcbc.v(w) or ''

        if not g_cons:
            continue
        if lex_etcbc == '=':
            continue
        if '-' in morph_etcbc and '(H' not in morph_etcbc: #skipt alleen de genoemde W-&B=
            continue

        reconstructed = (
            (Fdss.g_pfm_etcbc.v(w) or '') +
            (Fdss.g_vbs_etcbc.v(w) or '') +
            (Fdss.g_lex_etcbc.v(w) or '') +
            (Fdss.g_vbe_etcbc.v(w) or '') +
            (Fdss.g_nme_etcbc.v(w) or '') +
            (Fdss.uvf_etcbc.v(w)   or '') +
            (Fdss.g_prs_etcbc.v(w) or '')
        )

        assert reconstructed == g_cons, (
            f"Word {w}: reconstructed '{reconstructed}' != g_cons '{g_cons}'"
        )

def realise(morph):
    """The consonants of a morph string, as in programs/morphemes.py."""
    morph = re.sub(r":[a-z]+", "", morph)
    morph = re.sub(r"\([A-Z<>]", "", morph)
    return re.sub(r"[^A-Z<>]", "", morph)


def test_morph_etcbc_realises_g_cons_in_1Qisaa():
    """morph_etcbc of 1Qisaa realises g_cons (2.0.5, programs/fixMorph1Qisaa.py)."""
    scroll = [s for s in Fdss.otype.s('scroll') if Fdss.scroll.v(s) == '1Qisaa'][0]
    bad = [(w, Fdss.morph_etcbc.v(w), Fdss.g_cons.v(w)) for w in Ldss.d(scroll, 'word')
           if Fdss.morph_etcbc.v(w) and Fdss.g_cons.v(w)
           and realise(Fdss.morph_etcbc.v(w)) != Fdss.g_cons.v(w)]

    assert not bad, f"Failing word nodes: {bad}"


def test_parsed_words_have_g_cons():
    bad = [w for w in parsed_scroll_words()
           if Fdss.morph_etcbc.v(w) and cons_signs(w) and not Fdss.g_cons.v(w)]

    assert not bad, f"Failing word nodes: {bad}"


def test_g_cons_agrees_with_signs_in_parsed_scrolls():
    """The scroll has # for both shin and sin."""
    def agrees(g_cons, signs):
        return len(g_cons) == len(signs) and all(
            c == s or (s == '#' and c in 'CF') for c, s in zip(g_cons, signs))

    bad = [w for w in parsed_scroll_words()
           if Fdss.g_cons.v(w) and not agrees(Fdss.g_cons.v(w), cons_signs(w))]

    assert not bad, f"Failing word nodes: {bad}"


def test_morpheme_features_are_in_transliteration():
    bad = [(w, f) for w in parsed_scroll_words() for f in MORPHEME_FEATURES
           if any('\u0590' <= c <= '\u05ff' for c in (getattr(Fdss, f).v(w) or ''))]

    assert not bad, f"Failing word nodes: {bad}"


def test_lexemes_have_lex_utf8_in_parsed_scrolls():
    bad = [(w, Fdss.lex_etcbc.v(w)) for w in parsed_scroll_words()
           if Fdss.lex_etcbc.v(w) not in {None, '', '='} and not Fdss.lex_utf8_etcbc.v(w)]

    assert not bad, f"Failing word nodes: {bad}"


def test_1QpHab_is_parsed():
    """All words of 1QpHab with legible consonants have a parse (version 2.0.3)."""
    scroll = [s for s in Fdss.otype.s('scroll') if Fdss.scroll.v(s) == '1QpHab'][0]
    words = Ldss.d(scroll, 'word')
    bad = [w for w in words if cons_signs(w) and not Fdss.morph_etcbc.v(w)]

    assert not bad, f"Failing word nodes: {bad}"
    assert sum(1 for w in words if Fdss.morph_etcbc.v(w)) == 1874


def test_verbs_have_stem_and_tense_in_parsed_scrolls():
    bad = [w for w in parsed_scroll_words()
           if Fdss.sp_etcbc.v(w) == 'verb' and Fdss.scroll.v(Ldss.u(w, 'scroll')[0]) == '1QpHab'
           and (Fdss.vs_etcbc.v(w) in {None, '', 'NA'} or Fdss.vt_etcbc.v(w) in {None, '', 'NA'})]

    assert not bad, f"Failing word nodes: {bad}"


BHSA_STEMS = {'NA', 'unknown', 'qal', 'nif', 'piel', 'pual', 'hit', 'hif', 'hof', 'hsht',
              'hotp', 'pasq', 'poel', 'poal', 'tif', 'nit', 'htpo'}


def test_parsed_scrolls_follow_bhsa_stems_and_participles():
    """Polel, hitpolel etc. are piel, hitpael etc.; passive stems have passive participles."""
    bad = [w for w in parsed_scroll_words()
           if Fdss.morph_etcbc.v(w) and (
               Fdss.vs_etcbc.v(w) not in BHSA_STEMS
               or (Fdss.vt_etcbc.v(w) == 'ptca' and Fdss.vs_etcbc.v(w) in {'pual', 'hof', 'pasq'}))]

    assert not bad, f"Failing word nodes: {bad}"


if __name__ == '__main__':
    test_lexemes_adjv_subs_verb_endings()
