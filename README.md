little thing that converts english text into animal crossing voice sounds.

here's what it does, with an example roughly approximating the procedure:
1. start with user input  
   `bunny world`
2. use [DeepPhonemizer](https://github.com/as-ideas/DeepPhonemizer) to turn user input into IPA  
   `bʌni wɜːld`
3. parse the IPA into animal crossing voicebank samples (which consist of arabic numerals, latin letters, and japanese moras)  
   `[[b a n i] [w a r d]]`  
   `[[ba ni] [wa ru do]]`
4. stitch together the audio samples and play the resulting sound!  
   `🎵`

sorry about the code


get this thing working
---

look at `requirements.txt` and install those things. pytorch cannot be 2.6 because DeepPhonemizer doesn't pass `weights_only=False` to `torch.load`. i could probably fix this by forking DeepPhonemizer or copying the implementation of `load_checkpoint` into my code, but i don't really want to.

if you don't already have pytorch installed, may i suggest specifically pulling the cpu-only package from their site like this:  
`pip install torch~=2.5.0 --index-url https://download.pytorch.org/whl/cpu`  
so that you don't have to download one quadrillion nvidia packages you don't need. otherwise `pip install -r requirements.txt` is fine for the rest of the packages

you need to prepare a voicebank at a location specified in `config.py` (the default is `voices/GAL`). it should be a collection of wav files named `[0-9].wav`, `[A-Z].wav`, `[kgsztdnhbpmyrw]?[aiueo].wav`.

[here's a link to an audio rip from New Leaf by someone called JJ314](https://www.sounds-resource.com/3ds/animalcrossingnewleaf/sound/34689/). if you download that and extract it to a subdirectory called `voices_untitled` in this directory, you can run the provided `voices-rename.py` to receive three voicebanks BOY, GAL, and MAN.

now, you need a model for [DeepPhonemizer](https://github.com/as-ideas/DeepPhonemizer). this has been tested exclusively with their provided pretrained model `latin_ipa_forward.pt` in `en_uk` (find it in their README). the code expects that file with that name in the current directory, but you can change it in `config.py`.

if you want to use another language, or a model trained on american english, you'll surely have to make some serious alterations to my translation layer. the translation rules are tuned to what the aforementioned model emits and nothing more.


using it
---

there's a little sample CLI included if you run `acvoice.py` directly. use `--help` for more information. you need `ffplay` installed to get the repl to produce audio.

if you want to use it programmatically, you can import it and
1. `phonemizer` to turn english text into IPA
2. `parse_phonemes` to turn IPA into a voicebank wordlist
3. `stitch_audio` to turn a voicebank wordlist into a pydub AudioSegment
4. do whatever you want after that

i have deliberately restricted my use of the `config.py` to the sample CLI. if you import as a library, you don't need it and the API will not use its values.
