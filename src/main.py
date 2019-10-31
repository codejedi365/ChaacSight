#!/usr/bin/python

import getpass
from os import path
import shutil

# Main program
def main():
	print("[MAIN] Calling Data_Wrangling_CAP1...")
	try:
		import Data_Wrangling_CAP1

	except SystemExit as event_exit:
		if event_exit.code != 0:
			raise event_exit
		else:
			pass  # Ignore and continue (accelerated processing due to existing files)

	# Load any previous results if they exist
	try:
		prevResults = path.join(path.dirname(path.realpath(__file__)),'data','manipulated_data','allMAE.json')
		shutil.copyfile(
			prevResults,
			path.join(path.expanduser("~"), 'allMAE.json')
		)
		print("[MAIN] loading previously solved results from {}".format(prevResults))
	except:
		pass  # Ignore and continue since Exogenous Vars will create the file as default instead of modifying previous results

	print("[MAIN] Calling Exogenous_Variables...")
	import Exogenous_Variables
	# print("[MAIN] Calling Future Predictions...")
	# import Future_Predictions

print("[MAIN] Running Rainfall Predictor as "+getpass.getuser()+" ...")
print("[MAIN] HOME (~)="+path.expanduser("~"))
print("[MAIN] ")
main()
