#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of fgpoliciestocsv.
#
# Copyright (C) 2014, Thomas Debize <tdebize at mail.com>
# All rights reserved.
#
# fgpoliciestocsv is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fgpoliciestocsv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with fgpoliciestocsv.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import sys
import csv

# OptionParser imports
from optparse import OptionParser

# Options definition
option_0 = { 'name' : ('-i', '--input-file'), 'help' : '<INPUT_FILE>: Fortigate configuration file. Ex: fgfw.cfg', 'nargs' : 1}
option_1 = { 'name' : ('-o', '--output-file'), 'help' : '<OUTPUT_FILE>: output csv file (default \'./interfacees-out.csv\')', 'default' : 'interfacees-out.csv', 'nargs' : 1}
option_2 = { 'name' : ('-n', '--newline'), 'help' : '<NEWLINE> : insert a newline between each interface for better readability', 'action' : 'store_true', 'default' : False }
option_3 = { 'name' : ('-s', '--skip-header'), 'help' : '<SKIP_HEADER> : do not print the csv header', 'action' : 'store_true', 'default' : False }

options = [option_0, option_1, option_2, option_3]

# Handful patterns
# -- Entering interface definition block
p_entering_interface_block = re.compile('^\s*config system interface$', re.IGNORECASE)

# -- Exiting interface definition block
p_exiting_interface_block = re.compile('^end$', re.IGNORECASE)

# -- Commiting the current interface definition and going to the next one
p_interface_next = re.compile('^next$', re.IGNORECASE)

# -- Policy number
p_interface_name = re.compile('^\s*edit\s+"(?P<interface_name>.*)"$', re.IGNORECASE)

# -- Policy setting
p_interface_set = re.compile('^\s*set\s+(?P<interface_key>\S+)\s+(?P<interface_value>.*)$', re.IGNORECASE)

# Functions
def parse(fd):
	"""
		Parse the data according to several regexes
		
		@param fd:	input file descriptor
		@rtype:	return a list of interfacees ( [ {'id' : '1', 'srcintf' : 'internal', ...}, {'id' : '2', 'srcintf' : 'external', ...}, ... ] )  
				and the list of unique seen keys ['id', 'srcintf', 'dstintf', ...]
	"""
	global p_entering_interface_block, p_exiting_interface_block, p_interface_next, p_interface_name, p_interface_set
	
	in_interface_block = False
	
	interface_list = []
	interface_elem = {}
	
	order_keys = []
	
	with open(fd,'rb') as fd_input:
		for line in fd_input:
			line = line.lstrip().rstrip().strip()
			
			# We match a interface block
			if p_entering_interface_block.search(line):
				in_interface_block = True
			
			# We are in a interface block
			if in_interface_block:
				if p_interface_name.search(line):
					interface_name = p_interface_name.search(line).group('interface_name')
					interface_elem['name'] = interface_name
					if not('name' in order_keys): order_keys.append('name')
				
				# We match a setting
				if p_interface_set.search(line):
					interface_key = p_interface_set.search(line).group('interface_key')
					if not(interface_key in order_keys): order_keys.append(interface_key)
					
					interface_value = p_interface_set.search(line).group('interface_value').strip()
					interface_value = re.sub('["]', '', interface_value)
					
					interface_elem[interface_key] = interface_value
				
				# We are done with the current interface id
				if p_interface_next.search(line):
					interface_list.append(interface_elem)
					interface_elem = {}
			
			# We are exiting the interface block
			if p_exiting_interface_block.search(line):
				in_interface_block = False
	
	return (interface_list, order_keys)


def generate_csv(results, keys, fd, newline, skip_header):
	"""
		Generate a plain ';' separated csv file

		@param fd : output file descriptor
	"""
	if results and keys:
		with open(fd,'wb') as fd_output:
			spamwriter = csv.writer(fd_output, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
			
			if not(skip_header):
				spamwriter.writerow(keys)
			
			for interface in results:
				output_line = []
				
				for key in keys:
					if key in interface.keys():
						output_line.append(interface[key])
					else:
						output_line.append('')
			
				spamwriter.writerow(output_line)
				if newline: spamwriter.writerow('')		
		
		fd_output.close()
	
	return

def main(options, arguments):
	"""
		Dat main
	"""
	if (options.input_file == None):
		parser.error('Please specify a valid input file')
				
	results, keys = parse(options.input_file)
	generate_csv(results, keys, options.output_file, options.newline, options.skip_header)
	
	return
	

if __name__ == "__main__" :
	parser = OptionParser()
	for option in options:
		param = option['name']
		del option['name']
		parser.add_option(*param, **option)

	options, arguments = parser.parse_args()
	main(options, arguments)
