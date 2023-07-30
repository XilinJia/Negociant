
# Negociant, automatic trading engine of commodity and financial futures

---

### Brief Introduction

Negociant is an automated trading platform specialized in trading the Chinese futures markets through the CTP protocols. It was originally forked off from an open source project named "vnpy" in 2017, further developed, enhanced, customized, thoroughly tested and launched for automated trading.

Note: this is retired version that is no longer supported.

Update: all Python codes are now in Python 3

---
### Quick Start

1. Prepare a computer with Ubuntu 20.04 (64-bit) installed.

2. Install [Anaconda 5.2.0](http://www.continuum.io/downloads).

3. Install [MongoDB](https://www.mongodb.org/downloads#production), please register MongoDB as Windows Service.

4. Install [Visual C++  Redistributable Packages for VS2013 (32-bit)](https://www.microsoft.com/en-gb/download/details.aspx?id=40784).

5. Run **install.bat** to install Negociant and all dependencies.

6. Define your trading strategies in by referencing the files in **negociant/trader/app/ctaStrategy/strategy**.

7. Backtesting your strategy by referencing files in **example/CtaBacktesting**.

8. As an example, go to folder **examples/TradeNH/** and edit **CTP_connect.json** file with your exchange config:
	* brokerID: id of your broker
	* mdAddress: ip address of your broker's data server 
	* tdAddress: ip address of your broker's trade server
	* userID: your login id with the broker 

9. Specify your strategy combinations to be used in **CTA_setting.json**.

10. Start trading by running "python runNH.py", login with your password and then you are ready to trade!

### Project Structure

1. Python API of CTP is included.

2. Event engine and RPC framework.

3. A powerful bar engine **lkBarsEngine** builds data streams into trading bars with time units of your choice.

4. A powerful data recorder engine and a CTA trade engine realizes trading actions.

5. Examples about how to use Negociant for solving real world trading issues (examples).

---

### No warranty and no guarantee of porfits

While the system has been thoroughly tested and extensively used in live trading for years, the author here offers no warranty and absolutely no guarantee for your profits.

### Contact

If you have any questions about how to use the project or any suggestions about improving it, please feel free to communicate at https://github.com/XilinJia/Negociant.

---
### License
MIT

