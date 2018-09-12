import sqlite3
import hashlib

FILE = "users.csv"
PATH = "/home/marcelo/Documents/Insper/Open_Source/SoftDes-Desafios/" + FILE


def add_user(user, pwd, type):
    """
    Adds user to dB

    input: username, password and type
    output: None
    """
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute(
        'Insert into USER(user,pass,type) values("{0}","{1}","{2}");'.format(user, pwd, type))
    conn.commit()
    conn.close()


with open(PATH, 'r') as file:
    LINES = file.read().splitlines()

for users in LINES:
    (user, type) = users.split(',')
    print(user)
    print(type)
    add_user(user, hashlib.md5(user.encode()).hexdigest(), type)
