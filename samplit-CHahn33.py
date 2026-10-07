import random
import sys

file = open(sys.argv[1])

for row in file:
	if random.random() > 0.01:
		print(row)
