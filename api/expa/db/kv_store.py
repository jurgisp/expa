import io
from pathlib import Path
from typing import Protocol

import numpy as np


class KVStore(Protocol):
  def write_tensors_data(
    self,
    data: dict[str, np.ndarray],
    pid: int,
    xid: int,
    rid: int,
    mids: dict[str, int],
    step: int,
  ): ...


class FileKVStore:
  def __init__(self, root_dir: str | Path):
    self.root_dir = Path(root_dir)  # TODO: GCS
    self.root_dir.mkdir(parents=True, exist_ok=True)

  def write_tensors_data(
    self,
    data: dict[str, np.ndarray],
    pid: int,
    xid: int,
    rid: int,
    mids: dict[str, int],
    step: int,
  ):
    for key, value in data.items():
      self._write_tensor_data(value, xid, rid, mids[key], step)

  def _write_tensor_data(
    self,
    data: np.ndarray,
    xid: int,
    rid: int,
    mid: int,
    step: int,
  ):
    path = self.root_dir / str(xid) / str(rid) / str(mid) / f"{step}.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    save_npz(dict(data=data), path)


def save_npz(data: dict[str, np.ndarray], path: Path):
  # Save to memory buffer first
  with io.BytesIO() as f1:
    np.savez_compressed(f1, **data)
    f1.seek(0)
    # Then copy to file
    with path.open("wb") as f2:
      f2.write(f1.read())
