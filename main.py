#!/usr/bin/python3
import argparse
import tokenizer
import scriptwriter

parser = argparse.ArgumentParser(description="Transform GECK scripts into Papyrus.")
parser.add_argument('input', metavar='input', type=str, nargs=1, help='Input file')
parser.add_argument('output', metavar='output', type=str, nargs=1, help='Output file')
parser.add_argument('-nl', '--no-list-usage', action='store_true', help='Do not use the GECK function list to remove ambiguity')
parser.add_argument('-d', '--debug', action='store_true', help='Print debug informations')
args = parser.parse_args()

with open(args.input[0], "r") as script:
	with open(args.output[0], "w") as outscript:
		print("Tokenizing script...")
		tk = tokenizer.Tokenizer(script, not args.no_list_usage)
		tk.run()
		if args.debug:
			print(tk.tokens)
			print(tk.variableList)
		print("Generated", len(tk.tokens), "tokens, collected", len(tk.variableList), "variables, rewrote",  tk.rewroteCount, "elements")
		print("Writing script from tokens...")
		sw = scriptwriter.ScriptWriter(tk.tokens, outscript)
		sw.run()
		print("Done")
