import argparse
import websockets
import asyncio
import csv
import random
import threading

parser = argparse.ArgumentParser()

parser.add_argument("address")
parser.add_argument("port", type=int)

args = parser.parse_args()

voters = []
with open("voter_data.csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        voters.append(row)

async def proc_msg(socket):
    msg = await socket.recv()
    msg_args = msg.split("|||")
    if msg_args[0] == "NEW":
        # handle new
        if msg_args[1] != "NONE":
            qargs = msg_args[1].split("%%")
            qid = qargs[0]
            qtext = qargs[1]
            qoptions = qargs[2:]
            option_to_choose = qoptions[random.randrange(0, len(qoptions))]
            await socket.send("VOTE-" + qid + "-" + option_to_choose)

    await proc_msg(socket)

async def bot_client(voter):
    url = "ws://" + args.address + ":" + str(args.port)
    async with websockets.connect(url) as socket:
        await socket.send("VOTER")
        await socket.send(voter[3])

        await proc_msg(socket)

def open_bot(*args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(bot_client(args))

for voter in voters:
    x = threading.Thread(target=open_bot, args=(voter))
    x.start()
