import hashlib
from pathlib import Path
from typing import Union, Tuple


def check_file_md5(file_path: Path, hashes: Union[str, list]) -> Tuple[str, bool]:
    if isinstance(hashes, str):
        hashes = [hashes]

    hash_md5 = hashlib.md5()

    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)

    file_hash = hash_md5.hexdigest()

    check_result = True if file_hash in hashes else False

    return file_hash, check_result
