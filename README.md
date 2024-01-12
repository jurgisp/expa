# eXpa

Metric logging and analysis tool for ML experiments.

The components are:
- Scalable data store backed by PostgreSQL
- REST API for logging and retrieving data
- Python client library [expa](https://pypi.org/project/expa/) for sending metrics
- Powerful UI for metric visualization

**This is a pre-release work in progress, expect breaking changes!**

## Getting started

#### Start development server locally

```sh
git clone https://github.com/jurgisp/expa.git && cd expa
PORT=8000 docker-compose up
```

#### Use expa client to push metrics

```python
!pip install expa
import expa
logger = expa.Logger('experiment', 'run', api_url='http://localhost:8000/api')
logger.log_params({'param': 'value'})
for step in range(1, 101):
  logger.log({'loss': 1/step}, step)
```

#### Visualize metrics

Open [localhost:8000](http://localhost:8000/)

## Security

The API does not have any user authentication built-in. Be sure to add an auth layer if you are planning to deploy the service on publicly accessible network.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by Google and Google specifically disclaims all warranties as to its quality, merchantability, or fitness for a particular purpose.

This product is not intended or suitable for storing private data.
