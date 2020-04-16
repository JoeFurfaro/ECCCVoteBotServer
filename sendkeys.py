import smtplib, ssl
import csv

port = 465  # For SSL
password = "Dipole2001!"

# Create a secure SSL context
context = ssl.create_default_context()

with smtplib.SMTP_SSL("mail.dipole.app", port, context=context) as server:
    server.login("contact@dipole.app", password)

    voters = []
    with open("voter_data.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            voters.append(row)

    for voter in voters:
        print(voter)
        message =  "Subject: Your ECCC Voting Code\n"
        message += "From: ECCC Voting Bot <votebot@covchurch.ca>\n"
        message += "Content-type: text/html\r\n\n"
        message += "<h1>Hello " + voter[0] + " " + voter[1] + "!</h1>"
        message += "<p>Your ECCC secret voter login access code is:</p>"
        message += "<h2>" + voter[3] + "</h2>"
        message += "<p>You can log in using your access code <a href='http://192.168.2.95/ECCCVoteBotClient/'>here</a>.<p>"
        message += "<p>Blessings,</p>"
        message += "<p>ECCC Voting Bot</p>"

        server.sendmail("contact@dipole.app", voter[2], message)
