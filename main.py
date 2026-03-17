import os
import requests
import mysql.connector
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
import ssl

# Resolve problemas de certificado SSL em alguns ambientes
ssl._create_default_https_context = ssl._create_unverified_context

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
            # Verifica se já existe para evitar duplicidade
            self.cursor.execute("SELECT id_filme FROM filmes WHERE nome_filme = %s AND categoria = %s", (nome, categoria))
            res = self.cursor.fetchone()
            if res: return res['id_filme']
            
            sql = "INSERT INTO filmes (nome_filme, categoria, genero, imdb, imagem, sinopse) VALUES (%s, %s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (nome, categoria, genero, nota, imagem, sinopse))
            self.conexao.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"❌ Erro ao salvar ({categoria}): {e}")
            return None

bd = BancoDeDados()

# --- ROTAS ---

@app.route("/")
def home():
    try:
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
    api_key_google = os.getenv("GOOGLE_BOOKS_API_KEY")

    if query:
        # 1. BUSCA FILMES NO TMDB
        try:
            url_f = "https://api.themoviedb.org/3/search/movie"
            res_f = requests.get(url_f, params={
                "api_key": api_key_tmdb, 
                "query": query, 
                "language": "pt-BR"
            }, timeout=5)
            
            if res_f.status_code == 200:
                dados_f = res_f.json().get('results', [])
                for item in dados_f:
                    titulo = item.get('title', 'Título Desconhecido')
                    nota = str(round(item.get('vote_average', 0), 1))
                    poster = item.get('poster_path')
                    img = f"https://image.tmdb.org/t/p/w500{poster}" if poster else "https://via.placeholder.com/150x220"
                    sinopse = item.get('overview') or 'Sem sinopse disponível.'
                    
                    id_db = bd.salvar_obra(titulo, "filme", "Geral", nota, img, sinopse)
                    if id_db:
                        resultados_finais.append({
                            "id": id_db, "titulo": titulo, "nota": nota, "img": img, "sinopse": sinopse, "tipo": "filme"
                        })
        except Exception as e: 
            print(f"❌ Erro API Filme: {e}")

        # 2. BUSCA LIVROS NO GOOGLE BOOKS
        try:
            url_l = "https://www.googleapis.com/books/v1/volumes"
            params_l = {
                "q": query, 
                "maxResults": 10, 
                "printType": "books"
            }
            if api_key_google:
                params_l["GOOGLE_BOOKS_KEY"] = api_key_google

            res_l = requests.get(url_l, params=params_l, timeout=5)
            
            if res_l.status_code == 200:
                dados_l = res_l.json().get('items', [])
                for item in dados_l:
                    info = item.get('volumeInfo', {})
                    titulo = info.get('title', 'Título Desconhecido')
                    
                    img_links = info.get('imageLinks', {})
                    thumb = img_links.get('thumbnail') or img_links.get('smallThumbnail') or "https://via.placeholder.com/150x220"
                    img = thumb.replace("http://", "https://")
                    
                    sinopse = info.get('description') or 'Sem resumo disponível.'
                    if len(sinopse) > 1000: sinopse = sinopse[:997] + "..."
                    
                    id_db_livro = bd.salvar_obra(titulo, "livro", "Geral", "Livro", img, sinopse)
                    if id_db_livro:
                        resultados_finais.append({
                            "id": id_db_livro, "titulo": titulo, "nota": "Livro", "img": img, "sinopse": sinopse, "tipo": "livro"
                        })
            else:
                print(f"❌ Erro Google Books Status: {res_l.status_code}")
        except Exception as e: 
            print(f"❌ Erro API Livro: {e}")

    print(f"🔍 Busca por '{query}': {len(resultados_finais)} itens encontrados.")
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