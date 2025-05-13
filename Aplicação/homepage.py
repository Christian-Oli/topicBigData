import tkinter as tk
from tkinter import ttk
import requests

# Coloque sua chave da API TMDB aqui
API_KEY = 'SUA_API_KEY_TMDB'
BASE_URL = 'https://api.themoviedb.org/3'

# Função para buscar filmes
def buscar_filmes():
    query = entrada_busca.get()
    if not query.strip():
        return

    resposta = requests.get(
        f'{BASE_URL}/search/movie',
        params={'api_key': API_KEY, 'query': query, 'language': 'pt-BR'}
    )

    if resposta.status_code == 200:
        dados = resposta.json()
        exibir_resultados(dados['results'])
    else:
        print("Erro ao buscar filmes")

# Função para exibir a lista de filmes pesquisados
def exibir_resultados(filmes):
    for widget in frame_resultados.winfo_children():
        widget.destroy()

    for filme in filmes:
        botao = tk.Button(frame_resultados, text=filme['title'], anchor='w', width=70,
                          command=lambda f=filme: mostrar_detalhes(f))
        botao.pack(fill='x', padx=5, pady=2)

# Função para mostrar detalhes do filme selecionado
def mostrar_detalhes(filme):
    janela_detalhes = tk.Toplevel(root)
    janela_detalhes.title(filme['title'])
    janela_detalhes.geometry('500x400')

    titulo = filme.get('title', 'Sem título')
    descricao = filme.get('overview', 'Sem descrição disponível.')
    data_lancamento = filme.get('release_date', 'Data desconhecida')
    nota = filme.get('vote_average', 'N/A')

    tk.Label(janela_detalhes, text=titulo, font=('Arial', 16, 'bold')).pack(pady=10)
    tk.Label(janela_detalhes, text=f"Lançamento: {data_lancamento}").pack(pady=2)
    tk.Label(janela_detalhes, text=f"Nota: {nota} / 10").pack(pady=2)
    tk.Label(janela_detalhes, text="Descrição:", font=('Arial', 12, 'underline')).pack(pady=5)
    
    text_descricao = tk.Text(janela_detalhes, wrap='word', height=10, width=60)
    text_descricao.insert('1.0', descricao)
    text_descricao.config(state='disabled')
    text_descricao.pack(pady=5)

# Interface principal
root = tk.Tk()
root.title("Pesquisa de Filmes")
root.geometry("800x600")

# Entrada e botão de busca
frame_superior = tk.Frame(root)
frame_superior.pack(pady=10)

entrada_busca = ttk.Entry(frame_superior, width=50)
entrada_busca.pack(side='left', padx=10)

botao_buscar = ttk.Button(frame_superior, text="Buscar", command=buscar_filmes)
botao_buscar.pack(side='left')

# Frame para resultados
frame_resultados = tk.Frame(root)
frame_resultados.pack(fill='both', expand=True, padx=20, pady=10)

root.mainloop()
