import re
import warnings
from pathlib import Path
from typing import Callable, Optional, Any
import pickle

DEBUG = False # Whether to log or not
LOG_DIR =  Path.joinpath(Path(Path(__file__).parent), 'log/')

class Logger:
    def __init__(self, file: str = 'logs.log') -> None:
        if not DEBUG: return
        self.start = True
        self.file = Path.joinpath(LOG_DIR, file)
        if not Path.exists(LOG_DIR):
            Path.mkdir(LOG_DIR)
        if not LOG_DIR.is_dir():
            raise OSError('Logging directory is not a directory (maybe a file)')
    def log(self, *args, new_section=False, **kwargs):
        """
        Logs neatly. Makes an extra newline at the end. Use new_section
            if the logs should be separated more. Turned off if DEBUG is disabled
        """
        if not DEBUG: return
        with open(self.file, 'a') as fh:
            if new_section:
                print(f'\n{'-'*50}\n\n')
            if self.start:
                print(f'\n{'='*50}\n{'='*50}\n\n')
                self.start = False
            print(*args, **kwargs)
            print('\n')

class Recovery:
    def __init__(self, var: Any, file: Optional[str] = None) -> None:
        if not DEBUG: return
        self.var = var
        file = file or f'recovery_{Path(__file__).stem}'
        self.file = Path.joinpath(LOG_DIR, file)
    def __enter__(self):
        self.finished = False
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if (not DEBUG) or self.finished or exc_traceback is None: return
        PICKLE_EXT = 'pkl'

        file = str(self.file)
        # Find file path, don't overwrite
        while Path(f'{file}.{PICKLE_EXT}').exists():
            warnings.warn('Recovery file already exists - creating new file')
            suffix = re.match(r'.*\(([0-9]+)\)$', file)
            if suffix:
                num = suffix.group(1)
                file = f'{file[:-3]}({int(num)+1})'
            else:
                file = f'{file} (1)'
        # Save variable into pickle file
        with open(f'{file}.{PICKLE_EXT}', 'wb') as fh:
            self.pickle_file = pickle.Pickler(fh)
            msg = "Creating pickle file of important variable \
                    - force stop execution if it\'s taking \
                    too long"
            warnings.warn(msg, UserWarning)
            self.pickle_file.dump(self.var)

    def close_early(self):
        self.finished = True



log: Callable[..., None] = Logger().log

def main():
    x = ['1', 2]
    with Recovery(x) as fh:
        print('Hi')
        # fh.close_early()
        # raise RuntimeError('See this error')

if __name__ == '__main__':
    main()