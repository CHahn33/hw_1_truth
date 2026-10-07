import random
import sys

file = open(sys.argv[1])

for text in file:
	if random.random() > 0.01:
		print(text)

