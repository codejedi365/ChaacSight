#!/usr/bin/python

import math

class geolib:

	@classmethod
	def haversine(cls, lat1, lon1, lat2, lon2):
		''' 
		   Haversine computes the distance (km) between 2 locations
		   on a globe using their latitude and longitude coordinates
		'''
		lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])    
		dlon = lon2 - lon1
		dlat = lat2 - lat1    
		a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
		return 2 * 6371 * math.asin(math.sqrt(a))
	
	@classmethod
	def geo_distance(cls, loc1coords, loc2coords ):
		'''
			Find geographic distance between to geographic coordinates on the Earth
			loc1coords = Location 1 [lat, long] list
			loc2coords = Location 2 [lat, long] list
		'''
		i_lat = 0  # list position
		i_lng = 1  # list position
		dist = geolib.haversine(
			float(loc1coords[i_lat]), 
			float(loc1coords[i_lng]),
			float(loc2coords[i_lat]), 
			float(loc2coords[i_lng])
		)
		return dist

