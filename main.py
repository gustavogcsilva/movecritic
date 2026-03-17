import os
import requests
import mysql.connector
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class BancoDeDados:
    def __init__(self):
        try:
            self.conexao = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', 24675)),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME', 'defaultdb')
            )
            self.cursor = self.conexao.cursor(dictionary=True, buffered=True)
            self.criar_tabelas()
            print("✅ Conectado ao MySQL com sucesso!")
        except Exception as e:
            print(f"❌ Erro de Conexão: {e}")

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
                    nota INT,
                    FOREIGN KEY (filme_id) REFERENCES filmes(id_filme)
                )
            ''')
            self.conexao.commit()
        except Exception as e:
            print(f"❌ Erro Tabelas: {e}")

    def salvar_obra(self, nome, categoria, genero, nota, imagem, sinopse):
        try:
            self.cursor.execute("SELECT id_filme FROM filmes WHERE nome_filme = %s AND categoria = %s", (nome, categoria))
            res = self.cursor.fetchone()
            if res: return res['id_filme']
            
            sql = "INSERT INTO filmes (nome_filme, categoria, genero, imdb, imagem, sinopse) VALUES (%s, %s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (nome, categoria, genero, nota, imagem, sinopse))
            self.conexao.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return None

bd = BancoDeDados()

# --- ROTAS ---

@app.route("/")
def home():
    try:
        # Ordem cronológica para Recomendações
        bd.cursor.execute("SELECT * FROM filmes ORDER BY id_filme DESC LIMIT 8")
        recomendacoes = bd.cursor.fetchall()
        return render_template('index.html', filmes=recomendacoes, lista_resultados=[], busca=None)
    except Exception as e:
        print(f"Erro Home: {e}")
        return render_template('index.html', filmes=[], lista_resultados=[], busca=None)

@app.route('/search')
def pesquisar():
    query = request.args.get('q', '')
    resultados_finais = []
    api_key_tmdb = os.getenv("TMDB_API_KEY")

    if query:
        # 1. BUSCA FILMES NO TMDB
        try:
            url_f = "https://api.themoviedb.org/3/search/movie"
            res_f = requests.get(url_f, params={"api_key": api_key_tmdb, "query": query, "language": "pt-BR"})
            dados_f = res_f.json().get('results', [])
            
            for item in dados_f:
                titulo = item.get('title')
                nota = str(round(item.get('vote_average', 0), 1))
                img = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else "https://via.placeholder.com/150x220"
                sinopse = item.get('overview', 'Sem sinopse.')
                
                id_db = bd.salvar_obra(titulo, "filme", "Geral", nota, img, sinopse)
                resultados_finais.append({
                    "id": id_db, "titulo": titulo, "nota": nota, "img": img, "sinopse": sinopse, "tipo": "filme"
                })
        except Exception as e: print(f"Erro Filme: {e}")

        # 2. BUSCA LIVROS NO GOOGLE BOOKS
        try:
            url_l = "https://www.googleapis.com/books/v1/volumes"
            res_l = requests.get(url_l, params={"q": query, "maxResults": 10})
            dados_l = res_l.json().get('items', [])
            
            for item in dados_l:
                info = item.get('volumeInfo', {})
                titulo = info.get('title')
                img = (info.get('imageLinks', {}).get('thumbnail') or "https://via.placeholder.com/150x220").replace("http://", "https://")
                sinopse = info.get('description', 'Sem resumo disponível.')
                
                id_db = bd.salvar_obra(titulo, "livro", "Geral", "Livro", img, sinopse)
                resultados_finais.append({
                    "id": id_db, "titulo": titulo, "nota": "Livro", "img": img, "sinopse": sinopse, "tipo": "livro"
                })
        except Exception as e: print(f"Erro Livro: {e}")


    resultados_finais.reverse()
    return render_template('index.html', busca=query, lista_resultados=resultados_finais, filmes=[])

@app.route('/criticas/<int:filme_id>')
def ver_criticas(filme_id):
    try:
        bd.cursor.execute("SELECT * FROM filmes WHERE id_filme = %s", (filme_id,))
        filme = bd.cursor.fetchone()
        bd.cursor.execute("SELECT * FROM criticas WHERE filme_id = %s ORDER BY id_critica DESC", (filme_id,))
        criticas = bd.cursor.fetchall()
        return render_template('criticas.html', filme=filme, criticas=criticas)
    except Exception as e:
        print(f"Erro Críticas: {e}")
        return "Obra não encontrada.", 404

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
    except Exception as e:
        print(f"Erro Postar: {e}")
        return redirect(url_for('home'))

@app.route("/sobre")
def sobre(): return render_template('sobre.html')

@app.route("/contato")
def contato(): return render_template('contato.html')

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)