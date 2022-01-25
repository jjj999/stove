# stove

## Installing

- python: >= 3.7

```
python -m pip install git+ssh://git@github.com/athnomedical/mygit.git
```

## Usage

### Writeing your configuration file

```python
# glm_config.py
import subprocess
from stove import StoveGileum

def launch_app(host: str, port: int) -> None:
    subprocess.run(["gunicorn", "e2e.app:app", "-b", f"{host}:{port}"])

glm = StoveGileum(fireable=launch_app)
```

### Launching with the hot-loader

```
# stove [PATH OF CONFIGURATION]
stove glm_config.py
```
