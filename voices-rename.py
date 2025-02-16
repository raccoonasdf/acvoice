from os import listdir, makedirs
from shutil import copyfile

from acvoice import expected_voicebank_samples

for bank in ['BOY', 'GAL', 'MAN']:
    filenames_before = sorted(filter(lambda filename: bank in filename, listdir(f'voices_untitled')))

    filenames_after = expected_voicebank_samples

    filenames_trans = zip(filenames_before, filenames_after)

    for before, after in filenames_trans:
        print(f'{before} --> {after}')
        makedirs(f'voices/{bank}', exist_ok=True)
        copyfile(f'voices_untitled/{before}', f'voices/{bank}/{after}')
