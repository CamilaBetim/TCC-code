import zlib
from flask import render_template, request, Blueprint
import mysql.connector
from cryptography.fernet import Fernet
from random import randint
from stegano import lsbset
from stegano.lsbset import generators
from stegano import exifHeader
import cryptography.fernet
import os
import subprocess
import random

validacao = Blueprint('validacao', __name__, template_folder='templates')
@validacao.route('/validacao', defaults={'page': 'validacao'} , methods =["GET", "POST"])
def obra_validacao(page):

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
       
       number_folder = random.randint(0,10000)
       os.makedirs("database/tmp/"+str(number_folder)+"/")

       obra = request.files['file']
       obra.save("database/tmp/"+str(number_folder)+"/"+obra.filename)


       #Verificando extensão do arquivo de imagem

       file_extension = obra.filename.rsplit('.', 1)[1]

       #Verificando steganografia
       try:
        if file_extension == "png":
                stego_message_decode = lsbset.reveal(obra, generators.eratosthenes())
        else:
            if file_extension == "jpeg" or "jpg":
                stego_message = exifHeader.reveal(obra)
                stego_message_decode = stego_message.decode('utf_8')
        id_autor = stego_message_decode.split('\n')[0]
        id_autor = int(id_autor)
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE idusuario = %s", (id_autor,))
        validation_id = cursor.fetchone()[0]
        if validation_id == 0:
            print ("Id de usuário inexistente")
            con.close
            return render_template(f'validacao-result.html', value="Obra inválida", imagem="icone-errado.jpg")       
        else:
            id_obra = stego_message_decode.split('\n')[1]
            id_obra = int(id_obra)
            cursor.execute("SELECT COUNT(*) FROM obra WHERE id_usuario = %s and idobra = %s", (id_autor, id_obra))
            validation_id_obra = cursor.fetchone()[0]

            if validation_id_obra == 0:
                print("Id de obra inexistente")
                con.close
                return render_template(f'validacao-result.html', value="Obra inválida", imagem="icone-errado.jpg")     
            else:
                cursor.execute("SELECT path_key FROM usuario WHERE idusuario = %s", (id_autor,))
                path_key = cursor.fetchone()[0]
                key = open(path_key, "rb").read()
                encrypt_hash = (stego_message_decode.split('\n')[2]).encode(encoding = 'UTF-8')
                f = Fernet(key)
                decrypt_hash = (f.decrypt(encrypt_hash)).decode('utf_8')
                cursor.execute("SELECT hash_obra FROM obra WHERE idobra = %s", (id_obra,))
                database_hash = cursor.fetchone()[0]
                if database_hash == decrypt_hash: 
                    #Salvando obra         
                    batcmd = "certutil -hashfile " + "database/tmp/"+str(number_folder)+"/"+obra.filename + " SHA256"
                    result = subprocess.check_output(batcmd, shell=True)
                    result = result.decode("latin-1") 
                    result_hash = result.split('\n')[1]
                    cursor.execute("SELECT hash_imagem FROM obra WHERE idobra = %s", (id_obra,))
                    image_hash = cursor.fetchone()[0]
                    os.remove("database/tmp/"+str(number_folder)+"/"+obra.filename)
                    os.rmdir("database/tmp/"+str(number_folder)+"/")
                    #Validando obra
                    if image_hash == result_hash:
                        cursor.execute("SELECT nome_obra FROM obra WHERE idobra = %s", (id_obra,))
                        nome_obra = cursor.fetchone()[0]
                        cursor.execute("SELECT nome FROM usuario WHERE idusuario = %s", (id_autor,))
                        nome_autor = cursor.fetchone()[0]
                        cursor.execute("SELECT sobrenome FROM usuario WHERE idusuario = %s", (id_autor,))
                        sobrenome_autor = cursor.fetchone()[0]
                        cursor.execute("SELECT nickname FROM usuario WHERE idusuario = %s", (id_autor,))
                        nickname_autor = cursor.fetchone()[0]
                        con.close
                        return render_template(f'validacao-result.html', value=f"""Obra corresponde ao artista {nome_autor} {sobrenome_autor} com o nome "{nome_obra}" """, email=f"""Nickname: {nickname_autor}""", imagem="icon-correto.png")
                
                    else:
                        con.close
                        print("Fraude realizada na imagem, hashs não batem")
                        return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png")
                else:
                    con.close
                    return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png")
 
       except KeyError:
            print("Imagem não pertencente a plataforma")
            return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png") 
       except IndexError:
            print("Imagem não pertencente a plataforma")
            return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png") 
       except cryptography.fernet.InvalidToken:
            print("Token Fernet inválido")
            return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png")
       except zlib.error:
            print("Obra possui esteganografia de outra ferramenta")
            return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png")
       except ValueError:
            print("Foi encontrada uma string ao invés de número ao transformar valor em inteiro")
            return render_template(f'validacao-result.html', value="Obra não cadastrada no banco", imagem="icone-errado.png")
    
            
    return render_template(f'{page}.html')