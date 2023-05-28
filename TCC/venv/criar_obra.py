from flask import Flask, render_template, request, session, Blueprint
import mysql.connector
import os
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import hashlib
import hmac
from stegano import lsbset
from stegano.lsbset import generators
from stegano import exifHeader
import os
import subprocess

obra = Blueprint('cadastro_obra', __name__, template_folder='templates')
@obra.route('/cadastro_obra', defaults={'page': 'obra'} , methods =["GET", "POST"])
def obra_cadastro(page):

    #Abrindo conexão com o banco
    con = mysql.connector.connect(host='localhost',database='plataforma',user='root',password='****')
    if con.is_connected():
        db_info = con.get_server_info()
        print("Conectado ao servidor MySQL versão ",db_info)
        cursor = con.cursor()
        cursor.execute("select database();")
        linha = cursor.fetchone()
        print("Conectado ao banco de dados ",linha)

    #Coletando dados do formulário
    if request.method == "POST":

       name_obra = request.form.get("lobra")

       descricao_obra = request.form.get("descricao")

       obra = request.files['file']

       id = (session["id"])

      
      #Verificando extensão do arquivo de imagem

       file_extension = obra.filename.rsplit('.', 1)[1]

      #Verificando se obra já existe no banco com esse nome
       nome_obra = name_obra.replace(" ", "_")
       cursor.execute("SELECT COUNT(*) FROM obra WHERE id_usuario = %s and nome_obra = %s", (id, nome_obra))
       verify = cursor.fetchone()[0]
       if verify == 0:
         nome_obra_extension = nome_obra+'.'+file_extension
       else:
         count = verify + 1
         nome_obra_extension = nome_obra+str(count)+'.'+file_extension

      #Salvando obra no servidor de arquivos
       obra.filename = nome_obra_extension
       filename = (secure_filename(obra.filename))
       path_image = 'database/'+str(id)+'/obras/'
       path_image_database = 'database/'+str(id)+'/obras/'+nome_obra_extension
       obra.save(os.path.join(path_image, filename))


      #Salvando dados no banco
       if descricao_obra:
        sql = "INSERT INTO obra (nome_obra, desc_obra, obra_image, id_usuario) VALUES (%s, %s, %s, %s)"
        val = (name_obra, descricao_obra, path_image_database, id)
       else:
        sql = "INSERT INTO obra (nome_obra, obra_image, id_usuario) VALUES (%s, %s, %s)"
        val = (name_obra, path_image_database, id)
       cursor.execute(sql, val)
       con.commit()
       print(cursor.rowcount, "record inserted.")

      #Recuperando id da obra
       cursor.execute("SELECT idobra FROM obra WHERE id_usuario = %s and obra_image = %s", (id, path_image_database))
       id_obra = cursor.fetchone()[0]

      #Criando dados para esteganografia
       final_id = str(id).zfill(64)

       final_id_obra = str(id_obra).zfill(64)

      #Recuperando chave
       cursor.execute("SELECT path_key FROM usuario WHERE idusuario = %s", (id,))
       path_key = cursor.fetchone()[0]
         
       key = open(path_key, "rb").read() 

      #Criando hash junção do id_obra + id_autor
       juncao = str(id)+str(id_obra)
       juncao_hash = hmac.new(key, juncao.encode(), hashlib.sha256)
       juncao_hash = juncao_hash.hexdigest()

      #Guardando hash no banco de dados
       cursor.execute(""" UPDATE obra SET hash_obra=%s WHERE idobra=%s """, (juncao_hash, id_obra))
       con.commit()

      #Criptografando hash
       juncao_encode = juncao_hash.encode()
       f = Fernet(key)
       encrypted_message = f.encrypt(juncao_encode)
       encrypted_message_decode = encrypted_message.decode("utf-8") 
      
      #Salvando conteúdo em uma variável
       stegno_string = """{final_id}
{final_id_obra} 
{encrypted_message_decode} """.format(vars="variables", final_id=final_id, final_id_obra=final_id_obra, encrypted_message_decode=encrypted_message_decode)
       
      #Passando criptografia para a obra
       if file_extension == "png":
        stegano_image = lsbset.hide(path_image_database, stegno_string, generators.eratosthenes())
        stegano_image.save(path_image_database)
       else:
          if file_extension == "jpeg" or "jpg":
            stegano_image = exifHeader.hide(path_image_database, path_image_database, secret_message=stegno_string)

       #Gerando hash da obra e guardando no banco
       batcmd = "certutil -hashfile " + path_image_database + " SHA256"
       result = subprocess.check_output(batcmd, shell=True)
       result = result.decode("latin-1") 
       result_hash = result.split('\n')[1]
       
       cursor.execute(""" UPDATE obra SET hash_imagem=%s WHERE idobra=%s """, (result_hash, id_obra))
       con.commit()
  
       return render_template(f'{page}.html', value="Obra cadastrada com sucesso") 
      
      #Fechando conexão com o banco de dados
       con.close()     
    return render_template(f'{page}.html')