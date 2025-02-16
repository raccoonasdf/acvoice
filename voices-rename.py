from os import listdir, makedirs
from shutil import copyfile

for bank in ['BOY', 'GAL', 'MAN']:
    filenames_before = sorted(filter(lambda filename: bank in filename, listdir(f'voices_untitled')))

    filenames_after = '''
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
        '''.split()
    filenames_after = map(lambda n: n+'.wav', filenames_after)

    filenames_trans = zip(filenames_before, filenames_after)

    for before, after in filenames_trans:
        print(f'{before} --> {after}')
        makedirs(f'voices/{bank}', exist_ok=True)
        copyfile(f'voices_untitled/{before}', f'voices/{bank}/{after}')
