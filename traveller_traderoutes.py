#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Code for calculating trade route for the Traveller rpg (Mongoose edition)

import string, sys, re, argparse, json

system_list = {}

certain_routes = []
possible_routes = []

# ToDo name
higher_hex_modulo_two = 1
max_hex_row_value = 10
max_hex_column_value = 8
certain_dist_max = 2
possible_dist_max = 4

valid_trade_codes = ['Ag','As','Ba','De','Fl','Ga','Hi','Ht','IC','In','Lo','Lt','Na','NI','Po','Ri','Va','Wa']
col1i = ['Ht','In']
col2i = ['As','De','IC','NI']
col1j = ['Hi','Ri']
col2j = ['Ag','Ga','Wa']
# unused = ['Ba','Fl','Lo','Lt','Na','Po','Va']

def construct_args(argv):
	# add default formatter
	parser = argparse.ArgumentParser(description="Calculate trade routes for the rpg Traveller (Mongoose edition).",
	  formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	  epilog="Positional arguments start from 0, as is usual with most \
	  programming languages.  Care is advised when giving positional \
	  arguments, since if they're wrong, you may get strange errors. \
	  When no positional arguments for UWP files are given, everything \
	  up to the first four numbers is taken as the name of the system, \
	  and all two-letter combinations after the location code that are \
	  not on the list of acceptable tradecodes are simply discarded. \
	  Trade codes in json file may be a space-separated string or in \
	  their own list.")
	parser.add_argument('-i','--infile', nargs='?', 
	  type=argparse.FileType('r'),default=sys.stdin)
	parser.add_argument('-o','--outfile', nargs='?', 
	  type=argparse.FileType('w'),default=sys.stdout)
	parser.add_argument('-f','--format', 
	  choices=['UWP', 'json'], default='UWP', 
	  help="The input file format, either a text file with one UWP \
	  code per line or a json list of system lists.")
	parser.add_argument('-pn','--posname', type=int, default=0, 
	  help="Position of system name on UWP line or in json list.")
	parser.add_argument('-pl','--posloc', type=int, 
	  help="Position of system location on UWP line or in json list.")
	parser.add_argument('-pt','--postrcode', type=int, 
	  help="Position of system trade codes on UWP line or in json list.")
	return parser.parse_args()	

def separate_hexcode(hexcode):
	col = int(hexcode[:2])
	row = int(hexcode[2:])
	return col,row

def proper_hexcode(hexcode,syst_name):
	if not re.match('\d{4}',hexcode):
		print "Location hex code [" + hexcode + "], of " + syst_name + ", has improper characters (should be all numbers)."
		sys.exit()
	col,row = separate_hexcode(hexcode)
	if row < 1 or row > max_hex_row_value:
		print "Bad value for row at location [" + hexcode + "] (" + syst_name + ")"
		return False 
	if col < 1 or col > max_hex_column_value:
		print "Bad value for column at location [" + hexcode + "] (" + syst_name + ")"
		return False 
	return True 

def fix_hexcode(possibly_int,syst_name):
	if isinstance(possibly_int,int):
		possibly_int = str(possibly_int)
	if not (isinstance(possibly_int,str) or isinstance(possibly_int,unicode)):
		print "Bad location hex format for " + syst_name + ", should be string (or int)."
		sys.exit()
	if len(possibly_int) == 3:
		possibly_int = "0" + possibly_int
	elif len(possibly_int) != 4:
		print "Location hex code [" + hexcode + "], of " + syst_name + ", has improper length (not 4)."
		sys.exit()
	return possibly_int

def save_system(hexcode,syst_name,trcode_list):
	if not proper_hexcode(hexcode,syst_name):
		sys.exit()
	if hexcode not in system_list:
		system_list[hexcode] = [syst_name,trcode_list]
	else:
		print "Double locations! + add explanation"
		sys.exit()

def valid_trade_code_list(trcode_list):
	valid_list = []
	for trcode in trcode_list:
		if trcode in valid_trade_codes:
			valid_list.append(trcode)
	return valid_list

def split_trcode_str_into_list(trcode_str):
	trcode_list = re.findall('[A-Za-z]{2}',trcode_str)
	return valid_trade_code_list(trcode_list)

def create_from_UWP(UWP_list):
	# todo some checking?
	for line in UWP_list:
		syst_name = line[args.posname:args.posloc].strip()
		hexcode = line[args.posloc:args.posloc+4]
		trcode_list = split_trcode_str_into_list(line[args.postrcode:])
		save_system(hexcode,syst_name,trcode_list)

def guess_from_UWP(UWP_list):
	for line in UWP_list:
		syst_list = re.split('(\d{4})',line,1) # \b to front and end?
		syst_name = syst_list[0].strip()
		hexcode = syst_list[1]
		trcode_list = split_trcode_str_into_list(syst_list[2])
		save_system(hexcode,syst_name,trcode_list)

def create_from_json(json_list):
	for system_list in json_list:
		syst_name = system_list[args.posname]
		hexcode = fix_hexcode(system_list[args.posloc],syst_name)
		trcodes = system_list[args.postrcode]
		trcode_list = []
		if isinstance(trcodes,str) or isinstance(trcodes,unicode):
			trcode_list = split_trcode_str_into_list(trcodes)
		elif isinstance(trcodes,list):
			for trcode in trcodes:
				if len(trcode) != 2:
					print 'Warning: Improper length for trade code "' + trcode + '" (' + syst_name + '), should be 2 characters! (Will ignore.)'
			trcode_list = valid_trade_code_list(trcodes)
		else:
			print "Improper trade code list format in json file, should be list or string."
			sys.exit()	
		save_system(hexcode,syst_name,trcode_list)

def distance(hexcode_a, hexcode_b):
	if hexcode_a == hexcode_b:
		return 0
	col_a,row_a = separate_hexcode(hexcode_a)
	col_b,row_b = separate_hexcode(hexcode_b)
	if col_a == col_b:
		return abs(row_a - row_b)
	# To help conceptualize, we think of travelling from a to b
	col_dist = abs(col_a - col_b)
	corner_top = row_a - col_dist // 2
	corner_bottom = row_a + col_dist // 2
	if col_dist % 2 == 1:
		if col_a % 2 == higher_hex_modulo_two:
			corner_top = corner_top - 1
		else:
			corner_bottom = corner_bottom + 1
	if row_b < corner_top:
		return col_dist + (corner_top - row_b)
	elif corner_top <= row_b and row_b <= corner_bottom:
		return col_dist
	elif corner_bottom < row_b:
		return col_dist + (row_b - corner_bottom)
	else:
		return None  # Should never get here...

def calculate_routes():
	for loc_a in system_list:
		for loc_b in system_list:
			dist = distance(loc_a,loc_b)
			if loc_a == loc_b or dist > possible_dist_max:
				continue
			trcodes_a = system_list[loc_a][1]
			trcodes_b = system_list[loc_b][1]
			is_route = False
			if not (set(trcodes_a).isdisjoint(col1i) or
			        set(trcodes_b).isdisjoint(col2i)):
				is_route = True
			if not (set(trcodes_a).isdisjoint(col1j) or
			        set(trcodes_b).isdisjoint(col2j)):
				is_route = True
			if is_route:
				if dist <= certain_dist_max:
					certain_routes.append([loc_a,loc_b])
				else:
					possible_routes.append([loc_a,loc_b])
	certain_routes.sort()
	possible_routes.sort()

def create_routes_from_pairs(hexcode_pairs):
	out_text = ""
	arrow = ""
	two_way = 0
	one_way = 0
	for pair in hexcode_pairs:
		source = pair[0]
		dest = pair[1]
		if [dest,source] in hexcode_pairs:			
			if source < dest:
				arrow = "<=>"
				two_way = two_way + 1
			else:
				continue
		else:
			one_way = one_way + 1
			if distance(source,dest) == 1:
				arrow = " ->"
			else:
				arrow = "-->"	
		out_text = out_text + "[" + source + arrow + dest + "] \t(" + system_list[source][0] + " " + arrow + " " + system_list[dest][0] + ")\n"
	out_text = out_text + "Total number of routes found: " + str(len(hexcode_pairs)) + " (two-way routes: " + str(two_way) + ", one-way routes: " + str(one_way) + ")\n\n"
	return out_text


# Pääohjelma
args = construct_args(sys.argv[1:])

raw_text = args.infile.read()
args.infile.close()

# informat
if (args.format == "UWP"):
	UWP_list = []
	for line in raw_text.splitlines():
		if line.strip() != '':
			UWP_list.append(line)
	if args.posloc and args.postrcode:
		create_from_UWP(UWP_list)
	else:
		guess_from_UWP(UWP_list)
elif (args.format == "json"):
	try:
		json_list = json.loads(raw_text)
	except ValueError as err:
		print "Json reading error: " + str(err)
		sys.exit()
	if args.posloc and args.postrcode:
		create_from_json(json_list)
	else:
		print "For json input, the -pl and -pt options need values!"
		sys.exit()	
else:
	print "Strange error in main (unknown format)" 
	sys.exit()

calculate_routes()

# Default out is text rather than a object (todo)
out_text = "Certain routes: \n" + create_routes_from_pairs(certain_routes) + "\n" + "Possible routes: " + create_routes_from_pairs(possible_routes) + "\n"

args.outfile.write(out_text)
args.outfile.close()


