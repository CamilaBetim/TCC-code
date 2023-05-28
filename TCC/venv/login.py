from passlib.hash import sha256_crypt 
from flask import request
from flask import Blueprint
import mysql.connector
from flask import render_template, redirect, request, session, url_for

login = Blueprint('login', __name__, template_folder='templates')
@login.route('/', defaults={'page': 'login'} , methods =["GET", "POST"])
def logar(page):
    
    #Abrindo conexão com o banco
    con = mysql.connector.connect(host='localhost',database='plataforma',user='root',password='****')
    if con.is_connected():
        db_info = con.get_server_info()
        print("Conectado ao servidor MySQL versão ",db_info)
        cursor = con.cursor(buffered=True)
        cursor.execute("select database();")
        linha = cursor.fetchone()
        print("Conectado ao banco de dados ",linha)

    #Capturando dados do usuário
    if request.method == "POST":

       email = request.form.get("email")

       user_password = request.form.get("senha")

       cursor.execute('SELECT * FROM usuario WHERE email = %s', (email,))

       account = cursor.fetchone()
    
    #Validando se conta existe no banco
       if account:
          cursor.execute("SELECT senha FROM usuario WHERE email = %s", (email,))
          password = cursor.fetchone()[0]

          #Validando se é a senha correta
          validatePassword = sha256_crypt.verify(user_password, password)

          if validatePassword:
            cursor.execute("SELECT idusuario FROM usuario WHERE email = %s", (email,))
            session["id"]= cursor.fetchone()[0]
            #Login realizado com sucesso
            return redirect(url_for('cadastro_obra.obra_cadastro'))
          else:
            #Senha incorreta
            con.close
            return render_template(f'{page}.html', value="Senha incorreta")
       else:
        #Usuário inexistente
        con.close
        return render_template(f'{page}.html', value="Usuário inexistente")
    
    con.close
    return render_template(f'{page}.html')
    