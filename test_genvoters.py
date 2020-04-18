import argparse
import sys
import string
import random

def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

parser = argparse.ArgumentParser()

parser.add_argument("people", type=int)

args = parser.parse_args()

if args.people < 1:
    print("Number of people to generate must be larger than 0.")
    sys.exit()

out_file = open("voter_data.csv", "w")
codes = [""]

for i in range(args.people):
    rand_code = ""
    while rand_code in codes:
        rand_code = id_generator(6)
    codes.append(rand_code)
    out_file.write("Voter" + ",#" + str(i) + "," + "NO_EMAIL" + "," + rand_code + "\n")

out_file.close()
