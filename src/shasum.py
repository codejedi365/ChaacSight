#!/usr/bin/python

import os
import sys
import io
import hashlib
import re

class shasum:

	def sha(self, string, type=256):
		desired_fn_name = "sha"+str(type)
		if desired_fn_name not in hashlib.algorithms_available:
			raise TypeError("Hash type invalid. Provided {0}".format(desired_fn_name))

		desired_fn = getattr(hashlib, desired_fn_name)

		if not isinstance(string, str):
			raise TypeError("Must be of type string")

		obj_hash = desired_fn( bytes(string, 'utf-8'))
		return( obj_hash.hexdigest() )


	def md5(self, string):
		if not isinstance(string, str):
			raise TypeError("Must be of type string")
			
		obj_hash = hashlib.md5( bytes(string, 'utf-8'))
		return( obj_hash.hexdigest() )


	def file_sha(self, f, type=256):
		desired_fn_name = "sha"+str(type)
		if desired_fn_name not in hashlib.algorithms_available:
			raise TypeError("Hash type invalid. Provided {0}".format(desired_fn_name))

		desired_fn = getattr(hashlib, desired_fn_name)

		# handle different file sizes efficiently
		filesize = os.stat(f).st_size
		if int(filesize) > (2**29):		# file > 512MB
			obj_hash = desired_fn()
			return( self._hash_large_file(f, obj_hash) )
		else:
			return( self._hash_regular_file(f, desired_fn) )
	

	def file_md5(self, f):
		# handle different file sizes efficiently
		filesize = os.stat(f).st_size
		if int(filesize) > (2**29):		# file > 512MB
			obj_hash = hashlib.md5()      # initialize
			return( self._hash_large_file(f, obj_hash) )
		else:
			return( self._hash_regular_file(f, hashlib.md5) )


	def _hash_large_file(self, read_file, hash_obj):
		BUF_SIZE = 2 ** 16  # read file in 64kb chunks!

		try:
			if isinstance(read_file, str):
				f = open(read_file, 'rb') 
			elif not isinstance(read_file, io.RawIOBase):
				raise TypeError('File was not of type file or string')
			elif not re.match('b', read_file.mode):
				raise TypeError('File was not opened to read bytes.')
			else: # is file object
				f = read_file

		except TypeError as err:
			raise err

		else:
			while True:
				data = f.read(BUF_SIZE)
				if not data:
					break
				hash_obj.update(data)
			
		finally:
			if isinstance(read_file, str):
				f.close()

		return(hash_obj.hexdigest())
		# print("SHA1: {0}".format(sha1.hexdigest()))
	

	def _hash_regular_file(self, read_file, hash_fn):
		try:
			if isinstance(read_file, str):
				f = open(read_file, 'rb') 
			elif not isinstance(read_file, io.RawIOBase):
				raise TypeError('File was not of type file or string')
			elif not re.match('b', read_file.mode):
				raise TypeError('File was not opened to read bytes.')
			else: # is file object
				f = read_file

		except TypeError as err:
			raise err

		else:
			data = f.read()
			hash_obj = hash_fn(data)
			
		finally:
			if isinstance(read_file, str):
				f.close()

		return(hash_obj.hexdigest())
	
