import mysql.connector
from flask import Flask, request, render_template, redirect, url_for
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class BancoDeDados:
    def __init__(self):
        try:
            self.conexao = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password="Guga@123",
                database="projetinho"
            )
            self.cursor = self.conexao.cursor(dictionary=True, buffered=True)
            self.criar_tabelas()
            print("Conectado ao MySQL com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar ao Banco: {e}")

    def criar_tabelas(self):
        try:
            self.cursor.execute('''
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
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS criticas (
                    id_critica INT AUTO_INCREMENT PRIMARY KEY,
                    filme_id INT,
                    autor VARCHAR(100),
                    comentario TEXT,
                    nota INT
                )
            ''')
            self.conexao.commit()
        except Exception as e:
            print(f"Erro nas tabelas: {e}")

    def salvar_filme(self, nome, categoria, genero, imdb, imagem, sinopse):
        self.cursor.execute("SELECT id_filme FROM filmes WHERE nome_filme = %s", (nome,))
        resultado = self.cursor.fetchone()
        
        if resultado:
            return resultado['id_filme']
        
        comando = "INSERT INTO filmes (nome_filme, categoria, genero, imdb, imagem, sinopse) VALUES (%s, %s, %s, %s, %s, %s)"
        self.cursor.execute(comando, (nome, categoria, genero, imdb, imagem, sinopse))
        self.conexao.commit()
        return self.cursor.lastrowid

bd = BancoDeDados()

# --- ROTAS ---

@app.route("/")
def home():
    try:
        bd.cursor.execute("SELECT * FROM filmes ORDER BY id_filme DESC LIMIT 8")
        recomendacoes = bd.cursor.fetchall()
        return render_template('index.html', filmes=recomendacoes, lista_resultados=[], busca=None)
    except Exception as e:
        return render_template('index.html', filmes=[], lista_resultados=[], busca=None)

@app.route('/search')
def pesquisar():
    query = request.args.get('q', '')
    resultados_finais = []
    api_key_tmdb = os.getenv("TMDB_API_KEY")

    if query:
        # 1. BUSCA FILMES
        url_tmdb = "https://api.themoviedb.org/3/search/movie"
        params_tmdb = {"api_key": api_key_tmdb, "query": query, "language": "pt-BR"}
        try:
            res_f = requests.get(url_tmdb, params=params_tmdb)
            dados_f = res_f.json()
            for item in dados_f.get('results', []):
                nome = item.get('title')
                nota = str(item.get('vote_average'))
                path = item.get('poster_path')
                poster = f"https://image.tmdb.org/t/p/w500{path}" if path else "https://via.placeholder.com/150x220"
                sinopse = item.get('overview', 'Sinopse não disponível.')
                id_no_banco = bd.salvar_filme(nome, "Filme", "Geral", nota, poster, sinopse)
                resultados_finais.append({
                    "id": id_no_banco, "titulo": nome, "nota": nota, "img": poster, "sinopse": sinopse, "tipo": "filme"
                })
        except: pass

        # 2. BUSCA LIVROS
        url_books = "https://www.googleapis.com/books/v1/volumes"
        params_books = {"q": query, "maxResults": 20}
        
        
        try:
            res_l = requests.get(url_books, params=params_books)
            dados_l = res_l.json()
            for item in dados_l.get('items', []):
                info = item.get('volumeInfo', {})
                nome = info.get('title')
                sinopse = info.get('description', 'Resumo não disponível.')
                imgs = info.get('imageLinks', {})
                capa = imgs.get('thumbnail') or "https://via.placeholder.com/150x220"
                capa = capa.replace("http://", "https://")
                id_no_banco = bd.salvar_filme(nome, "Livro", "Geral", "Livro", capa, sinopse)
                resultados_finais.append({
                    "id": id_no_banco, "titulo": nome, "nota": "Livro", "img": capa, "sinopse": sinopse, "tipo": "livro"
                })
        except: pass

    return render_template('index.html', busca=query, lista_resultados=resultados_finais, filmes=[])

@app.route('/postar_critica', methods=['POST'])
def postar_critica():
    try:
        id_f = request.form.get('obra_id')
        autor = request.form.get('autor')
        comentario = request.form.get('comentario')
        if id_f and autor and comentario:
            sql = "INSERT INTO criticas (filme_id, autor, comentario, nota) VALUES (%s, %s, %s, %s)"
            bd.cursor.execute(sql, (id_f, autor, comentario, 10))
            bd.conexao.commit()
            return redirect(f'/criticas/{id_f}') 
        return redirect(url_for('home'))
    except: return redirect(url_for('home'))

@app.route('/criticas/<int:filme_id>')
def ver_criticas(filme_id):
    try:
        bd.cursor.execute("SELECT * FROM filmes WHERE id_filme = %s", (filme_id,))
        filme = bd.cursor.fetchone()
        bd.cursor.execute("SELECT autor, comentario, nota FROM criticas WHERE filme_id = %s", (filme_id,))
        criticas = bd.cursor.fetchall()
        return render_template('criticas.html', filme=filme, criticas=criticas)
    except: return "Obra não encontrada.", 404

@app.route("/sobre")
def sobre(): return render_template('sobre.html')

@app.route("/contato")
def contato(): return render_template('contato.html')

if __name__ == "__main__":
    app.run(debug=False)