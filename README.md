# Reconcile
Playing around with file reconcilliation
# ReconProject
Sample project playing around with trade reconcilliation 

Thoughts about this project- this is a bit of a double exploration project, first and foremost with trade reconcilliation and as deep of a dive as I can do. Additionally playing around with the capabilities of generative AI- looking at 

6/13/2025 update: Played around with this a bit- uploading what I have to github so I can better monitor my project. Currently have fake data through external confirmations and an internal system. The confirmation pdfs are generated through a confirmation csv- this csv can not be used for any validation work (will neveer be "seen" by the checker) Started on checker, but unsure how I feel about it yet. Ideally to mimic real life- the system should take in a confirmation PDF- not the confirmation CSV just the pdf and try to find the matching in the system, as well as being able to handle numerical errors- then report on how many files were matched correctly
Thoughts on next steps:
. Then the system should be built out as follows, adding in typos in the stock symbols focusing on the current 10- being able to find similarity and pick the correct symbol-after that modify such that the prices reflect current prices rather than some randomized price- include all stock symbols through use of an API - having the system check the most likely correct stock- perhaps finally adding in other confirmations

6/17/202- Got my wisdom teeth out so have been slightly MIA on this project- trying to make the synthetic data more realaistic- barring that my fake trade form is from 1998. Got more symbols and realistic prcing into into the fake data- need to mess with the yahoo query error as well as the recon simulation

6/19/2025- Teeth still hurting, added so many comments to this project. Also added more controllable randomness to the error. Added in a way to get some metrics out of this matching. Will work on more testing tommorrow.



Sources:
Portions of this was also an exercise with generative AI's coding abilities
Sample Trade Confirmation to be copied:
https://www.rbccm.com/assets/rbccm/docs/legal/doddfrank/Documents/ISDALibrary/1992%20Confirmation%20for%20OTC%20Equity%20Index%20Option%20Transaction.pdf

using yfinance and y finance documentation https://ranaroussi.github.io/yfinance/
