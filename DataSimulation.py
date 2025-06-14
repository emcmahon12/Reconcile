# Import Statements 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from fpdf import FPDF

#setting up a random seed
random.seed(42)
np.random.seed(42)

#simulated stock symbols currently S&P Top 10 Constituents by Index Weight TODO: incorporate an error here
symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN','NVDA','META', 'AVGO','BRK.B', 'GOOG']

#building data folders
os.makedirs("data", exist_ok=True)
os.makedirs("confirmations/external", exist_ok=True)
os.makedirs("confirmations/internal", exist_ok=True)

#simple trade generation data TODO: calculate complexity/try to improve
def TradeGenerate(n):
    #takes in amount to generate
    data = []
    OptionStyles = ['European', 'American']
    OptionTypes = ['Call', 'Put']

    for i in range(n):
        time = datetime.now() - timedelta(minutes=random.randint(0, 1440))
        symbol = random.choice(symbols)
        quantity = random.randint(1, 1000)
        price = round(random.uniform(100, 1000), 2)
        style = random.choice(OptionStyles)
        TypeOption = random.choice(OptionTypes)
        data.append([time, symbol, quantity, price, style, TypeOption])

    return pd.DataFrame(data, columns=["timestamp", "symbol", "quantity", "price", "style", "TypeOption"])

def FileSim():
   internal = TradeGenerate(100)
   #workaround for matching algo defo could use TradeID
   internal['InternalNum'] = list(range(len(internal)))
   external = internal.copy()

   #starting to have incorrect matches in price and quantity
   for i in range(10):
       external.loc[i, 'quantity'] += random.randint(-3, 3)
       external.loc[i, 'price'] += round(random.uniform(-2, 2), 2)

   #saving sheets to data
   internal.to_csv("data/internal_trades.csv", index=False)
   external.to_csv("data/external_trades.csv", index=False)
   print("data saved (yipee)")


#building fake pdfs as done in https://www.rbccm.com/assets/rbccm/docs/legal/doddfrank/Documents/ISDALibrary/1992%20Confirmation%20for%20OTC%20Equity%20Index%20Option%20Transaction.pdf
#citation note- utilized CHATGPT for help with formatting to fit the documents

class TradeConfirmationPDF(FPDF):
   
   #headers
   def header(self):
       self.set_font("Arial", 'B', 13) #Bold, Size 13
       self.cell(0, 10, "Confirmation of OTC Equity Index Option Transaction", ln=True, align='C')
       self.set_font("Arial", '', 11)
       self.ln(8) #vertical space after header

   def introduction(self, TradeID, party):
       #miniature intro letter, modeled after the RBC doc
       self.multi_cell(0, 7, f"""
[Letterhead of {party}]


Date: {self.DateToday()}
To: Counterparty (MCMAHON Investments)


Dear Sir or Madam,


The purpose of this Confirmation is to confirm the terms and conditions of the OTC Equity Index Option Transaction entered into between us on the Trade Date specified below (the "Transaction"). This Confirmation constitutes a "Confirmation" as referred to in the ISDA Master Agreement between the parties.
       """)
       self.ln(4)


   def GeneralTerms(self, trade):
    #adding in these terms similar to RBC
    self.set_font("Arial", 'B', 11)
    self.cell(0, 8, "General Terms:", ln=True)
    self.set_font("Arial", '', 11)

    self.multi_cell(0, 7, f"""
Trade ID: {trade['TradeID']}
Trade Date: {trade['timestamp']}
Option Style: {trade['style']}
Option Type: {trade['TypeOption']}
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
       #the execution terms
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
       #cash settlement terms
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
       #fake closing text
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
   #create fake pdf from trade details
   pdf = TradeConfirmationPDF()
   pdf.add_page()
   pdf.introduction(trade['TradeID'], trade['party'])
   pdf.GeneralTerms(trade)
   pdf.ExerciseTerms()
   pdf.SettlementTerms(trade)
   pdf.footer()
   pdf.output(OutputPath)


def ReadConfirmations(PathCSV, OutputFolder, PartyLabel):
   #reads data from the csv to put in
   df = pd.read_csv(PathCSV)
   for i, row in df.iterrows():
       trade = row.to_dict()
       #5 digits for the time being
       trade["TradeID"] = f"{i:05d}"
       trade["party"] = PartyLabel
       print({trade['TradeID']})
       filename = os.path.join(OutputFolder, f"{trade['TradeID']}.pdf")
       GenerateConfirmation(trade, filename)
   print(f" {len(df)} confirmations built")




if __name__ == "__main__":
   FileSim()
   ReadConfirmations("data/external_trades.csv", "confirmations/external", "External")
