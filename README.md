# RabbitMQ Chat

## Installation

### docker-compose (recommended)

To easily bootstrap project, please use docker-compose. Make sure, that ports `5672` and `15672` are not used.

```shell
docker-compose up -d --build
```

### Manually

Not documented yet

## Usage

### View rabbitmq management panel

Visit `localhost:15672` with `guest:guest` credentials

### Run chat client

First client
```shell
docker exec -ti chat-client1 python cli.py
```

Second client
```shell
docker exec -ti chat-client2 python cli.py
```

### Application usage

You can interact with ui via mouse or keyboard. 

To run command select input on the bottom and type command. Then you can select groups and type messages under the same input on the bottom.
