import csv
import requests
import logging

logging.basicConfig(filename="mail.log", level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def send_key(api_key, email_address, name, key):
    return requests.post(
        "https://api.mailgun.net/v3/mg.eccc.reeve.tech/messages",
        auth=("api", api_key),
        data={"from": "ECCC Voting Services <votebot@reeve.tech>",
              "to": [name, email_address],
              "subject": "Your ECCC Voting Session Invitation",
              "html": "<h1>Hello " + name + "!</h1>" +
              "<p>Your ECCC secret voter login access code is:</p>" +
              "<h2>" + key + "</h2>" +
              "<p>You can sign in using your access code <a href='https://eccc.reeve.tech'>here</a> when the voting session is ready.<p>" +
              "<p>Blessings,</p>" +
              "<p>ECCC Voting Bot</p>"
        })

key_file = open("mailgun.key")
mailgun_key = [x.strip() for x in key_file.readlines()][0]
key_file.close()

voters = []
with open("voter_data.csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        voters.append(row)

print("Attempting to deliver mail...")
logging.info("Starting mailing job...")

for voter in voters:
    result = send_key(mailgun_key, voter[2], voter[0] + " " + voter[1], voter[3])
    logging.info(voter[2] + ": " + str(result))

logging.info("Job complete.")

print("DONE! Check mail.log for status.")
