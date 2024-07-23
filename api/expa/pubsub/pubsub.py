# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dataclasses
from concurrent import futures
from typing import Callable

import google.cloud.pubsub_v1.publisher.futures as publisher_futures
import google.cloud.pubsub_v1.subscriber.message as subscriber_message
import msgpack
import numpy as np
from google.cloud import pubsub_v1


@dataclasses.dataclass
class DataMessage:
  project: str
  user: str
  exp: str
  run: str
  step: int
  timestamp: float
  data: dict[str, np.ndarray]

  def pack_safe(self, max_size: int = 9_999_000):
    # Pack to bytes, respecting the maximum PubSub message size.
    buf = self.pack()
    if len(buf) > max_size:
      # Remove fields above 1k. Assume that's enough to cut down the size
      data = self.data
      large_fields = [k for k, v in data.items() if v.nbytes > 10_000]
      print(f'Message over {max_size} bytes - skipping {large_fields}')
      data = {k: v for k, v in data.items() if k not in large_fields}
      buf = dataclasses.replace(self, data=data).pack()
      assert len(buf) <= max_size, 'Message still too large'
    return buf

  def pack(self) -> bytes:
    def encode_np(obj):
      if isinstance(obj, np.ndarray):
        obj = {'__np__': (obj.dtype.str, obj.shape, obj.tobytes())}
      return obj

    obj = dataclasses.asdict(self)
    buf = msgpack.packb(obj, default=encode_np)
    assert isinstance(buf, bytes)
    return buf

  @staticmethod
  def unpack(packed: bytes) -> 'DataMessage':
    def decode_np(obj):
      if '__np__' in obj:
        dtype, shape, buf = obj['__np__']
        return np.frombuffer(buf, dtype).reshape(shape)
      return obj

    obj = msgpack.unpackb(packed, object_hook=decode_np)
    if 'exp' not in obj:  # TODO: temporary patch for old messages
      exp, run = obj['run'].split('/', maxsplit=1)
      obj['exp'] = exp
      obj['run'] = run
    return DataMessage(**obj)


@dataclasses.dataclass
class ParamsMessage:
  project: str
  user: str
  exp: str
  run: str
  params: dict[str, str]

  def pack(self) -> bytes:
    obj = dataclasses.asdict(self)
    buf = msgpack.packb(obj)
    assert isinstance(buf, bytes)
    return buf

  @staticmethod
  def unpack(packed: bytes) -> 'ParamsMessage':
    obj = msgpack.unpackb(packed)
    if 'exp' not in obj:  # TODO: temporary patch for old messages
      exp, run = obj['run'].split('/', maxsplit=1)
      obj['exp'] = exp
      obj['run'] = run
    return ParamsMessage(**obj)


class Publisher:

  def __init__(self, project: str, topic: str, credentials=None):
    self._pub = pubsub_v1.PublisherClient(credentials=credentials)
    self._topic = pubsub_v1.PublisherClient.topic_path(project, topic)
    self._pending: list[publisher_futures.Future] = []

  def send_metrics(self, data: DataMessage, block: bool = False) -> None:
    self._send('data', data.pack_safe(), block=block)

  def send_params(self, params: ParamsMessage, block: bool = False) -> None:
    self._send('params', params.pack(), block=block)

  def _send(self, typ: str, msg: bytes, block: bool = False) -> None:
    self._pending = [f for f in self._pending if f.running()]
    res = self._pub.publish(self._topic, msg, typ=typ)
    if block:
      res.result()
    else:
      self._pending.append(res)

  def wait(self):
    futures.wait(self._pending)
    self._pending = []


class Subscriber:

  def __init__(self, project: str, subscription: str):
    self._sub = pubsub_v1.SubscriberClient()
    self._sub_path = pubsub_v1.SubscriberClient.subscription_path(
        project, subscription
    )

  def listen(
      self,
      on_data: Callable[[DataMessage], bool],
      on_params: Callable[[ParamsMessage], bool],
      parallel=10,
  ):
    def callback(msg: subscriber_message.Message):
      try:
        if msg.attributes.get('typ') == 'data':
          data = DataMessage.unpack(msg.data)
          if on_data(data):
            msg.ack()
          else:
            msg.nack()

        elif msg.attributes.get('typ') == 'params':
          params = ParamsMessage.unpack(msg.data)
          if on_params(params):
            msg.ack()
          else:
            msg.nack()

        else:
          print(f'Skipping unknown type {msg.attributes}: {len(msg.data)}')
          msg.ack()

      except Exception as ex:
        msg.nack()
        print(f'ERROR processing message: {ex}')

    flow = pubsub_v1.types.FlowControl(max_messages=parallel)
    job = self._sub.subscribe(self._sub_path, callback, flow_control=flow)
    print('listening...')
    job.result()
