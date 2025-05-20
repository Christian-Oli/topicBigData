import customtkinter as ctk
import tkinter as tk
import requests
import pandas as pd
from PIL import Image, ImageTk
from io import BytesIO
import os

# Configurações da API e do CSV
TMDB_API_KEY = "5968e0e2ae961359489ef818f486a395" # Sua chave da API TMDB
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200" # Imagem menor para o menu
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500" # Imagem maior para detalhes

CSV_FILE_PATH = os.path.join("dataset", "Dataset_ADD.csv")
CSV_TMDB_ID_COLUMN = "id"

CSV_COLUMN_LABELS = {
    "id": "ID TMDB (do CSV)",
    "Indi_oscar": "Indicador Oscar",
    "outros_premios": "Outros Prêmios Ganhos",
    "quant_premios": "Quantidade de Prêmios",
    "quant_indicacoes": "Quantidade de Indicações",
    "distribui_interncional": "Distribuição Internacional",
    "marketing_inter": "Marketing Internacional (USD)",
    "orca_marketing": "Orçamento de Marketing (USD)",
    "critica_nacional": "Crítica Nacional",
    "critica_internacional": "Crítica Internacional",
    "analises_roteiro": "Análise de Roteiro",
    "analises_direcao": "Análise de Direção",
    "analise_fotografia": "Análise de Fotografia",
    "diff_culturais": "Diferenças Culturais",
    "presente_streaming": "Presente em Streaming",
    "explicacao_nao_oscar": "Explicação (Não Ganhou Oscar)"
}

class BeeViewApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BeeView")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Frame do cabeçalho (sempre visível)
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, height=100)
        self.header_frame.pack(fill="x", pady=(0,0), side="top") # Adicionado pady=(0,0) e side="top"

        self.title_label = ctk.CTkLabel(self.header_frame, text="BeeView", font=ctk.CTkFont(size=30, weight="bold"))
        self.title_label.pack(pady=(10, 0))

        self.subtitle_label = ctk.CTkLabel(self.header_frame, text="Sua central de análise de filmes", font=ctk.CTkFont(size=16))
        self.subtitle_label.pack(pady=(0, 10))

        # Container principal que trocará os frames de visualização
        self.view_container = ctk.CTkFrame(self, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True, padx=0, pady=0) # Removido padx e pady

        # --- Frame para a grade de filmes ---
        self.movie_grid_view_frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
        # self.movie_grid_view_frame.pack(fill="both", expand=True) # Não empacotar inicialmente

        self.movie_menu_label = ctk.CTkLabel(self.movie_grid_view_frame, text="Filmes do seu Dataset", font=ctk.CTkFont(size=20, weight="bold"))
        self.movie_menu_label.pack(pady=10, padx=20)

        self.movie_menu_scrollable_frame = ctk.CTkScrollableFrame(self.movie_grid_view_frame, border_width=2, border_color="yellow", fg_color="#2B2B2B")
        self.movie_menu_scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0,10))

        # --- Frame para os detalhes do filme ---
        self.movie_details_view_frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
        # self.movie_details_view_frame.pack(fill="both", expand=True) # Não empacotar inicialmente
        # Este frame será preenchido dinamicamente

        self.movies_data_display = []
        self.df_csv = self.load_csv_data()

        self.load_and_filter_movies_for_grid() # Carrega filmes para a grade
        self.show_movie_grid_view() # Exibe a grade de filmes inicialmente

    def clear_frame(self, frame):
        """Remove todos os widgets de um frame."""
        for widget in frame.winfo_children():
            widget.destroy()

    def show_movie_grid_view(self):
        """Exibe a visualização da grade de filmes."""
        self.subtitle_label.configure(text="Sua central de análise de filmes (Conectados ao CSV)")
        self.movie_details_view_frame.pack_forget()
        self.clear_frame(self.movie_details_view_frame) # Limpa detalhes anteriores
        self.movie_grid_view_frame.pack(fill="both", expand=True)
        # Recarrega os filmes na grade caso haja alguma atualização,
        # ou apenas garante que está visível.
        if not self.movie_menu_scrollable_frame.winfo_children():
             self.display_filtered_movies_in_grid()


    def show_movie_details_view(self, movie_data_tmdb):
        """Exibe a visualização de detalhes do filme."""
        self.movie_grid_view_frame.pack_forget()
        self.clear_frame(self.movie_details_view_frame) # Limpa detalhes anteriores

        movie_title = movie_data_tmdb.get('title', 'Detalhes do Filme')
        self.subtitle_label.configure(text=f"Detalhes: {movie_title}")

        # Botão Voltar
        back_button = ctk.CTkButton(self.movie_details_view_frame, text="⬅ Voltar para a Lista",
                                    command=self.show_movie_grid_view,
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    fg_color="#4A4A4A", hover_color="#5A5A5A")
        back_button.pack(pady=10, padx=20, anchor="nw")

        # Scrollable Frame para o conteúdo dos detalhes
        details_scroll_frame = ctk.CTkScrollableFrame(self.movie_details_view_frame, fg_color="transparent")
        details_scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Seção de Informações do TMDB ---
        tmdb_main_frame = ctk.CTkFrame(details_scroll_frame, corner_radius=10, fg_color="#2B2B2B")
        tmdb_main_frame.pack(fill="x", pady=(0, 20))

        # Frame para poster e infos lado a lado
        tmdb_content_frame = ctk.CTkFrame(tmdb_main_frame, fg_color="transparent")
        tmdb_content_frame.pack(fill="x", expand=True, padx=15, pady=15)
        tmdb_content_frame.grid_columnconfigure(1, weight=1) # Coluna do texto expande

        poster_label = ctk.CTkLabel(tmdb_content_frame, text="Carregando poster...", width=200, height=300, fg_color="#333333", corner_radius=8)
        poster_label.grid(row=0, column=0, rowspan=5, padx=(0, 15), pady=5, sticky="nw")
        if movie_data_tmdb.get('poster_path'):
            self.load_image_async(TMDB_POSTER_BASE_URL + movie_data_tmdb['poster_path'], poster_label, (200, 300))
        else:
            poster_label.configure(text="Poster não\ndisponível")

        ctk.CTkLabel(tmdb_content_frame, text=f"{movie_data_tmdb.get('title', 'N/A')}", font=ctk.CTkFont(size=20, weight="bold"), wraplength=450, justify="left").grid(row=0, column=1, sticky="nw", pady=(0,5))
        ctk.CTkLabel(tmdb_content_frame, text=f"Título Original: {movie_data_tmdb.get('original_title', 'N/A')}", font=ctk.CTkFont(size=13), wraplength=450, justify="left").grid(row=1, column=1, sticky="nw")
        ctk.CTkLabel(tmdb_content_frame, text=f"Lançamento: {movie_data_tmdb.get('release_date', 'N/A')}", font=ctk.CTkFont(size=13), wraplength=450, justify="left").grid(row=2, column=1, sticky="nw")
        ctk.CTkLabel(tmdb_content_frame, text=f"Avaliação TMDB: {movie_data_tmdb.get('vote_average', 0):.1f}/10 ({movie_data_tmdb.get('vote_count', 0)} votos)", font=ctk.CTkFont(size=13), wraplength=450, justify="left").grid(row=3, column=1, sticky="nw", pady=(0,10))

        overview_title = ctk.CTkLabel(tmdb_content_frame, text="Visão Geral:", font=ctk.CTkFont(size=14, weight="bold"))
        overview_title.grid(row=4, column=1, sticky="sw", pady=(5,0)) # Movido para baixo do poster

        overview_text_widget = ctk.CTkTextbox(tmdb_main_frame, height=100, activate_scrollbars=True, wrap="word", font=ctk.CTkFont(size=12), border_spacing=5, fg_color="#333333")
        overview_text_widget.pack(fill="x", expand=True, padx=15, pady=(0,15))
        overview_text_widget.insert("1.0", movie_data_tmdb.get('overview', 'Não disponível.'))
        overview_text_widget.configure(state="disabled")

        # --- Seção de Informações do CSV ---
        ctk.CTkLabel(details_scroll_frame, text="Análise Adicional (Dataset Local)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10,5), anchor="w")

        csv_data_container = ctk.CTkFrame(details_scroll_frame, fg_color="transparent")
        csv_data_container.pack(fill="both", expand=True)

        movie_csv_data = self.get_movie_csv_data(movie_data_tmdb.get('id'))
        
        if movie_csv_data is not None and not movie_csv_data.empty:
            col_count = 0
            max_cols_csv = 3 # Quantas "células" de informação por linha

            for idx, (col_name_csv, label_text_display) in enumerate(CSV_COLUMN_LABELS.items()):
                if col_name_csv == CSV_TMDB_ID_COLUMN and label_text_display == "ID TMDB (do CSV)": # Não mostrar o ID TMDB novamente aqui
                    continue
                if col_name_csv in movie_csv_data and pd.notna(movie_csv_data[col_name_csv]):
                    value = movie_csv_data[col_name_csv]
                    try:
                        if isinstance(value, (float, int)) and float(value).is_integer():
                            value = int(value)
                        elif isinstance(value, str):
                            if value.replace('.', '', 1).isdigit():
                                val_float = float(value)
                                if val_float.is_integer(): value = int(val_float)
                            elif value.lower() == 'true': value = "Sim"
                            elif value.lower() == 'false': value = "Não"
                    except ValueError:
                        pass

                    # Estilo "Colmeia" - Frame individual para cada dado
                    cell_frame = ctk.CTkFrame(csv_data_container, corner_radius=10, border_width=1, border_color="#FFD700", fg_color="#303030") # Dourado para abelha :)
                    
                    # Usando grid para organizar as células
                    row_csv = idx // max_cols_csv
                    col_csv = idx % max_cols_csv
                    cell_frame.grid(row=row_csv, column=col_csv, padx=5, pady=5, sticky="nsew")
                    csv_data_container.grid_columnconfigure(col_csv, weight=1) # Faz colunas expandirem igualmente

                    ctk.CTkLabel(cell_frame, text=label_text_display, font=ctk.CTkFont(size=11, weight="bold"), wraplength=180).pack(anchor="n", padx=10, pady=(10,2))
                    
                    # Usar CTkTextbox para valores que podem ser longos, senão CTkLabel
                    if isinstance(value, str) and len(value) > 100: # Heurística para texto longo
                        value_widget = ctk.CTkTextbox(cell_frame, font=ctk.CTkFont(size=12), height=60, activate_scrollbars=True, wrap="word", fg_color="#3A3A3A", border_width=0)
                        value_widget.insert("1.0", str(value))
                        value_widget.configure(state="disabled")
                    else:
                        value_widget = ctk.CTkLabel(cell_frame, text=str(value), font=ctk.CTkFont(size=13), wraplength=180)
                    
                    value_widget.pack(anchor="n", padx=10, pady=(0,10), fill="x")
                    col_count +=1
        else:
            ctk.CTkLabel(csv_data_container, text=f"Dados adicionais do CSV não encontrados para o filme com ID TMDB: {movie_data_tmdb.get('id')}.", font=ctk.CTkFont(size=14)).pack(padx=10, pady=10)

        self.movie_details_view_frame.pack(fill="both", expand=True) # Exibe o frame de detalhes

    def load_csv_data(self):
        try:
            df = pd.read_csv(CSV_FILE_PATH, delimiter=';')
            print(f"CSV '{CSV_FILE_PATH}' carregado com sucesso.")
            if CSV_TMDB_ID_COLUMN in df.columns:
                df.dropna(subset=[CSV_TMDB_ID_COLUMN], inplace=True)
                try:
                    df[CSV_TMDB_ID_COLUMN] = df[CSV_TMDB_ID_COLUMN].astype(float).astype(int).astype(str)
                except ValueError:
                    df[CSV_TMDB_ID_COLUMN] = df[CSV_TMDB_ID_COLUMN].astype(str)
                print(f"Coluna de conexão '{CSV_TMDB_ID_COLUMN}' encontrada e processada como string.")
            else:
                print(f"AVISO: A coluna de conexão '{CSV_TMDB_ID_COLUMN}' NÃO foi encontrada no CSV.")
                return pd.DataFrame()
            return df
        except FileNotFoundError:
            print(f"Erro: Arquivo CSV não encontrado em '{CSV_FILE_PATH}'.")
            # Exibir mensagem na UI
            self.display_error_in_grid(f"Erro: Arquivo CSV não encontrado em\n'{CSV_FILE_PATH}'.\nVerifique o caminho e o nome do arquivo.")
            return pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar ou processar o CSV: {e}")
            self.display_error_in_grid(f"Erro ao carregar ou processar o CSV:\n{e}")
            return pd.DataFrame()

    def fetch_tmdb_api(self, endpoint, params=None):
        if params is None:
            params = {}
        params['api_key'] = TMDB_API_KEY
        params['language'] = 'pt-BR'
        try:
            response = requests.get(f"{TMDB_BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados da API TMDB para endpoint '{endpoint}': {e}")
            return None

    def display_error_in_grid(self, message):
        """Exibe uma mensagem de erro na área da grade de filmes."""
        self.clear_frame(self.movie_menu_scrollable_frame)
        error_label = ctk.CTkLabel(self.movie_menu_scrollable_frame, text=message,
                                   font=ctk.CTkFont(size=16),
                                   wraplength=self.movie_menu_scrollable_frame.winfo_width() - 40 if self.movie_menu_scrollable_frame.winfo_width() > 40 else 300,
                                   justify="center")
        error_label.pack(pady=20, padx=10, expand=True, fill="both")


    def load_and_filter_movies_for_grid(self):
        self.clear_frame(self.movie_menu_scrollable_frame) # Limpa a grade antes de carregar

        if self.df_csv.empty or CSV_TMDB_ID_COLUMN not in self.df_csv.columns:
            msg = "Arquivo CSV não carregado ou coluna de ID ausente.\nImpossível listar filmes."
            if CSV_TMDB_ID_COLUMN not in self.df_csv.columns and not self.df_csv.empty:
                 msg = f"Coluna '{CSV_TMDB_ID_COLUMN}' (para IDs do TMDB) não encontrada no CSV.\nVerifique o nome da coluna no arquivo."
            elif self.df_csv.empty and os.path.exists(CSV_FILE_PATH): # CSV existe mas está vazio ou erro na leitura
                 msg = f"CSV '{CSV_FILE_PATH}' está vazio ou ocorreu um erro ao lê-lo."
            # Não precisa de verificação de not os.path.exists aqui, pois load_csv_data já trata
            self.display_error_in_grid(msg)
            return

        self.movies_data_display = []
        csv_tmdb_ids = self.df_csv[CSV_TMDB_ID_COLUMN].astype(str).unique().tolist()

        if not csv_tmdb_ids:
            self.display_error_in_grid(f"Nenhum ID de filme encontrado na coluna '{CSV_TMDB_ID_COLUMN}' do arquivo CSV.")
            return

        print(f"Encontrados {len(csv_tmdb_ids)} IDs únicos no CSV para buscar na TMDB.")
        movies_fetched_count = 0
        for tmdb_id_str in csv_tmdb_ids:
            if not tmdb_id_str.strip() or tmdb_id_str.lower() == 'nan':
                print(f"Aviso: ID inválido ou vazio ('{tmdb_id_str}') encontrado no CSV, pulando.")
                continue

            print(f"Buscando filme com ID TMDB: {tmdb_id_str}...")
            movie_details_tmdb = self.fetch_tmdb_api(f"movie/{tmdb_id_str.strip()}")

            if movie_details_tmdb and movie_details_tmdb.get('id'):
                self.movies_data_display.append(movie_details_tmdb)
                movies_fetched_count +=1
                print(f"Filme '{movie_details_tmdb.get('title')}' (ID: {tmdb_id_str}) adicionado.")
            else:
                print(f"Não foram encontrados detalhes válidos na TMDB para o ID '{tmdb_id_str}' do CSV ou a API falhou.")
        
        print(f"Total de {movies_fetched_count} filmes do CSV encontrados e carregados da TMDB.")

        if not self.movies_data_display:
            self.display_error_in_grid("Nenhum filme do seu CSV pôde ser encontrado ou carregado com dados da TMDB.\nVerifique os IDs no CSV, sua conexão com a internet e a chave da API.")
        else:
            self.display_filtered_movies_in_grid()

    def display_filtered_movies_in_grid(self):
        self.clear_frame(self.movie_menu_scrollable_frame) # Limpa a grade
        row, col = 0, 0
        max_cols = 4

        if not self.movies_data_display: # Checagem extra
            self.display_error_in_grid("Nenhum filme para exibir.")
            return

        for movie in self.movies_data_display:
            title = movie.get('title', 'Título Desconhecido')
            poster_path = movie.get('poster_path')

            item_frame = ctk.CTkFrame(self.movie_menu_scrollable_frame, fg_color="#333333", corner_radius=8)
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.movie_menu_scrollable_frame.grid_columnconfigure(col, weight=1) # Para que as colunas se ajustem

            img_label = ctk.CTkLabel(item_frame, text="Carregando...", height=150, width=100, fg_color="#2B2B2B", corner_radius=6)
            img_label.pack(pady=(10,5), padx=10)

            if poster_path:
                self.load_image_async(TMDB_IMAGE_BASE_URL + poster_path, img_label, (100, 150))
            else:
                img_label.configure(text="Sem Poster")

            title_text = title if len(title) < 25 else title[:22] + "..."
            title_label = ctk.CTkLabel(item_frame, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), wraplength=120)
            title_label.pack(pady=(0,5), padx=10, fill="x")

            details_button = ctk.CTkButton(item_frame, text="Ver Detalhes",
                                           command=lambda m=movie: self.show_movie_details_view(m),
                                           font=ctk.CTkFont(size=12))
            details_button.pack(pady=(0,10), padx=10, fill="x")

            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configurar peso das linhas também, se necessário, para preenchimento vertical
        if row > 0 : # Se houver pelo menos uma linha completa
             for r in range(row +1): # +1 para incluir a linha atual em progresso
                  self.movie_menu_scrollable_frame.grid_rowconfigure(r, weight=1)


    def load_image_async(self, url, label_widget, size):
        try:
            response = requests.get(url, stream=True, timeout=10) # Adicionado timeout
            response.raise_for_status()
            img_data = BytesIO(response.content)

            img = Image.open(img_data)
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS

            img = img.resize(size, resample_filter)
            photo = ImageTk.PhotoImage(img)

            label_widget.configure(image=photo, text="")
            label_widget.image = photo
        except requests.exceptions.Timeout:
            print(f"Timeout ao carregar imagem de {url}")
            label_widget.configure(text="Timeout Img", image=None)
        except Exception as e:
            print(f"Erro ao carregar imagem de {url}: {e}")
            label_widget.configure(text="Erro Img", image=None) # Texto mais curto

    def get_movie_csv_data(self, movie_tmdb_id_to_find):
        if self.df_csv.empty or CSV_TMDB_ID_COLUMN not in self.df_csv.columns:
            return None
        movie_data_csv = self.df_csv[self.df_csv[CSV_TMDB_ID_COLUMN] == str(movie_tmdb_id_to_find)]
        if not movie_data_csv.empty:
            return movie_data_csv.iloc[0]
        print(f"Alerta: Nenhum dado encontrado no CSV para TMDB ID '{movie_tmdb_id_to_find}' (coluna '{CSV_TMDB_ID_COLUMN}').")
        return None

if __name__ == "__main__":
    app = BeeViewApp()
    app.mainloop()