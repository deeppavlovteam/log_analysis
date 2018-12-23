import re
from pathlib import Path


jupyter_config_path = Path('~/.jupyter/jupyter_notebook_config.py').expanduser().resolve()

with jupyter_config_path.open('r') as f:
    jupyter_config = f.read()

jupyter_config = re.sub(pattern=r'#c\.NotebookApp\.allow_remote_access = False',
                        repl='c.NotebookApp.allow_remote_access = True',
                        string=jupyter_config)

jupyter_config = re.sub(pattern=r'#c\.NotebookApp\.ip = \'localhost\'',
                        repl='c.NotebookApp.ip = \'0.0.0.0\'',
                        string=jupyter_config)

with jupyter_config_path.open('w') as f:
    f.write(jupyter_config)

print('done')
