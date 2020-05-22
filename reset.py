import sys

session_name = input("Enter a session name to reset: ")

try:
    with open("results/attendance/" + session_name + ".txt", "r") as file:
        pass
    with open("results/attendance/" + session_name + ".txt", "w") as file:
        file.write("")
    with open("results/tallies/" + session_name + ".txt", "w") as file:
        file.write("")
    with open("results/votes/" + session_name + ".txt", "w") as file:
        file.write("")
except Exception as e:
    print("No session data was found for the name '" + session_name + "'")
    sys.exit(0)

print("Session reset successfully")