# WS server example

import asyncio
import websockets
from votebotlib import *

async def run(socket, path):
    global session, logger
    login_type = None
    while login_type != "VOTER" and login_type != "ADMIN":
        try:
            login_type = await socket.recv();
        except:
            pass

    # Status codes
    # -> 700: Voter login failure
    # -> 705: Invalid VOTER question ID
    # -> 706: Current question is NONE
    # -> 707: Voter has already voted on question
    # -> 708: Receieved an unexpected VOTE value
    # -> 709: User is already logged in
    # -> 800: Voter login success
    # -> 801: Vote registered successfully
    if login_type == "VOTER":
        # Handle voter login
        verified = False
        while not verified:
            try:
                access_code = await socket.recv()
                voter = session.verify_voter(access_code)
                if voter == None:
                    await socket.send("700")
                    logger.log("WARNING", "VOTER login failed using access code \"" + access_code + "\"")
                    continue
                if voter in session.connected_voters:
                    # Voter is already connected
                    await socket.send("709")
                    logger.log("WARNING", "VOTER duplicate login blocked using access code \"" + access_code + "\"")
                else:
                    verified = True
            except:
                pass

        # Voter has now verified identity
        logger.log("INFO", voter.name + " has verified their VOTER identity using access code \"" + voter.access_code + "\"")
        await socket.send("800|||" + voter.name)
        session.connected_voters.add(voter)
        voter.websocket = socket
        if session.cur_question == None:
            await socket.send("NEW|||NONE|||NONE")
        else:
            await socket.send("NEW|||" + str(session.cur_question.id) + "|||" + session.cur_question.text + "|||" + str(session.has_already_voted(voter)))
        await session.send_to_admins("ONLINE|||" + str(len(session.connected_voters)))

        try:
            # Handle all voter actions
            cmd = None
            while cmd != "CLOSE":
                cmd = await socket.recv()
                if type(cmd) == str:
                    args = cmd.split("-")
                    if len(args) > 0 and args[0] != "":
                        # Process voter commands here
                        if args[0] == "VOTE":
                            try:
                                question_id = int(args[1])
                                value = args[2]
                                if session.get_question(question_id) != None:
                                    if session.cur_question != None:
                                        if not session.has_already_voted(voter):
                                            # Validate VOTE value
                                            if value in ("IN_FAVOUR", "OPPOSED", "ABSTAIN"):
                                                # Process vote
                                                session.cur_question.votes.append(Vote(voter, value))
                                                await socket.send("801")
                                                stats = session.vote_stats(session.cur_question)
                                                await session.send_to_admins("STATS|||" + str(session.cur_question.id) + "|||" + str(stats[0]) + "|||" + str(stats[1]) + "|||" + str(stats[2]) + "|||" + str(stats[3]) + "|||" + str(stats[4]) + "|||" + str(stats[5]))
                                                logger.log("INFO", voter.name + " has voted \"" + value + "\"")
                                            else:
                                                await socket.send("708")
                                        else:
                                            await socket.send("707")
                                    else:
                                        await socket.send("706")
                                else:
                                    await socket.send("705")
                            except:
                                await socket.send("705")
        except Exception:
            pass
        finally:
            # Remove voter from connected list
            session.connected_voters.remove(voter)
            voter.websocket = None
            await session.send_to_admins("ONLINE|||" + str(len(session.connected_voters)))
            logger.log("INFO", "VOTER " + voter.name + " disconnected")

    # Status codes
    # -> 701: Admin login failure
    # -> 702: Invalid new current question ID
    # -> 703: Admin command not found
    # -> 704: Tried to reset currently active question
    # -> 710: Admin is already connected
    # -> 802: Question changed successfully
    # -> 803: Question cleared successfully
    # -> 804: Question votes reset successfully
    # -> 805: Admin login success
    elif login_type == "ADMIN":
        # Handle admin login
        verified = False
        while not verified:
            try:
                access_code = await socket.recv()
                admin = session.verify_admin(access_code)
                if admin == None:
                    await socket.send("701")
                    logger.log("WARNING", "ADMIN login failed using access code \"" + access_code + "\"")
                    continue
                if admin in session.connected_admins:
                    # Admin is already connected
                    await socket.send("710")
                    logger.log("WARNING", "ADMIN duplicate login blocked using access code \"" + access_code + "\"")
                else:
                    verified = True
            except:
                pass

        # Admin has now verified identity
        await socket.send("805|||" + admin.name)
        logger.log("INFO", admin.name + " has verified their ADMIN identity using access code \"" + admin.access_code + "\"")
        session.connected_admins.add(admin)
        admin.websocket = socket
        if session.cur_question == None:
            await socket.send("NEW|||NONE|||NONE")
        else:
            await socket.send("NEW|||" + str(session.cur_question.id) + "|||" + session.cur_question.text)

        for question in session.questions:
            stats = session.vote_stats(question)
            await socket.send("REG|||" + str(question.id) + "|||" + str(question.text) + "|||" + str(stats[0]) + "|||" + str(stats[1]) + "|||" + str(stats[2]) + "|||" + str(stats[3]) + "|||" + str(stats[4]) + "|||" + str(stats[5]))
        await socket.send("ONLINE|||" + str(len(session.connected_voters)))

        try:
            # Handle all admin actions
            cmd = None
            while cmd != "CLOSE":
                cmd = await socket.recv()
                if type(cmd) == str:
                    args = cmd.split("-")
                    if len(args) > 0 and args[0] != "":
                        # Process admin commands here
                        if args[0] == "CUR":
                            # Change current question
                            try:
                                new_question_id = int(args[1])
                                assert(session.set_current_question(new_question_id))
                                question = session.get_question(new_question_id)
                                for voter in session.connected_voters:
                                    await voter.websocket.send("NEW|||" + str(new_question_id) + "|||" + question.text + "|||" + str(session.has_already_voted(voter)))
                                await session.send_to_admins("NEW|||" + str(new_question_id) + "|||" + question.text)
                                await socket.send("802")
                                logger.log("INFO", admin.name + " has changed the question ID to " + str(new_question_id))
                            except:
                                await socket.send("702")
                        elif args[0] == "CLR":
                            # Clear current question
                            session.clear_question()
                            await session.send_to_all("NEW|||NONE|||NONE")
                            await socket.send("803")
                            logger.log("INFO", admin.name + " has cleared the current question")
                        elif args[0] == "RESET":
                            question_id = int(args[1])
                            if session.cur_question == None or session.cur_question.id != question_id:
                                assert(session.reset_question(question_id))
                                await socket.send("804")
                                question = session.get_question(question_id)
                                stats = session.vote_stats(question)
                                await session.send_to_admins("STATS|||" + str(question_id) + "|||" + str(stats[0]) + "|||" + str(stats[1]) + "|||" + str(stats[2]) + "|||" + str(stats[3]) + "|||" + str(stats[4]) + "|||" + str(stats[5]))
                                logger.log("INFO", admin.name + " has reset the votes on question " + str(question_id))
                            else:
                                await socket.send("704")
                        else:
                            await socket.send("703")
        except Exception:
            pass
        finally:
            # Remove admin from connected list
            admin.websocket = None
            session.connected_admins.remove(admin)
            logger.log("INFO", "ADMIN " + admin.name + " disconnected")


logger = VoteBotLogger()

admin = Admin("Joe", "Furfaro", "secret123")

voter = Voter("Joe", "Furfaro", "joe@dipole.app", "democracy")
voter2 = Voter("Adam", "Furfaro", "adamfurfaro@gmail.com", "right?")
voter3 = Voter("Paula", "Furfaro", "peabee2@gmail.com", "tuna")
voter4 = Voter("Lilli", "Furfaro", "lillifurfaro@gmail.com", "lilli")
voter5 = Voter("Glenn", "Peterson", "glenn@covchurch.ca", "jonas")

question_1 = Question(1, "What is your favourite colour?")
question_2 = Question(2, "Peanut butter jelly time")

session = VotingSession([admin], [voter, voter2, voter3, voter4, voter5], [question_1, question_2])

try:
    print("Starting ECCCVoteBotServer...")
    start_server = websockets.serve(run, "192.168.2.95", 8765)
    print("Running!")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    logger.close()
