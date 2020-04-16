import random
import string
import csv

def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

voters = []
with open("voter_input.csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        voters.append(row)

out_file = open("voter_data.csv", "w")

codes = [""]

for voter in voters[1:]:
    rand_code = ""
    while rand_code in codes:
        rand_code = id_generator(8)
    codes.append(rand_code)
    out_file.write(voter[0] + "," + voter[1] + "," + voter[2] + "," + rand_code + "\n")

out_file.close()
