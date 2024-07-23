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

import asyncio
import threading
import time

from absl import app, flags

import expa.db
import expa.pubsub

flags.DEFINE_string('project', None, 'GCP project', required=True)
flags.DEFINE_string('subscription', None, 'GCP subscription', required=True)
flags.DEFINE_string(
    'dsn', 'postgresql://postgres:postgres@localhost/postgres', 'Database.'
)
flags.DEFINE_integer('parallel', 20, 'Number of parallel messages to process.')
flags.DEFINE_bool('log_sql', False, '')

args = flags.FLAGS


def main(unused_argv):
  sync = SyncRunner()
  sub = expa.pubsub.Subscriber(args.project, args.subscription)
  repo = expa.db.Repository(args.dsn, max_conn=args.parallel, log=args.log_sql)
  sync(repo.init())

  def on_data(msg: expa.pubsub.DataMessage) -> bool:
    print(
        f'Processing {len(msg.data)} metrics from {msg.exp}/{msg.run}'
        f' step {msg.step} age {(time.time() - msg.timestamp):.0f} sec\n',
        end='',
    )
    sync(
        repo.write_metrics(
            msg.data,
            project=msg.project,
            user=msg.user,
            exp=msg.exp,
            run=msg.run,
            step=msg.step,
            timestamp=msg.timestamp,
        )
    )
    return True

  def on_params(msg: expa.pubsub.ParamsMessage) -> bool:
    print(f'Processing {len(msg.params)} params from {msg.run}\n', end='')
    sync(
        repo.write_params(
            msg.params,
            project=msg.project,
            user=msg.user,
            exp=msg.exp,
            run=msg.run,
        )
    )
    return True

  sub.listen(on_data, on_params, parallel=args.parallel)


class SyncRunner:
  """Safe way to run async calls from sync code."""

  def __init__(self):
    self.loop = asyncio.new_event_loop()
    self.loop_started = threading.Event()
    self.thread = threading.Thread(target=self.start_loop, daemon=True)
    self.thread.start()
    self.loop_started.wait()

  def start_loop(self):
    asyncio.set_event_loop(self.loop)
    self.loop_started.set()
    self.loop.run_forever()

  def __call__(self, coro):
    assert self.loop.is_running()
    return asyncio.run_coroutine_threadsafe(coro, self.loop).result()


if __name__ == '__main__':
  app.run(main)
