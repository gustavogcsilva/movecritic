import os
import requests
import mysql.connector
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
import ssl

<<<<<<< HEAD
# Resolve problemas de certificado SSL para APIs externas
ssl._create_default_https_context = ssl._create_unverified_context

# Tenta carregar o arquivo .env (caminho absoluto)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
=======
# Resolve problemas de certificado SSL para chamadas de API
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307

app = Flask(__name__)

class BancoDeDados:
    def __init__(self):
<<<<<<< HEAD
        self.conexao = None
        self.conectar()

    def conectar(self):
        try:
            # Dados inseridos manualmente para ignorar o .env problemático
            self.conexao = mysql.connector.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="1234",
                database="Banco_de_dados",
                use_pure=True,
                auth_plugin='mysql_native_password'
            )
            if self.conexao.is_connected():
                print("✅ AGORA SIM! Conectado com sucesso.")
                self.criar_tabelas()
        except Exception as e:
            print(f"❌ Erro Real: {e}")
            self.conexao = None

    def get_cursor(self):
        """Retorna um cursor novo ou tenta reconectar se a conexão caiu."""
        try:
            if self.conexao is None or not self.conexao.is_connected():
                self.conectar()
            
            if self.conexao and self.conexao.is_connected():
                # dictionary=True facilita o acesso no HTML: filme['nome_filme']
                return self.conexao.cursor(dictionary=True, buffered=True)
            return None
        except:
            return None

    def criar_tabelas(self):
        """Garante que a estrutura do Movecritic exista no banco."""
        cur = self.get_cursor()
        if not cur: return
        try:
            cur.execute('''
=======
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
            # Tabela de Obras (Filmes e Livros)
            self.cursor.execute('''
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307
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
<<<<<<< HEAD
            cur.execute('''
=======
            # Tabela de Críticas
            self.cursor.execute('''
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307
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
<<<<<<< HEAD
            print(f"❌ Erro ao criar tabelas: {e}")
        finally:
            if cur: cur.close()

    def salvar_obra(self, nome, categoria, genero, nota, imagem, sinopse):
        """Salva obra e retorna o ID."""
        cur = self.get_cursor()
        if not cur: return None
        try:
            cur.execute("SELECT id_filme FROM filmes WHERE nome_filme = %s AND categoria = %s", (nome, categoria))
            res = cur.fetchone()
            if res: 
                return res['id_filme']
            
            sql = "INSERT INTO filmes (nome_filme, categoria, genero, imdb, imagem, sinopse) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (nome, categoria, genero, nota, imagem, sinopse))
            self.conexao.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"❌ Erro ao salvar {categoria}: {e}")
            return None
        finally:
            if cur: cur.close()

# Instância global
=======
            print(f"❌ Erro Tabelas: {e}")

    def salvar_obra(self, nome, categoria, genero, nota, imagem, sinopse):
        try:
            # Evita duplicados verificando nome e categoria
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

>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307
bd = BancoDeDados()

# --- ROTAS ---

@app.route("/")
def home():
<<<<<<< HEAD
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
=======
    try:
        bd.cursor.execute("SELECT * FROM filmes ORDER BY id_filme DESC LIMIT 8")
        recomendacoes = bd.cursor.fetchall()
        return render_template('index.html', filmes=recomendacoes, lista_resultados=[], busca=None)
    except Exception as e:
        print(f"Erro Home: {e}")
        return render_template('index.html', filmes=[], lista_resultados=[], busca=None)
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307

@app.route('/search')
def pesquisar():
    query = request.args.get('q', '')
    resultados_finais = []
    api_key_tmdb = os.getenv("TMDB_API_KEY")

    if query:
<<<<<<< HEAD
        # 1. Filmes (TMDB)
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
                        sinopse = item.get('overview') or 'Sem sinopse.'
                        id_db = bd.salvar_obra(titulo, "filme", "Geral", nota, img, sinopse)
                        if id_db:
                            resultados_finais.append({"id": id_db, "titulo": titulo, "nota": nota, "img": img, "sinopse": sinopse, "tipo": "filme"})
            except: pass

        # 2. Livros (OpenLibrary)
        try:
            res_ol = requests.get("https://openlibrary.org/search.json", params={"q": query, "limit": 5}, timeout=10)
            if res_ol.status_code == 200:
                for item in res_ol.json().get('docs', []):
                    titulo = item.get('title')
                    cover = item.get('cover_i')
                    img = f"https://covers.openlibrary.org/b/id/{cover}-L.jpg" if cover else ""
                    autores = ", ".join(item.get('author_name', ['N/A']))
                    id_db = bd.salvar_obra(titulo, "livro", "Geral", "Livro", img, f"Autor(es): {autores}")
                    if id_db:
                        resultados_finais.append({"id": id_db, "titulo": titulo, "nota": "Livro", "img": img, "sinopse": f"Autores: {autores}", "tipo": "livro"})
        except: pass
=======
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

        # 2. BUSCA LIVROS (OPEN LIBRARY API)
        try:
            print(f"--- Iniciando busca na Open Library para: {query} ---")
            url_ol = "https://openlibrary.org/search.json"
            res_ol = requests.get(url_ol, params={"q": query, "limit": 10}, timeout=10)
            
            if res_ol.status_code == 200:
                dados_ol = res_ol.json().get('docs', [])
                for item in dados_ol:
                    titulo = item.get('title', 'Título Desconhecido')
                    
                    # Tratamento de Capa
                    cover_id = item.get('cover_i')
                    img = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else "https://via.placeholder.com/150x220?text=Sem+Capa"
                    
                    # Montagem da Sinopse/Resumo (Autores + Ano)
                    autores = ", ".join(item.get('author_name', ['Autor desconhecido']))
                    ano = item.get('first_publish_year', 'N/A')
                    resumo = f"Escrito por: {autores}. Publicado originalmente em: {ano}."
                    
                    id_db_livro = bd.salvar_obra(titulo, "livro", "Geral", "Livro", img, resumo)
                    if id_db_livro:
                        resultados_finais.append({
                            "id": id_db_livro, 
                            "titulo": titulo, 
                            "nota": "Livro", 
                            "img": img, 
                            "sinopse": resumo, 
                            "tipo": "livro"
                        })
                print(f"✅ Open Library retornou {len(dados_ol)} livros.")
            else:
                print(f"❌ Erro Open Library: {res_ol.status_code}")
        except Exception as e:
            print(f"❌ Erro Crítico Open Library: {e}")
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307

    return render_template('index.html', busca=query, lista_resultados=resultados_finais, filmes=[])

@app.route('/criticas/<int:filme_id>')
def ver_criticas(filme_id):
<<<<<<< HEAD
    cur = bd.get_cursor()
    if not cur: return "Erro de banco", 500
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
    return redirect(f'/criticas/{id_f}')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
=======
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
>>>>>>> cebc956a49e87c34f9344dde5eaa5c5374006307
