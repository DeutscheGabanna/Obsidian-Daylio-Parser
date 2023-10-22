"""Provides a 2D array of mood groups and associated moods based on the moods.json file"""
import json

# MOODS are used to determine colour coding for the particular moods if colour = TRUE
# [0,x] - best, [4,x] - worst

with open("moods.json", encoding="UTF-8") as jsonfile:
    available_moods = json.load(jsonfile)
