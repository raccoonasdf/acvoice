'''
each syllable in a word cuts the previous syllable off by this amount

more of this gives more animal crossing energy
but makes the result less intelligible
'''
CLIP_SYLLABLES_BY_MS = 35


'''
add extra silence between words
'''
SPACE_WORDS_BY_MS = 0


'''
add extra silence between each line
'''
SPACE_LINES_BY_MS = 100


'''
add extra silence at the end of the clip.

ffplay might cut off the end if this is too low. silly
'''
SPACE_END_BY_MS = 175


'''
extra words for the phonemizer to recognize before it falls back to inference
EXAMPLE ENTRIES:
{
    # numerals and capital letters use the corresponding voicebank samples directly
    'brb': 'BRB',
    'go': '5',
    # outputs are run through the parser so you can use any IPA that it understands
    'bunytization': 'bʌnitaɪzeɪʃən',
    'pikapi': 'pikapi'
}
'''
SUPPLEMENTAL_DICT = {

}


'''
use the voicebank at this directory
'''
DEFAULT_VOICEBANK = 'voices/GAL'


'''
use the pretrained phonemizer model at this directory
'''
PHONEMIZER_MODEL = 'latin_ipa_forward.pt'