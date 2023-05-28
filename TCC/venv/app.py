from flask import Flask
from cadastro import cadastro
from login import login
from criar_obra import obra
from validacao import validacao
from flask import Flask, render_template, redirect, request, session
from flask_session import Session


app = Flask(__name__)
app.register_blueprint(cadastro)
app.register_blueprint(login)
app.register_blueprint(obra)
app.register_blueprint(validacao)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)