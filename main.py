import os
import requests
import mysql.connector
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
#teste de alteração
app = Flask(__name__)

class BancoDeDados:
    def __init__(self):
        self.conexao = None
        self.conectar()

    def conectar(self):
        try:

            db_user = os.getenv("DB_USER")
            db_pass = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_name = os.getenv("DB_NAME")
            db_port = os.getenv("DB_PORT", "22091")

            self.conexao = mysql.connector.connect(
                host=db_host,
                port=int(db_port),
                user=db_user,
                password=db_pass,
                database=db_name,
                auth_plugin='mysql_native_password'
            )
            if self.conexao.is_connected():
                print(f"✅ CONECTADO AO BANCO DE PRODUÇÃO: {db_name}")
        except Exception as e:
            self.conexao = None

    def get_cursor(self):

        try:
            if self.conexao is None or not self.conexao.is_connected():
                self.conectar()
            if self.conexao and self.conexao.is_connected():
                return self.conexao.cursor(dictionary=True, buffered=True)
            return None
        except:
            return None

    def criar_tabelas(self):

        cur = self.get_cursor()
        if not cur: return
        try:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS filmes (
                    id_filme INT AUTO_INCREMENT PRIMARY KEY,
                    nome_filme VARCHAR(255) NOT NULL,
                    categoria VARCHAR(50),
                    genero VARCHAR(50),
                    imdb VARCHAR(10),
                    imagem TEXT,
                    sinopse TEXT
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS criticas (
                    id_critica INT AUTO_INCREMENT PRIMARY KEY,
                    filme_id INT,
                    autor VARCHAR(100),
                    comentario TEXT,
                    nota INT,
                    FOREIGN KEY (filme_id) REFERENCES filmes(id_filme)
                )
            ''')
            self.conexao.commit()
        finally:
            if cur: cur.close()

    def salvar_obra(self, nome, categoria, genero, nota, imagem, sinopse):
        cur = self.get_cursor()
        if not cur: return None
        try:
            cur.execute("SELECT id_filme FROM filmes WHERE nome_filme = %s AND categoria = %s", (nome, categoria))
            res = cur.fetchone()
            if res: return res['id_filme']
            
            sql = "INSERT INTO filmes (nome_filme, categoria, genero, imdb, imagem, sinopse) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (nome, categoria, genero, nota, imagem, sinopse))
            self.conexao.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"❌ Erro ao salvar {categoria}: {e}")
            return None
        finally:
            if cur: cur.close()


bd = BancoDeDados()

#Rotas do flask

@app.route("/")
def home():
    cur = bd.get_cursor()
    if not cur:
        return render_template('index.html', filmes=[], lista_resultados=[], busca=None, erro_db=True)
    try:
        cur.execute("SELECT * FROM filmes ORDER BY id_filme DESC LIMIT 8")
        recomendacoes = cur.fetchall()
        return render_template('index.html', filmes=recomendacoes, lista_resultados=[], busca=None)
    except:
        return render_template('index.html', filmes=[], lista_resultados=[], busca=None)
    finally:
        if cur: cur.close()

@app.route('/search')
def pesquisar():
    query = request.args.get('q', '')
    resultados_finais = []
    api_key_tmdb = os.getenv("TMDB_API_KEY")

    if query:

        if api_key_tmdb:
            try:
                res_f = requests.get("https://api.themoviedb.org/3/search/movie", params={
                    "api_key": api_key_tmdb, "query": query, "language": "pt-BR"
                }, timeout=5)
                if res_f.status_code == 200:
                    for item in res_f.json().get('results', []):
                        titulo = item.get('title')
                        nota = str(round(item.get('vote_average', 0), 1))
                        poster = item.get('poster_path')
                        img = f"https://image.tmdb.org/t/p/w500{poster}" if poster else ""
                        id_db = bd.salvar_obra(titulo, "filme", "Geral", nota, img, item.get('overview'))
                        if id_db:
                            resultados_finais.append({"id": id_db, "titulo": titulo, "nota": nota, "img": img, "tipo": "filme"})
            except: pass

        try:
            res_ol = requests.get("https://openlibrary.org/search.json", params={"q": query, "limit": 5}, timeout=10)
            if res_ol.status_code == 200:
                for item in res_ol.json().get('docs', []):
                    titulo = item.get('title')
                    cover = item.get('cover_i')
                    img = f"https://covers.openlibrary.org/b/id/{cover}-L.jpg" if cover else ""
                    id_db = bd.salvar_obra(titulo, "livro", "Geral", "Livro", img, "Sinopse em breve.")
                    if id_db:
                        resultados_finais.append({"id": id_db, "titulo": titulo, "nota": "Livro", "img": img, "tipo": "livro"})
        except: pass

    return render_template('index.html', busca=query, lista_resultados=resultados_finais, filmes=[])

@app.route('/criticas/<int:filme_id>')
def ver_criticas(filme_id):
    cur = bd.get_cursor()
    if not cur: return "Erro de conexão", 500
    try:
        cur.execute("SELECT * FROM filmes WHERE id_filme = %s", (filme_id,))
        filme = cur.fetchone()
        cur.execute("SELECT * FROM criticas WHERE filme_id = %s ORDER BY id_critica DESC", (filme_id,))
        criticas = cur.fetchall()
        return render_template('criticas.html', filme=filme, criticas=criticas)
    finally:
        if cur: cur.close()

@app.route('/postar_critica', methods=['POST'])
def postar_critica():
    cur = bd.get_cursor()
    id_f = request.form.get('obra_id')
    if not cur or not id_f: return redirect(url_for('home'))
    try:
        autor = request.form.get('autor')
        comentario = request.form.get('comentario')
        if autor and comentario:
            cur.execute("INSERT INTO criticas (filme_id, autor, comentario, nota) VALUES (%s, %s, %s, %s)", (id_f, autor, comentario, 10))
            bd.conexao.commit()
    finally:
        if cur: cur.close()
    return redirect(url_for('ver_criticas', filme_id=id_f))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)