from datetime import datetime
import asyncio
import websockets

class Voter():
    def __init__(self, first_name, last_name, email, access_code, ID):
        self.id = ID
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.access_code = access_code
        self.name = first_name + " " + last_name
        self.websocket = None

class Admin():
    def __init__(self, first_name, last_name, access_code):
        self.first_name = first_name
        self.last_name = last_name
        self.access_code = access_code
        self.name = first_name + " " + last_name
        self.websocket = None

class VotingSession():
    def __init__(self, name, admins, voters, questions):
        self.name = name
        self.questions = questions
        self.voters = voters
        self.admins = admins
        self.connected_voters = set()
        self.connected_admins = set()
        self.attendance_list = set()
        self.cur_question = None

    def load(self):
        attendance_file = open("results/attendance/" + self.name + ".txt", "r")
        votes_file = open("results/votes/" + self.name + ".txt", "r")

        attendance_lines = [x.strip() for x in attendance_file.readlines()]
        attendance_file.close()

        for row in attendance_lines:
            voter = self.get_voter_by_id(int(row))
            if voter != None:
                self.attendance_list.add(voter)

        vote_lines = [x.strip() for x in votes_file.readlines()]
        votes_file.close()

        cur_q = None
        data = []
        for line in vote_lines:
            if cur_q == None:
                cur_q = self.get_question(int(line))
            elif len(data) < 2:
                data.append(line)
            elif len(data) == 2:
                voter = self.get_voter_by_id(int(data[0]))
                cur_q.votes.append(Vote(voter, data[1]))
                data = []

            if line == "--":
                cur_q = None
                data = []

    def save(self):
        attendance_file = open("results/attendance/" + self.name + ".txt", "w")
        tallies_file = open("results/tallies/" + self.name + ".txt", "w")
        votes_file = open("results/votes/" + self.name + ".txt", "w")

        for voter in self.attendance_list:
            attendance_file.write(str(voter.id))
        
        attendance_file.close()

        for question in self.questions:
            stats = self.vote_stats(question)
            tallies_file.write("[#" + str(question.id) + "] " + question.text + "\n")
            for i,option in enumerate(question.options):
                tallies_file.write("    " + option + ": " + str(stats[i]) + "\n")
            tallies_file.write("    " + "Did not vote: " + str(stats[-3]) + "\n")
            tallies_file.write("    " + "Total voters: " + str(stats[-2]) + "\n")
            tallies_file.write("    " + "Participation: " + str(stats[-1]) + "%" + "\n\n")
        
        tallies_file.write("Attendance list:\n")
        for voter in self.attendance_list:
            tallies_file.write("    " + voter.name)

        tallies_file.close()

        for question in self.questions:
            votes_file.write(str(question.id) + "\n")
            for vote in question.votes:
                votes_file.write(str(vote.voter.id) + "\n")
                votes_file.write(vote.value + "\n")
            votes_file.write("--\n")

        votes_file.close()

    def vote_stats(self, question):
        did_not_vote = len(self.voters) - len(question.votes)
        stats = question.vote_stats()
        total_voters = sum(list(stats.values()))
        perc_voted = round(100 * total_voters / len(self.voters), 1)
        return list(stats.values()) + [did_not_vote, total_voters, perc_voted]

    def vote_stats_str(self, question):
        stats = self.vote_stats(question)
        stat_str = ""
        for i,stat in enumerate(stats):
            stat_str += str(stat)
            if i < len(stats) - 1:
                stat_str += "%%"
        return stat_str

    async def send_to_voters(self, data):
        for voter in self.connected_voters:
            await voter.websocket.send(data)

    async def send_to_admins(self, data):
        for admin in self.connected_admins:
            await admin.websocket.send(data)

    async def send_to_all(self, data):
        await self.send_to_voters(data)
        await self.send_to_admins(data)

    def get_voter_by_id(self, id):
        for voter in self.voters:
            if voter.id == id:
                return voter
        return None

    def clear_question(self):
        self.cur_question = None

    def reset_question(self, id):
        for question in self.questions:
            if question.id == id:
                question.votes = []
                return True
        return False

    def set_current_question(self, id):
        for question in self.questions:
            if question.id == id:
                self.cur_question = question
                return True
        return False

    def get_question(self, id):
        for question in self.questions:
            if question.id == id:
                return question
        return None

    def get_voter(self, access_code):
        for voter in self.voters:
            if voter.access_code == access_code:
                return voter
        return None

    def get_admin(self, access_code):
        for admin in self.admins:
            if admin.access_code == access_code:
                return admin
        return None

    def verify_voter(self, access_code):
        if type(access_code) == str:
            try:
                voter = self.get_voter(access_code)
                if voter != None:
                    return voter
            except:
                return None
        return None

    def verify_admin(self, access_code):
        if type(access_code) == str:
            try:
                admin = self.get_admin(access_code)
                if admin != None:
                    return admin
            except:
                return None
        return None

    def has_already_voted(self, voter):
        if self.cur_question == None:
            return None
        for vote in self.cur_question.votes:
            if vote.voter == voter:
                return True
        return False

class Question():
    def __init__(self, id, text, options):
        self.id = id
        self.text = text
        self.votes = []
        self.options = options

    def vote_stats(self):
        results = {}
        for option in self.options:
            results[option] = 0
        for vote in self.votes:
            if vote.value in self.options:
                results[vote.value] += 1
        return results

    def __str__(self):
        text = str(self.id) + "%%" + self.text + "%%"
        for i,option in enumerate(self.options):
            text += option
            if i < len(self.options) - 1:
                text += "%%"
        return text

class Vote():
    def __init__(self, voter, value):
        self.voter = voter
        self.value = value

class VoteBotLogger():
    def __init__(self):
        # Create new log file here
        self.name_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.log_file = open("logs/" + self.name_str + ".log", "a")
        self.log("INFO", "Starting logger")

    def save_results(self, session):
        file = open("results/" + self.name_str + ".txt", "w")
        file.write("---------------------------------------------------------\n")
        for question in session.questions:
            stats = session.vote_stats(question)
            file.write("[#" + str(question.id) + "] " + question.text + "\n")
            for i,option in enumerate(question.options):
                file.write("        " + option + ": " + str(stats[i]) + "\n")
            file.write("        " + "Did not vote: " + str(stats[-3]) + "\n")
            file.write("        " + "Total voters: " + str(stats[-2]) + "\n")
            file.write("        " + "Participation : " + str(stats[-1]) + "%" + "\n")
            file.write("---------------------------------------------------------\n")
        file.write("\nAttendance List:\n\n")
        for voter in session.attendance_list:
            file.write("        " + voter.name + "\n")
        file.close()

    def log(self, type, message):
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        log_str = "[" + now_str + "] [" + type + "] " + message
        print(log_str)
        self.log_file.write(log_str + "\n")

    def close(self):
        self.log("INFO", "Closing logger")
        self.log_file.close()
