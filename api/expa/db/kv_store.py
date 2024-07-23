import io
from pathlib import Path
from typing import Protocol

import numpy as np


class KVStore(Protocol):
  def write_tensors_data(
    self,
    data: dict[str, np.ndarray],
    xid: int,
    rid: int,
    mids: dict[str, int],
    step: int,
  ) -> None: ...

  def write_tensor_data(
    self,
    data: np.ndarray,
    xid: int,
    rid: int,
    mid: int,
    step: int,
  ) -> None: ...

  def read_tensor_data(
    self,
    xid: int,
    rid: int,
    mid: int,
    step: int,
  ) -> np.ndarray | None: ...


class FileKVStore:
  def __init__(self, root_dir: str | Path):
    self.root_dir = Path(root_dir)  # TODO: GCS
    self.root_dir.mkdir(parents=True, exist_ok=True)

  def write_tensors_data(
    self,
    data: dict[str, np.ndarray],
    xid: int,
    rid: int,
    mids: dict[str, int],
    step: int,
  ) -> None:
    for key, value in data.items():
      self.write_tensor_data(value, xid, rid, mids[key], step)

  def write_tensor_data(
    self,
    data: np.ndarray,
    xid: int,
    rid: int,
    mid: int,
    step: int,
  ) -> None:
    # TODO: async (will block ui otherwise)
    path = self.root_dir / str(xid) / str(rid) / str(mid) / f"{step}.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    save_npz({"data": data}, path)

  def read_tensor_data(
    self,
    xid: int,
    rid: int,
    mid: int,
    step: int,
  ) -> np.ndarray | None:
    # TODO: async (will block ui otherwise)
    path = self.root_dir / str(xid) / str(rid) / str(mid) / f"{step}.npy"
    if not path.exists():
      print(f'{str(path)} not found')
      return None
    with path.open("rb") as f:
      print(f'{str(path)} loading')
      return np.load(f)["data"]


def save_npz(data: dict[str, np.ndarray], path: Path):
  # Save to memory buffer first
  with io.BytesIO() as f1:
    np.savez_compressed(f1, **data)
    f1.seek(0)
    # Then copy to file
    with path.open("wb") as f2:
      f2.write(f1.read())
