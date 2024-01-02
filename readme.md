# Quantconnect strategies
This repo is a collection of strategies that I've developed across a year of tinkering with [quantconnect](https://www.quantconnect.com/).
Most of them are not profitable, but exist as an implementation of an idea I had at one point and wished to try.
The only strategy I actually live traded is in the Breakout directory.
I no longer use quantconnect and so have decided to make this repo public.

## Usage guide

When running the strategies locally you can download stock data from qunatconnect API:
```sh
$ lean data download --dataset "US Equities" --organization "<ORG_ID>" --data-type "Trade" --ticker "AAPL" --resolution "Daily" --start "20210101" --end "20211231"
```

To push strategy updates to the cloud, do the following:
```sh
$ lean cloud push --project <PROJECT_NAME>
```

To backtest a strategy on quantconnect, do the following:
```sh
$ lean cloud backtest <PROJECT_NAME> --push
```
The `--push` flag will ensure that the latest local updates are pushed before the backtest starts.
Initiating the backtest via the cli is also much quicker when compared with using the in browser GUI.
