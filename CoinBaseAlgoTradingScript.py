#Automated algorithimic trading script, likely to be implemented in either Coinbase
#or ThinkOrSwim.
#Bitcoin or other cryptocurrencies are favorable given the fees are minimal, trading is
#24/7, and there are no day-trade restrictions.

#https://www.youtube.com/channel/UCrXjzUN6EtlyhaaAerbPfkQ
#This will be the source of my trading strategies and possibly some of the code as well

#Requirements:
#1. Trading must take place automatically, at all hours of the day
#2. Preferable to use signals on a 1 minute or 5 minute chart so the scalps can be quicker
#   and exponentiate the returns faster
#3. Stop-Loss
#4. Regular withdrawls between 10-20% of total balance. Can be reduced as balance increases
#5. Strategy must be backtested before implemenated live

#Pros and cons of Algo Trading
#https://www.investopedia.com/articles/trading/11/automated-trading-systems.asp

#Begin code found on https://github.com/danpaquin/coinbasepro-python
#Useful: https://algotrading101.com/learn/coinbase-pro-api-guide/
#Doesn't work on Python 3.10, must use Python 3.9 or earlier
import cbpro
import base64
import json
from time import sleep

key = 'a14432901d2cf55b3c604ca109674fc0'
passphrase = '21hvkngwzux'
secret = ''

encoded = json.dumps(secret).encode()
b64secret = base64.b64encode(encoded)

auth_client = cbpro.AuthenticatedClient(key, secret, passphrase)
limit = auth_client.get_product_ticker(product_id='RLC-USD')

#This code is supposed to place the order, must go in an if statement
#and execute once conditions are met
try:
    order=auth_client.place_limit_order(product_id='RLC-USD', side='sell',
    price=float(limit['ask'])+0.03, size='6')
except Exception as e:
    print(f'Error placing order: {e}')

sleep(2)

try: #This checks to see if the order was placed
    check = order['id']
    check_order = auth_client.get_order(order_id=check)
except Exception as e:
    print(f'Unable to check order. It might be rejected. {e}')

#https://www.youtube.com/watch?v=9kOCpkC-PFQ Potential Trading Strategy
#Placing orders works. Now I must find a strategy and find a way to implement it
#Data can come from ThinkOrSwim if having difficulty implementing indicators
#directly through Coinbase API

#CB-Pro Trading fee structure, based on 30 day trailing volume
#https://help.coinbase.com/en/pro/trading-and-funding/trading-rules-and-fees/fees
#After $10k in volume traded (and $40 in fees), my fees would be 0.5% for maker orders,
#0.25% when buying and 0.25% when selling.  I should profit at least 1% per trade
#in order for this strategy to be successful
#https://ftx.capitalise.ai/account/signup?returnUrl=https%3A%2F%2Fftx.capitalise.ai%2Fstrategy-examples%3Furef%3Dtradepro%26shortlink%3Dd2f24f9%26c%3DTradePro%26pid%3DAffiliation%26af_referrer_customer_id%3Dadd401f6-fb83-9d4a-877f-d99727c6a94e
#Above is a website for back-testing. For now programming is on pause, and the plan is
#3. CB fees are too high. Consider using ByBit or another exchange with lower fees
#2. Find a strategy(s)
#3. Backtest it using different time periods, and different time intervals
