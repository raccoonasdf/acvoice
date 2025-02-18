#!/usr/bin/env python

from argparse import ArgumentParser
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile
import warnings

from parsy import (
    char_from, string, regex, decimal_digit,
    peek, success, fail,
    ParseError
)

from pydub import AudioSegment
from pydub.utils import get_player_name


# pytorch warning about unpickling possibly malicious models
warnings.filterwarnings('ignore', category=FutureWarning)
# pytorch warning about nested tensor
warnings.filterwarnings('ignore', category=UserWarning)


def phonemizer(model_path, supplemental_dict=None, lang='en_uk'):
    # DeepPhonemizer has a massive startup cost
    # so we defer import until we use it here
    from dp.phonemizer import Phonemizer
    phonemizer = Phonemizer.from_checkpoint(model_path)

    if supplemental_dict is not None:
        phonemizer.lang_phoneme_dict['en_uk'].update(
            supplemental_dict
            # voicebank letters
            | dict(zip('abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
    
    def phonemize(text: str):
        return phonemizer(text, lang=lang, punctuation='1234567890')

    return phonemize


def assert_result(p):
    return lambda res: success(res) if p(res) else fail('assert failed')

def word_end(c: str):
    match c:
        case 't' | 'd':
            return c+'o'
        case 'n':
            return 'nn'
        case _:
            return c+'u'

def parse_phonemes(ipa: str):
    pvowel = (
        string('ɒː').result('a')
        | string('əɹ').result('a')
        # sample overrides for if i ever make bare schwa contextual
        #| string('əː').result('a')
        #| (string('ə') << eof).result('a')

        | string('eɪ').result('e')

        #| string('ɔː').result('o') # oa?
        | string('əʊ').result('o')


        | string('æ').result('a')
        | string('a').result('a')
        | string('ɑ').result('a')
        | string('ʌ').result('a')
        | string('ɜ').result('a')
        # maybe make schwa smarter? might require spelling context though        
        | string('ə').result('a') 

        | string('i').result('i')
        # FALLBACK for consonant y        
        | string('j').result('i')
        | string('ɪ').result('i')

        | string('u').result('u')
        | string('ʊ').result('u')
        # FALLBACK for consonant w
        | string('w').result('u')
        
        | string('e').result('e')
        | string('ɛ').result('e')        

        | string('ɒ').result('o')
        | string('ɔ').result('o')
        | string('o').result('o')
    )

    pconsonant = (
        string('k').result('k')
        | string('s').result('s')
        | string('θ').result('s')
        | string('t').result('t')
        | string('n').result('n')
        | string('ŋ').result('n')
        | string('h').result('h')
        | string('f').result('h')
        | string('m').result('m')
        | (string('j')
            << peek(pvowel.bind(assert_result(lambda res: res in 'auo'))))
            .result('y')
        | string('r').result('r')
        | string('ɹ').result('r')
        | string('l').result('r')
        # deliberately omitting wo
        | (string('w')
            << peek(pvowel.bind(assert_result(lambda res: res == 'a'))))            
            .result('w') 

        | string('g').result('g')
        | string('ɡ').result('g')
        | string('z').result('z')
        | string('ð').result('z')
        | string('dʒ').result('z')
        | string('ʒ').result('z')
        | string('d').result('d')
        | string('b').result('b')
        | string('v').result('b')
        | string('p').result('p')
    )

    psyllable = (
        # use digit and letter words supplied from the voicebank
        decimal_digit | char_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        # approximate s- t- youon
        # (z- d- aren't convincing enough to be worth the extra syllable)
        | string('ʃ').result('si')
        | string('tʃ').result('ti')
        # CC: give the first consonant -u. don't consume the second yet
        | (pconsonant << peek(pconsonant)).map(lambda c: c+'u')
        # CV
        | (pconsonant + pvowel)
        # C: word-ending -u, -o, nn
        | pconsonant.map(word_end)
        # V
        | pvowel
        # ignore superfluous long
    ) << string('ː').optional()

    pword = psyllable.many()

    pwords = pword.sep_by(regex(r'[\s-]+'))


    # ignore some ipa combiners entirely
    for codepoint in [
          '329' # vertical line below
        , '32f' # inv breve below
        , '361' # double inv breve
    ]:
        ipa = ipa.replace(chr(int(codepoint, 16)), '')

    return pwords.parse(ipa)

def stitch_audio(voicebank_wordlist: list[list[str]],
                 voicebank_path,
                 clip_syllables_by_ms=0,
                 space_words_by_ms=0):
    audio = AudioSegment.empty()

    for word in voicebank_wordlist:
        for syl in word:
            sample = AudioSegment.from_wav(f'{voicebank_path}/{syl}.wav')
            audio = audio[:len(audio)-clip_syllables_by_ms] + sample

        audio += AudioSegment.silent(clip_syllables_by_ms+space_words_by_ms)

    return audio


expected_voicebank_samples = map(lambda name: name+'.wav', '''
     a  i  u  e  o
    ka ki ku ke ko
    sa si su se so
    ta ti tu te to
    na ni nu ne no
    ha hi hu he ho
    ma mi mu me mo
    ya    yu    yo
    ra ri ru re ro
    wa          wo    nn

    ga gi gu ge go
    za zi zu ze zo
    da di du de do
    ba bi bu be bo
    pa pi pu pe po
    
    0 1 2 3 4 5 6 7 8 9
    
    A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    '''.split())


def list_missing_voicebank_samples(voicebank_path):    
    missing = []
    for sample in expected_voicebank_samples:
        if not os.path.isfile(f'{voicebank_path}/{sample}'):
            missing.append(sample)
    
    return missing


def cli(args):
    from config import (
        CLIP_SYLLABLES_BY_MS, SPACE_WORDS_BY_MS, SPACE_LINES_BY_MS,
        SPACE_END_BY_MS, SUPPLEMENTAL_DICT, DEFAULT_VOICEBANK, PHONEMIZER_MODEL
    )


    interactive = sys.stdin.isatty()

    if args.out is not None:
        out = open(args.out, 'w+b')
    else:
        if interactive and not args.repl_dont_play:
            out = NamedTemporaryFile('w+b', suffix='.wav')
            print(f'no --out specified, using {out.name}')
        else:
            print('no --out specified')
            return
    

    if not os.path.isdir(DEFAULT_VOICEBANK):
        print(f'no voicebank at {DEFAULT_VOICEBANK}')
        return
    
    missing = list_missing_voicebank_samples(DEFAULT_VOICEBANK)
    if missing != []:
        for sample in missing:
            print(f'missing {DEFAULT_VOICEBANK}/{sample}')
        return

    if not os.path.isfile(PHONEMIZER_MODEL):
        print(f'missing phonemizer model at {PHONEMIZER_MODEL}')
        return

    phonemize = phonemizer(PHONEMIZER_MODEL, SUPPLEMENTAL_DICT)


    # non-interactive outputs the whole text at once
    # so should initialize the audio just once before the loop starts
    if not interactive:
        audio = AudioSegment.empty()

    first_loop = True
    while True:
        if first_loop:
            first_loop = False
        else:
            print('======')
            audio += AudioSegment.silent(SPACE_LINES_BY_MS)

        try:
            words = input('? ' if interactive else '')
        except EOFError:
            break
        except KeyboardInterrupt:
            return

        if words == '':
            continue
        
        # echo
        if not interactive:
            print(words)

        # "!lit" to supply already-phonemized input
        if words.startswith('!lit '):
            res = words[5:]
        else:
            try:
                res = phonemize(words)
            except RuntimeError:
                print('phonemizer failed to run for that input')
            print(res)

        try:
            parsed = parse_phonemes(res)
        except ParseError as e:
            print(f'unexpected {res[e.index]} at index {e.index}')
            continue

        parsed_str = ' '.join(''.join(word) for word in parsed)
        print(parsed_str)

        # interactive outputs line-by-line
        # so should reinitialize the audio every loop
        if interactive:
            audio = AudioSegment.empty()

        audio += stitch_audio(parsed,
                              DEFAULT_VOICEBANK,
                              clip_syllables_by_ms=CLIP_SYLLABLES_BY_MS,
                              space_words_by_ms=SPACE_WORDS_BY_MS)

        # interactive exports and plays the output every loop
        if interactive:
            audio += AudioSegment.silent(SPACE_END_BY_MS)
            audio.export(out.name, 'wav')

            if args.repl_dont_play == False:
                subprocess.call([get_player_name(),
                    "-nodisp", "-autoexit", "-hide_banner", out.name])    


    # non-interactive exports once
    if not interactive:
        audio += AudioSegment.silent(SPACE_END_BY_MS)
        audio.export(out.name, 'wav')
        

if __name__ == '__main__':
    parser = ArgumentParser(
        prog='ac-voice',
        description='take english text from stdin and emit animal crossing voice audio'
    )

    parser.add_argument('-o', '--out', metavar='PATH',
        help='store the output in wav format here')
    parser.add_argument('--repl-dont-play', action='store_true',
        help="don't autoplay in the repl, just produce the last line's output at --out")

    cli(parser.parse_args())
