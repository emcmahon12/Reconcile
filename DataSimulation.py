# Import Statements 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from fpdf import FPDF
import yfinance as yf
import time
import requests
from io import StringIO


# setting up a random seed
random.seed(42)
np.random.seed(42)

# Get top 500 tickers from GitHub
def GetSymbols():
    """
    Downloads S&P 500 symbols from GitHub (with dots converted to dashes for Yfinance workaround ).
    Falls back to a default of top 10 if exception.
    """
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    try:
        #this was some weird workaround for getting thhe data 
        response = requests.get(url, verify=False)  # disable SSL verification
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))# returning list of symbols replacing dots with dashes
        return [sym.replace(".", "-") for sym in df["Symbol"].tolist()] 
    except Exception as e:
        #in the case that loading fails
        print(f"Failed to load CSV: {e}")
        return ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN','NVDA','META', 'AVGO','BRK-B', 'GOOG']

symbols = GetSymbols()

# building data folders
os.makedirs("data", exist_ok=True)
os.makedirs("confirmations/external", exist_ok=True)
os.makedirs("confirmations/internal", exist_ok=True)

def LiveStockData(symbol):
    """
    Takes in a stock symbol and fetches stock data that should be accurate through yfinance for the symbol
    Returns accurate data, or random data if exception.
    """
    try:
        ticker = yf.Ticker(symbol) #creating yfinance ticker object
        hist = ticker.history(period="1d") #getting last one day of historical data
        price = round(hist["Close"].iloc[-1], 2) if not hist.empty else round(random.uniform(100, 1000), 2)

        info = ticker.info #getting general info

        #getting short name, sector and market cap defaulting unknown
        stockName = info.get("shortName", "Unknown") 
        stockSector = info.get("sector", "Unknown")
        marketCap = info.get("marketCap", None)

        #returning all fetched information
        return {
            "price": price,
            "stockName": stockName,
            "stockSector": stockSector,
            "marketCap": marketCap
        }
        #if exception random price, all else unknown
    except Exception:
        return {
            "price": round(random.uniform(100, 1000), 2),
            "stockName": "Unknown",
            "stockSector": "Unknown",
            "marketCap": None
        }

# simple trade generation data TODO: calculate complexity/try to improve
def TradeGenerate(n):
    """
    Takes in an integer n, then generates 'n' simulated trade with some random details.
    """
    data = []
    OptionStyles = ['European', 'American']
    OptionTypes = ['Call', 'Put']

    for i in range(n):
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 1440)) ##time stamp is random within the last 24 hours
        symbol = random.choice(symbols) #picking random symbol from list
        stockData = LiveStockData(symbol) #getting data for the symbol
        #time.sleep(0.1)
        quantity = random.randint(1, 1000) #quantity is random 
        price = stockData['price'] #price is from data
        style = random.choice(OptionStyles) # option style is random from list
        typeOption = random.choice(OptionTypes) #option type random from list
        #putting all of this into a pd dataframe
        data.append([
            timestamp, symbol, quantity, price, style, typeOption,
            stockData["stockName"], stockData["stockSector"], stockData["marketCap"]
        ])
    return pd.DataFrame(data, columns=[
    "timestamp", "symbol", "quantity", "price", "style", "typeOption",
    "stockName", "stockSector", "marketCap"   # lowercase names to match what PDF expects
])
def FileSim():
    """
    Generates internal and external trade df, creates possible issues only in 
    ithe external df, and save both to CSV files. Nothing is returned. Note- External DF should never been "seen" by checker.
    """
    internal = TradeGenerate(100) #generate 100 trades
    internal['InternalNum'] = list(range(len(internal)))  # ground truth index
    internal.to_csv("data/internal_trades.csv", index=False)

    external = internal.copy()
    external = external.sample(frac=1).reset_index(drop=True)
    external = external.copy()

    # deciding on error rate- this gives 20% of trades an error 
    ErrorRate = 0.20
    ErrorNum = int(len(external) * ErrorRate)

    # Randomly select indx to include error
    ErrorINDX = random.sample(range(len(external)), ErrorNum)

    for i in ErrorINDX:
        #pick type of error to include
        ErrorType = random.choice(['quantity', 'price', 'symbol_typo'])

        if ErrorType == 'quantity':
            external.loc[i, 'quantity'] += random.randint(-5, 5) 
            # quantity can't go below 1
            if external.loc[i, 'quantity'] < 1:
                external.loc[i, 'quantity'] = 1
        elif ErrorType == 'price':
            external.loc[i, 'price'] += round(random.uniform(-5, 5), 2) 
            #price can't go below 1
            if external.loc[i, 'price'] < 1:
                external.loc[i, 'price'] = 1.0
        elif ErrorType == 'symbol_typo':
            symbol = external.loc[i, "symbol"]
            if len(symbol) > 1:
                TypoIndex = random.randint(0, len(symbol) - 1)
                TypoCharacter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                TypoSymbol = symbol[:TypoIndex] + TypoCharacter + symbol[TypoIndex + 1:]
                external.loc[i, "symbol"] = TypoSymbol
            else: # case if symbol is just one signular character
                 external.loc[i, "symbol"] = symbol + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # saving sheets to data
    internal.to_csv("data/internal_trades.csv", index=False)
    external.to_csv("data/external_trades.csv", index=False)
    print("data saved (yipee)")

# building fake pdfs as done in RBC doc
# citation note - utilized CHATGPT for help with formatting to fit the documents

class TradeConfirmationPDF(FPDF):
    """
    Class for generating PDF trade confirmation documents, inheriting from FPDF.
    Includes methods for header, introduction, general terms, exercise terms,
    settlement terms, and footer, mimicking the cited confirmation.
    """

    # headers
    def header(self):
        self.set_font("Arial", 'B', 13)  # Bold, Size 13
        self.cell(0, 10, "Confirmation of OTC Equity Index Option Transaction", ln=True, align='C')
        self.set_font("Arial", '', 11)
        self.ln(8)  # vertical space after header

    def introduction(self, tradeId, party):
        # miniature intro letter, modeled after the RBC doc
        self.multi_cell(0, 7, f"""
[Letterhead of {party}]


Date: {self.DateToday()}
To: Counterparty (MCMAHON Investments)


Dear Sir or Madam:


The purpose of this Confirmation is to confirm the terms and conditions of the OTC Equity Index Option Transaction entered into between us on the Trade Date specified below (the "Transaction"). This Confirmation constitutes a "Confirmation" as referred to in the ISDA Master Agreement between the parties.
       """)
        self.ln(4)

    def GeneralTerms(self, trade):
        # adding in these terms similar to RBC
        self.set_font("Arial", 'B', 11)
        self.cell(0, 8, "General Terms:", ln=True)
        self.set_font("Arial", '', 11)

        self.multi_cell(0, 7, f"""
Trade ID: {trade['tradeId']}
Trade Date: {trade['timestamp']}
Option Style: {trade['style']}
Option Type: {trade['typeOption']}
Seller: MCMAHON Investments
Buyer: {trade['party']} Party B
Index: {trade['symbol']} Equity Index

Number of Options: {trade['quantity']}
Strike Price: ${trade['price']}
Premium: ${round(trade['price'] * 0.1, 2)}
Premium Payment Date: T+1
Exchange: NASDAQ
Calculation Agent: MCMAHON INVESTMENTS (binding in absence of manifest error)
        """)
        self.ln(2)

    def ExerciseTerms(self):
        # the execution terms
        self.set_font("Arial", 'B', 11)
        self.cell(0, 8, "Procedure for Exercise:", ln=True)
        self.set_font("Arial", '', 11)

        self.multi_cell(0, 7, """
Exercise Period: Expiration Date only
Expiration Date: 2025-06-30
Automatic Exercise: If not previously exercised, Option shall be automatically exercised on the Expiration Date.
Valuation Time: 4:00 PM EST
Valuation Date: Expiration Date
        """)
        self.ln(2)

    def SettlementTerms(self, trade):
        # cash settlement terms
        self.set_font("Arial", 'B', 11)
        self.cell(0, 8, "Cash Settlement Terms:", ln=True)
        self.set_font("Arial", '', 11)

        cash_settlement = round(max(0, (trade['price'] + 2.0) - trade['price']) * trade['quantity'], 2)

        self.multi_cell(0, 7, f"""
Cash Settlement: Applicable
Cash Settlement Amount: ${cash_settlement}
Cash Settlement Payment Date: T+3
Currency: USD
        """)
        self.ln(2)

    def footer(self):
        # fake closing text
        self.set_font("Arial", '', 11)
        self.multi_cell(0, 7, """
This Confirmation will be governed by and construed in accordance with the laws of New York.

Please confirm that the foregoing correctly sets forth the terms of our agreement by signing and returning this Confirmation.

Yours sincerely,

ELEANOR Investments 
By: _______________________ 
Name: 
Title:

Confirmed and agreed:

Counterparty 
By: _______________________ 
Name: 
Title:
        """)
        self.ln(5)

    def DateToday(self):
        return datetime.now().strftime("%Y-%m-%d")

def GenerateConfirmation(trade, OutputPath):
    """
    Giveb a trade and a path, creates a fake PDF document modeling the fake trade.
    """
    pdf = TradeConfirmationPDF()
    pdf.add_page()
    pdf.introduction(trade['tradeId'], trade['party'])
    pdf.GeneralTerms(trade)
    pdf.ExerciseTerms()
    pdf.SettlementTerms(trade)
    pdf.footer()
    pdf.output(OutputPath)

def ReadConfirmations(PathCSV, OutputFolder, PartyLabel):
    """
    Given paths and party labels, reads data, generates fake confirmations,
    and saves them to output folder.
    """
    df = pd.read_csv(PathCSV)
    for i, row in df.iterrows():
        trade = row.to_dict()
        # 5 digits for the time being
        trade["tradeId"] = f"{int(trade['InternalNum']):05d}" # internal num becomes the id/ title
        trade["party"] = PartyLabel
        trade["true_internal_num"] = trade["InternalNum"]
        print({trade['tradeId']})
        filename = os.path.join(OutputFolder, f"{trade['tradeId']}.pdf")
        GenerateConfirmation(trade, filename)
    print(f" {len(df)} confirmations built")

if __name__ == "__main__":
    FileSim()
    ReadConfirmations("data/external_trades.csv", "confirmations/external", "External")
