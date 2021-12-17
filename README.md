# Live BTC Implied Volatility Charts

![image](https://user-images.githubusercontent.com/313480/140698710-91c1e568-7825-46ad-9656-086c3dae32c5.png)

Implied volatility (IV) is basically a metric used to forecast what the market thinks about the future price movements of an option's underlying stock. IV is a dynamic figure that changes based on activity in the options marketplace. Usually, when implied volatility increases, the price of options will increase as well, assuming all other things remain constant. When implied volatility increases after a trade has been placed, it’s good for the option owner and bad for the option seller. IV is useful because it offers traders a general range of prices that a security is anticipated to swing between and helps indicate good entry and exit points. IV isn’t based on historical pricing data on the stock. Instead, it’s what the marketplace is “implying” the volatility of the stock will be in the future, based on price changes in an option. 


Using LedgerX public websocket API we're able to demonstrate using Redis as a multipurpose datastore.
Using a server side Lua script to check the received updates counter we can appropriately publish PUBSUB messages to the
listening [Bokeh](https://docs.bokeh.org/en/latest/) app and store the bid/ask prices to a 
[RedisTimeSeries](https://oss.redislabs.com/redistimeseries/) data type atomically.

The Bokeh app displays the implied volatility calculated from the best bid and offer prices received over websocket.
We're using the Black-Scholes formula implemented by the [vollib](http://vollib.org/) library.

![image](https://user-images.githubusercontent.com/313480/140698675-08c8728f-a92b-426f-9552-aeb9bdfa22fd.png)


We get the price of bitcoin from polling the coinbase API every 3 seconds.

This allows traders to do further analysis and find opportunities in possible mispricings in the volatility component of
the options pricing model.

## Getting Started

### Step 1. Run Redis container

```
 docker run -d -p 6379:6379 redislabs/redismod
```

Thhis will run both Redis and Redis modules like [RedisTimeSeries](https://oss.redislabs.com/redistimeseries/)

### Step 2. Clone the repository

```
 git clone https://github.com/redis-developer/bitcon-implied-volatility
```

### Step 3. Install the dependencies

Install the below dependencies in requirements.txt in venv

```
 pip3 install -r requirements.txt`

```

### Step 4. Create a LedgeX API key

Create a LedgerX api key (https://app.ledgerx.com/profile/api-keys) and copy to a file in root of project named "secret"

### Step 5.  Execute the script

Run `ledgerx_ws.py` which is the script consuming the websocket stream from LedgerX 

```
 python3 ledgerx_ws.py
```

### Step 5. Run Bokeh server application

Run the below command from the project root to start up the Bokeh server application and open a web browser to
the local URL.

```bash
  bokeh serve --show iv_app.py
```

![image](https://user-images.githubusercontent.com/313480/140698568-d92a7020-db73-47b9-ad2a-fc896d52c897.png)


There are pre-cache files `contracts.pkl` and `id_table.json` which are loaded so no authenticated requests are needed.
If you have a LedgerX account and API key, you can create a file named `secret` with the API key on the first line which
will enable authenticated API queries.

## Using Docker

### Pre-requisite:
- Install docker: https://docs.docker.com/engine/install/

- Run the command to avoid background save failure under low memory condition

```bash
  sysctl vm.overcommit_memory=1 
```

- Install docker-compose: https://docs.docker.com/compose/install/

If you don't configure docker to be used without sudo you'll have to add sudo in front of any docker command

- To build image: 

```
 sudo docker build -t iv_app:dev .`
```

- To run image interactively, mapping port 5006 from the container to 5006 on your local machine:

`sudo docker run -it -p 5006:5006 -w "/implied-vol-plot" -v "$(pwd):/implied-vol-plot" iv_app:dev bash`

- To run it in the background in detached mode:

`sudo docker run -d -p 5006:5006 -w "/implied-vol-plot" -v "$(pwd):/implied-vol-plot" iv_app:dev`

### Using Docker-compose

- To start services: 
`docker-compose up` #can add -d flag to run in background

- To stop services: 

`docker-compose down`

To run a specific service interactively: 

`docker-compose exec <name-of-service-in-docker-compose-yaml> sh`
