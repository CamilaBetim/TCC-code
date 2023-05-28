from passlib.hash import sha256_crypt 
from flask import request
from flask import Blueprint, render_template
import mysql.connector
import os
from cryptography.fernet import Fernet

cadastro = Blueprint('cadastro', __name__, template_folder='templates')
@cadastro.route('/cadastro', defaults={'page': 'usuario'} , methods =["GET", "POST"])
def cadastro_usuario(page):

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
       first_name = request.form.get("lname")
       last_name = request.form.get("lsobrenome")
       user_password = sha256_crypt.encrypt(request.form.get("lsenha"))
       email = request.form.get("lemail")
       nickname = request.form.get("nickname")

      #Verificando se e-mail ou nickaame existe no banco de dados
       verification = "SELECT * FROM usuario WHERE email ='{}'".format(email)
       cursor.execute(verification)
       result = cursor.fetchall()
       verification_nickname = "SELECT * FROM usuario WHERE nickname ='{}'".format(nickname)
       cursor.execute(verification_nickname)
       result_nickname = cursor.fetchall()

       if len(result)!=0:  #Verifica se o retorno contém alguma linha
         return render_template(f'{page}.html', value="Conta já existente com esse e-mail."  )
       else:
         if len(result_nickname)!=0:
          return render_template(f'{page}.html', value="Nickname já em uso."  )
         else:

          #Inserindo dados no banco
          sql = "INSERT INTO usuario (nome, sobrenome, senha, email, nickname) VALUES (%s, %s, %s, %s, %s)"
          val = (first_name, last_name, user_password, email, nickname)
          cursor.execute(sql, val)
          con.commit()
          print(cursor.rowcount, "record inserted.")

          cursor.execute("SELECT idusuario FROM usuario WHERE email = %s", (email,))
          id = cursor.fetchone()[0]

          #Criando pasta no servidor de arquivos

          os.makedirs("database/"+str(id)+"/chave/")
          os.makedirs("database/"+str(id)+"/obras/")
          
          #Criando chave 
              
          path_key = 'database/'+str(id)+'/chave/key.txt'
          key = Fernet.generate_key()
          file = open(path_key, "wb")
          file.write(key) 
          file.close()

          #Inserindo caminho da chave no banco

          cursor.execute(""" UPDATE usuario SET path_key=%s WHERE idusuario=%s """, (path_key, id))
          con.commit()

          #Fechando conexão com o banco de dados
          con.close()
          return render_template(f'{page}.html', value="Cadastro realizado com sucesso!"  )

    return render_template(f'{page}.html')