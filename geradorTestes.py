def main():

	import random
	import string

	file = open("teste.txt", 'w')
	for count in range(999999):
		c = random.choice(string.printable)
		file.write(str(c))
	file.close()

main()