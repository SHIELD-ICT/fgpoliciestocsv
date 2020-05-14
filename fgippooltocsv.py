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
option_1 = { 'name' : ('-o', '--output-file'), 'help' : '<OUTPUT_FILE>: output csv file (default \'./ippooles-out.csv\')', 'default' : 'ippooles-out.csv', 'nargs' : 1}
option_2 = { 'name' : ('-n', '--newline'), 'help' : '<NEWLINE> : insert a newline between each ippool for better readability', 'action' : 'store_true', 'default' : False }
option_3 = { 'name' : ('-s', '--skip-header'), 'help' : '<SKIP_HEADER> : do not print the csv header', 'action' : 'store_true', 'default' : False }

options = [option_0, option_1, option_2, option_3]

# Handful patterns
# -- Entering ippool definition block
p_entering_ippool_block = re.compile('^\s*config firewall ippool$', re.IGNORECASE)

# -- Exiting ippool definition block
p_exiting_ippool_block = re.compile('^end$', re.IGNORECASE)

# -- Commiting the current ippool definition and going to the next one
p_ippool_next = re.compile('^next$', re.IGNORECASE)

# -- Policy number
p_ippool_name = re.compile('^\s*edit\s+"(?P<ippool_name>.*)"$', re.IGNORECASE)

# -- Policy setting
p_ippool_set = re.compile('^\s*set\s+(?P<ippool_key>\S+)\s+(?P<ippool_value>.*)$', re.IGNORECASE)

# Functions
def parse(fd):
	"""
		Parse the data according to several regexes
		
		@param fd:	input file descriptor
		@rtype:	return a list of ippooles ( [ {'id' : '1', 'srcintf' : 'internal', ...}, {'id' : '2', 'srcintf' : 'external', ...}, ... ] )  
				and the list of unique seen keys ['id', 'srcintf', 'dstintf', ...]
	"""
	global p_entering_ippool_block, p_exiting_ippool_block, p_ippool_next, p_ippool_name, p_ippool_set
	
	in_ippool_block = False
	
	ippool_list = []
	ippool_elem = {}
	
	order_keys = []
	
	with open(fd,'rb') as fd_input:
		for line in fd_input:
			line = line.lstrip().rstrip().strip()
			
			# We match a ippool block
			if p_entering_ippool_block.search(line):
				in_ippool_block = True
			
			# We are in a ippool block
			if in_ippool_block:
				if p_ippool_name.search(line):
					ippool_name = p_ippool_name.search(line).group('ippool_name')
					ippool_elem['name'] = ippool_name
					if not('name' in order_keys): order_keys.append('name')
				
				# We match a setting
				if p_ippool_set.search(line):
					ippool_key = p_ippool_set.search(line).group('ippool_key')
					if not(ippool_key in order_keys): order_keys.append(ippool_key)
					
					ippool_value = p_ippool_set.search(line).group('ippool_value').strip()
					ippool_value = re.sub('["]', '', ippool_value)
					
					ippool_elem[ippool_key] = ippool_value
				
				# We are done with the current ippool id
				if p_ippool_next.search(line):
					ippool_list.append(ippool_elem)
					ippool_elem = {}
			
			# We are exiting the ippool block
			if p_exiting_ippool_block.search(line):
				in_ippool_block = False
	
	return (ippool_list, order_keys)


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
			
			for ippool in results:
				output_line = []
				
				for key in keys:
					if key in ippool.keys():
						output_line.append(ippool[key])
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
