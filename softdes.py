# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 09:00:39 2017

@author: rauli
"""

from flask import Flask, request, jsonify, abort, make_response, session, render_template, redirect
from flask_httpauth import HTTPBasicAuth
from datetime import datetime
import sqlite3
import json
import hashlib

DBNAME = './quiz.db'

def lambda_handler(event, context):
    try:
        import json
        import numbers

        def not_equals(first, second):
            if isinstance(first, numbers.Number) and isinstance(second, numbers.Number):
                return abs(first - second) > 1e-3
            return first != second

        # TODO implement
        ndes = int(event['ndes'])
        code = event['code']
        args = event['args']
        resp = event['resp']
        diag = event['diag']
        exec(code, locals())


        test = []
        for index, arg in enumerate(args):
            if not 'desafio{0}'.format(ndes) in locals():
                return "Nome da função inválido. Usar 'def desafio{0}(...)'".format(ndes)

            if not_equals(eval('desafio{0}(*arg)'.format(ndes)), resp[index]):
                test.append(diag[index])

        return " ".join(test)
    except:
        return "Função inválida."

def converteData(orig):
    return orig[8:10]+'/'+orig[5:7]+'/'+orig[0:4]+' '+orig[11:13]+':'+orig[14:16]+':'+orig[17:]

def getQuizes(user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user == 'admin' or user == 'fabioja':
        cursor.execute("SELECT id, numb from QUIZ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    else:
        cursor.execute("SELECT id, numb from QUIZ where release < '{0}'".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def getUsers(user):
    if user != 'admin' and user != 'fabioja':
        return []
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user from USER")
    info = [reg[0] for reg in cursor.fetchall()]
    conn.close()
    return info


def getReportData(users, challenges):
    all_user_quizzes = getAllUserQuiz()
    users_data = {user: {c[1]: {'passed': False, 'submissions': 0} for c in challenges} for user in users}
    print(users)
    for userid, numb, _sent, _answer, result in all_user_quizzes:
        user_data = users_data[userid]
        quiz_data = user_data[numb]
        quiz_data['submissions'] += 1
        if result == 'OK!':
            quiz_data['passed'] = True
        user_data[numb] = quiz_data
        users_data[userid] = user_data
    for user in users_data.values():
        for quiz_data in user.values():
            if quiz_data['submissions'] == 0:
                quiz_data['status'] = 'N/A'
                quiz_data['class'] = 'table-danger'
            elif quiz_data['passed']:
                quiz_data['status'] = 'Passou'
                quiz_data['class'] = 'table-success'
            else:
                quiz_data['status'] = 'Falhou'
                quiz_data['class'] = 'table-warning'
    return users_data


def getAllUserQuiz():
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT userid,numb,sent,answer,result from USERQUIZ INNER JOIN QUIZ on QUIZ.id = USERQUIZ.quizid order by sent desc")
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def getUserQuiz(userid, quizid):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sent,answer,result from USERQUIZ where userid = '{0}' and quizid = {1} order by sent desc".format(userid, quizid))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def setUserQuiz(userid, quizid, sent, answer, result):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    #print("insert into USERQUIZ(userid,quizid,sent,answer,result) values ('{0}',{1},'{2}','{3}','{4}');".format(userid, quizid, sent, answer, result))
    #cursor.execute("insert into USERQUIZ(userid,quizid,sent,answer,result) values ('{0}',{1},'{2}','{3}','{4}');".format(userid, quizid, sent, answer, result))
    cursor.execute("insert into USERQUIZ(userid,quizid,sent,answer,result) values (?,?,?,?,?);", (userid, quizid, sent, answer, result))
    #
    conn.commit()
    conn.close()

def getQuiz(id, user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user == 'admin' or user == 'fabioja':
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0}".format(id))
    else:
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0} and release < '{1}'".format(id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def setInfo(pwd, user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE USER set pass = ? where user = ?",(pwd, user))
    conn.commit()
    conn.close()

def getInfo(user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pass, type from USER where user = '{0}'".format(user))
    print("SELECT pass, type from USER where user = '{0}'".format(user))
    info = [reg[0] for reg in cursor.fetchall()]
    conn.close()
    if len(info) == 0:
        return None
    else:
        return info[0]

auth = HTTPBasicAuth()

app = Flask(__name__, static_url_path='')
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?TX'

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def main():
    msg = ''
    p = 1
    challenges=getQuizes(auth.username())
    sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST' and 'ID' in request.args:
        id = request.args.get('ID')
        quiz = getQuiz(id, auth.username())
        if len(quiz) == 0:
            msg = "Boa tentativa, mas não vai dar certo!"
            p = 2
            return render_template('index.html', username=auth.username(), challenges=challenges, p=p, msg=msg)


        quiz = quiz[0]
        if sent > quiz[2]:
            msg = "Sorry... Prazo expirado!"

        f = request.files['code']
        filename = './upload/{0}-{1}.py'.format(auth.username(), sent)
        f.save(filename)
        with open(filename,'r') as fp:
            answer = fp.read()

        #lamb = boto3.client('lambda')
        args = {"ndes": id, "code": answer, "args": eval(quiz[4]), "resp": eval(quiz[5]), "diag": eval(quiz[6]) }

        #response = lamb.invoke(FunctionName="Teste", InvocationType='RequestResponse', Payload=json.dumps(args))
        #feedback = response['Payload'].read()
        #feedback = json.loads(feedback).replace('"','')
        feedback = lambda_handler(args,'')


        result = 'Erro'
        if len(feedback) == 0:
            feedback = 'Sem erros.'
            result = 'OK!'

        setUserQuiz(auth.username(), id, sent, feedback, result)


    if request.method == 'GET':
        if 'ID' in request.args:
            id = request.args.get('ID')
        else:
            id = 1

    if len(challenges) == 0:
        msg = "Ainda não há desafios! Volte mais tarde."
        p = 2
        return render_template('index.html', username=auth.username(), challenges=challenges, p=p, msg=msg)
    else:
        quiz = getQuiz(id, auth.username())

        if len(quiz) == 0:
            msg = "Oops... Desafio invalido!"
            p = 2
            return render_template('index.html', username=auth.username(), challenges=challenges, p=p, msg=msg)

        answers = getUserQuiz(auth.username(), id)

    return render_template('index.html', username=auth.username(), challenges=challenges, quiz=quiz[0], e=(sent > quiz[0][2]), answers=answers, p=p, msg=msg, expi = converteData(quiz[0][2]))

@app.route('/pass', methods=['GET', 'POST'])
@auth.login_required
def change():
    if request.method == 'POST':
        velha = request.form['old']
        nova = request.form['new']
        repet = request.form['again']

        p = 1
        msg = ''
        if nova != repet:
            msg = 'As novas senhas nao batem'
            p = 3
        elif getInfo(auth.username()) != hashlib.md5(velha.encode()).hexdigest():
            msg = 'A senha antiga nao confere'
            p = 3
        else:
            setInfo(hashlib.md5(nova.encode()).hexdigest(), auth.username())
            msg = 'Senha alterada com sucesso'
            p = 3
    else:
        msg = ''
        p = 3

    return render_template('index.html', username=auth.username(), challenges=getQuizes(auth.username()), p=p, msg=msg)


@app.route('/logout')
def logout():
    return render_template('index.html',p=2, msg="Logout com sucesso"), 401

@app.route('/report')
@auth.login_required
def report():
    user = auth.username()
    if user != 'admin':
        return redirect('/')
    users = getUsers(user)
    challenges=getQuizes(auth.username())
    report_data = getReportData(users, challenges)
    return render_template('index.html', p=4, msg='', report_data=report_data, challenges=challenges)


@auth.get_password
def get_password(username):
    return getInfo(username)

@auth.hash_password
def hash_pw(password):
    return hashlib.md5(password.encode()).hexdigest()

if __name__ == '__main__':
    app.run(debug=True, host= '0.0.0.0', port=80)

