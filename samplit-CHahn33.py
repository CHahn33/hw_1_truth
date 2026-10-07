import random
import sys

file = open(sys.argv[1])

for line in file:
	if random.random() > 0.01:
		print(line)
