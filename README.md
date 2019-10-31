# ChaacSight

ChaacSight is intended to predict the rainfall amounts per month for certain physical locations (such as the state of North Carolina) for the next 50 years. The data comes from NOWData hosted by NOAA. A sarima model predicts the 95% confidence intervals for the next 50 years using monthly rainfall data from January 1980 to April 2019. Data was sourced from 112 different locations in North Carolina and 10 external locations from South Carolina and Tennessee.

Requirements: 
 - Raw rainfall measurements 
 - Corresponding Latitude and Longtitude values of measured locations
 - The more surrounding location data possible improves each estimate nearby
