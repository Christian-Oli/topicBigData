import customtkinter
import requests
from PIL import Image, ImageTk
import io
import threading
import tkinter as tk
from typing import List, Dict, Any, Optional, Tuple

# --- Constantes ---
API_KEY = "5968e0e2ae961359489ef818f486a395"  # Sua Chave da API TMDb
BASE_URL_TMDB = "https://api.themoviedb.org/3"
BASE_URL_IMG_TMDB = "https://image.tmdb.org/t/p/"

# --- Novas Cores ---
COR_PRIMARIA = "#ffcf00"       # Amarelo Principal (era Verde)
COR_SECUNDARIA = "#febf00"     # Amarelo Secundário (era Verde Escuro)
COR_TEXTO_CLARO = "#040500"    # Preto (para contraste com amarelo)
COR_TEXTO_ESCURO = "#FFFFFF"   # Branco (para contraste com fundo escuro)
COR_FUNDO = "#040500"          # Preto (era Cinza Claro)
COR_INPUT_FUNDO = "#1b1e0d"    # Verde Muito Escuro (era Branco)
COR_ERRO = "#FF009D"           # Rosa (era Avermelhado)
COR_PLACEHOLDER = "#febf00"    # Amarelo Secundário (era Cinza Claro)
COR_BORDA_CLARA = "#444444"    # Cinza Escuro (era Cinza Mais Claro)
COR_TEXTO_PLACEHOLDER_INPUT = "#cccccc" # Cinza claro para texto de placeholder no input

FAMILIA_FONTE = "Segoe UI"
TAMANHO_FONTE_NORMAL = 12
TAMANHO_FONTE_GRANDE = 18
TAMANHO_FONTE_TITULO_APP = 36
TAMANHO_FONTE_TITULO_FILME_DETALHE = 24
TAMANHO_FONTE_SUBTITULO_DETALHE = 16

LARGURA_POSTER_LISTA = 130
ALTURA_POSTER_LISTA = 195
LARGURA_POSTER_DETALHE = 220
ALTURA_POSTER_DETALHE = 330
COLUNAS_GRID_RESULTADOS = 4


class BeeViewApp(customtkinter.CTk):
    """
    Aplicativo BeeView para pesquisar filmes usando a API TMDb.
    Refatorado com navegação para detalhes do filme e novo esquema de cores.
    """

    def __init__(self) -> None:
        super().__init__()

        self.api_key: str = API_KEY
        self.cache_poster_lista: Dict[str, ImageTk.PhotoImage] = {}
        self.cache_poster_detalhe: Dict[str, ImageTk.PhotoImage] = {}

        self._configurar_janela_principal()
        self._configurar_estilos_fonte()

        # --- Gerenciamento de Views (Telas) ---
        # Container principal que ocupará a maior parte da janela após a barra de pesquisa (se visível)
        self.container_view_principal = customtkinter.CTkFrame(self, fg_color=COR_FUNDO)
        self.container_view_principal.grid(row=1, column=0, sticky="nsew")
        self.container_view_principal.grid_rowconfigure(0, weight=1)
        self.container_view_principal.grid_columnconfigure(0, weight=1)

        self._criar_barra_pesquisa_superior() # Barra de pesquisa fica no topo (row=0 da janela principal)
        self._criar_view_boas_vindas()
        self._criar_view_resultados()
        self._criar_view_detalhes_filme()

        self._mostrar_view_boas_vindas() # Começa com a tela de boas-vindas

    def _configurar_janela_principal(self) -> None:
        """Configura as propriedades da janela principal."""
        self.title("BeeView - Universo Cinematográfico")
        self.geometry("950x750")
        self.minsize(800, 600)
        self.configure(fg_color=COR_FUNDO)

        # Configuração do grid da janela principal
        self.grid_rowconfigure(0, weight=0)  # Para a barra de pesquisa (se visível no topo)
        self.grid_rowconfigure(1, weight=1)  # Para o container da view principal
        self.grid_columnconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self._ao_fechar_janela)

    def _configurar_estilos_fonte(self) -> None:
        """Define os estilos de fonte usados no aplicativo."""
        self.fonte_normal = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_NORMAL)
        self.fonte_negrito = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_NORMAL, weight="bold")
        self.fonte_grande = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_GRANDE)
        self.fonte_titulo_app = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_TITULO_APP, weight="bold")
        self.fonte_titulo_filme_detalhe = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_TITULO_FILME_DETALHE, weight="bold")
        self.fonte_subtitulo_detalhe = customtkinter.CTkFont(family=FAMILIA_FONTE, size=TAMANHO_FONTE_SUBTITULO_DETALHE, weight="bold")

    # --- Criação das Views (Telas) ---

    def _criar_barra_pesquisa_superior(self) -> None:
        """Cria a barra de pesquisa que fica no topo da janela."""
        self.frame_barra_pesquisa_superior = customtkinter.CTkFrame(self, fg_color="transparent", height=60)
        # Este frame será gerenciado por grid_remove/grid ao trocar de view principal

        self.entrada_pesquisa = customtkinter.CTkEntry(
            self.frame_barra_pesquisa_superior,
            placeholder_text="Pesquisar por filmes...",
            font=self.fonte_normal,
            text_color=COR_TEXTO_ESCURO, # Texto digitado
            placeholder_text_color=COR_TEXTO_PLACEHOLDER_INPUT,
            fg_color=COR_INPUT_FUNDO,
            border_color=COR_PRIMARIA,
            height=38,
            corner_radius=8
        )
        self.entrada_pesquisa.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 5), pady=10)
        self.entrada_pesquisa.bind("<Return>", lambda event: self._iniciar_pesquisa_filmes())

        self.botao_pesquisar = customtkinter.CTkButton(
            self.frame_barra_pesquisa_superior,
            text="Pesquisar",
            command=self._iniciar_pesquisa_filmes,
            font=self.fonte_negrito,
            text_color=COR_TEXTO_CLARO, # Texto do botão
            fg_color=COR_PRIMARIA,
            hover_color=COR_SECUNDARIA,
            height=38,
            width=120,
            corner_radius=8
        )
        self.botao_pesquisar.pack(side=tk.RIGHT, padx=(0, 20), pady=10)

    def _criar_view_boas_vindas(self) -> None:
        """Cria os widgets para a tela de boas-vindas."""
        self.view_boas_vindas = customtkinter.CTkFrame(self.container_view_principal, fg_color="transparent")
        self.view_boas_vindas.grid_columnconfigure(0, weight=1)
        # Centralizar verticalmente o conteúdo da boas-vindas
        self.view_boas_vindas.grid_rowconfigure(0, weight=1) # Espaço acima
        self.view_boas_vindas.grid_rowconfigure(1, weight=0) # Título
        self.view_boas_vindas.grid_rowconfigure(2, weight=0) # Tagline
        self.view_boas_vindas.grid_rowconfigure(3, weight=0) # Barra de pesquisa específica da boas-vindas
        self.view_boas_vindas.grid_rowconfigure(4, weight=1) # Espaço abaixo


        label_titulo_app = customtkinter.CTkLabel(
            self.view_boas_vindas,
            text="BeeView",
            font=self.fonte_titulo_app,
            text_color=COR_PRIMARIA
        )
        label_titulo_app.grid(row=1, column=0, pady=(0, 10))

        label_tagline = customtkinter.CTkLabel(
            self.view_boas_vindas,
            text="Seu portal para o universo cinematográfico!",
            font=self.fonte_grande,
            text_color=COR_TEXTO_ESCURO
        )
        label_tagline.grid(row=2, column=0, pady=(0, 40))

        # Barra de pesquisa para a tela de boas-vindas (pode ser diferente da superior)
        frame_pesquisa_boas_vindas = customtkinter.CTkFrame(self.view_boas_vindas, fg_color="transparent")
        frame_pesquisa_boas_vindas.grid(row=3, column=0, pady=20, padx=50, sticky="ew")
        frame_pesquisa_boas_vindas.grid_columnconfigure(0, weight=1)

        self.entrada_pesquisa_boas_vindas = customtkinter.CTkEntry(
            frame_pesquisa_boas_vindas,
            placeholder_text="Digite o nome de um filme...",
            font=self.fonte_normal,
            text_color=COR_TEXTO_ESCURO,
            placeholder_text_color=COR_TEXTO_PLACEHOLDER_INPUT,
            fg_color=COR_INPUT_FUNDO,
            border_color=COR_PRIMARIA,
            height=40,
            corner_radius=8
        )
        self.entrada_pesquisa_boas_vindas.grid(row=0, column=0, padx=(0,10), sticky="ew")
        self.entrada_pesquisa_boas_vindas.bind("<Return>", lambda event: self._iniciar_pesquisa_filmes(origem="boas_vindas"))

        self.botao_pesquisar_boas_vindas = customtkinter.CTkButton(
            frame_pesquisa_boas_vindas,
            text="Buscar Filmes",
            command=lambda: self._iniciar_pesquisa_filmes(origem="boas_vindas"),
            font=self.fonte_negrito,
            text_color=COR_TEXTO_CLARO,
            fg_color=COR_PRIMARIA,
            hover_color=COR_SECUNDARIA,
            height=40,
            corner_radius=8
        )
        self.botao_pesquisar_boas_vindas.grid(row=0, column=1)


    def _criar_view_resultados(self) -> None:
        """Cria os widgets para a tela de resultados da pesquisa."""
        self.view_resultados = customtkinter.CTkFrame(self.container_view_principal, fg_color="transparent")
        self.view_resultados.grid_rowconfigure(0, weight=1)
        self.view_resultados.grid_columnconfigure(0, weight=1)

        self.canvas_resultados = customtkinter.CTkCanvas(
            self.view_resultados,
            highlightthickness=0,
            background=COR_FUNDO # Cor de fundo do canvas
        )
        self.canvas_resultados.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=10) # Adiciona um pouco de padding

        self.scrollbar_resultados = customtkinter.CTkScrollbar(
            self.view_resultados,
            command=self.canvas_resultados.yview,
            fg_color=COR_FUNDO, # Cor da scrollbar
            button_color=COR_PRIMARIA,
            button_hover_color=COR_SECUNDARIA,
            corner_radius=8
        )
        self.scrollbar_resultados.grid(row=0, column=1, sticky="ns", pady=10, padx=(0,10))
        self.canvas_resultados.configure(yscrollcommand=self.scrollbar_resultados.set)

        # Frame interno do canvas que conterá os cards dos filmes
        self.frame_interno_resultados = customtkinter.CTkFrame(self.canvas_resultados, fg_color=COR_FUNDO) # Cor de fundo do frame interno
        self.id_janela_canvas_resultados = self.canvas_resultados.create_window(
            (0, 0), window=self.frame_interno_resultados, anchor="nw"
        )

        # Configura colunas para o grid de cards de filmes
        for i in range(COLUNAS_GRID_RESULTADOS):
            self.frame_interno_resultados.grid_columnconfigure(i, weight=1, minsize=LARGURA_POSTER_LISTA + 20)

        # Bind para atualizar a scrollregion e largura do frame interno
        self.frame_interno_resultados.bind("<Configure>", self._atualizar_scrollregion_resultados)
        self.canvas_resultados.bind("<Configure>", self._configurar_largura_frame_interno_canvas)


    def _criar_view_detalhes_filme(self) -> None:
        """Cria os widgets para a tela de detalhes de um filme."""
        self.view_detalhes_filme = customtkinter.CTkScrollableFrame(self.container_view_principal, fg_color=COR_FUNDO, scrollbar_button_color=COR_PRIMARIA, scrollbar_fg_color=COR_FUNDO)
        # Usar CTkScrollableFrame simplifica o scroll para esta view.

        # Botão Voltar
        frame_botoes_detalhe = customtkinter.CTkFrame(self.view_detalhes_filme, fg_color="transparent")
        frame_botoes_detalhe.pack(fill="x", padx=20, pady=(20,10))

        botao_voltar_resultados = customtkinter.CTkButton(
            frame_botoes_detalhe,
            text="‹ Voltar aos Resultados",
            command=self._mostrar_view_resultados,
            font=self.fonte_negrito,
            text_color=COR_PRIMARIA,
            fg_color="transparent",
            hover_color=COR_INPUT_FUNDO, # Um leve destaque
            anchor="w"
        )
        botao_voltar_resultados.pack(side=tk.LEFT)

        botao_nova_pesquisa = customtkinter.CTkButton(
            frame_botoes_detalhe,
            text="Nova Pesquisa (Início)",
            command=self._mostrar_view_boas_vindas,
            font=self.fonte_negrito,
            text_color=COR_PRIMARIA,
            fg_color="transparent",
            hover_color=COR_INPUT_FUNDO,
            anchor="e"
        )
        botao_nova_pesquisa.pack(side=tk.RIGHT)


        # Container para Poster e Informações Lado a Lado
        container_poster_info = customtkinter.CTkFrame(self.view_detalhes_filme, fg_color="transparent")
        container_poster_info.pack(fill="both", expand=True, padx=30, pady=10)
        container_poster_info.grid_columnconfigure(0, weight=0) # Poster
        container_poster_info.grid_columnconfigure(1, weight=1) # Informações

        self.label_poster_detalhe = customtkinter.CTkLabel(
            container_poster_info, text="", width=LARGURA_POSTER_DETALHE, height=ALTURA_POSTER_DETALHE,
            fg_color=COR_INPUT_FUNDO, corner_radius=8
        )
        self.label_poster_detalhe.grid(row=0, column=0, rowspan=6, sticky="n", padx=(0, 25), pady=(10,0))

        self.label_titulo_filme_detalhe = customtkinter.CTkLabel(container_poster_info, text="Título do Filme", font=self.fonte_titulo_filme_detalhe, text_color=COR_TEXTO_ESCURO, wraplength=550, anchor="w", justify="left")
        self.label_titulo_filme_detalhe.grid(row=0, column=1, sticky="new", pady=(10,5))

        self.label_tagline_filme_detalhe = customtkinter.CTkLabel(container_poster_info, text="Tagline...", font=self.fonte_grande, text_color=COR_TEXTO_ESCURO, wraplength=550, anchor="w", justify="left")
        self.label_tagline_filme_detalhe.grid(row=1, column=1, sticky="new", pady=(0,15))

        self.label_sinopse_titulo_detalhe = customtkinter.CTkLabel(container_poster_info, text="Sinopse:", font=self.fonte_subtitulo_detalhe, text_color=COR_PRIMARIA, anchor="w")
        self.label_sinopse_titulo_detalhe.grid(row=2, column=1, sticky="new", pady=(10,2))
        self.label_sinopse_filme_detalhe = customtkinter.CTkLabel(container_poster_info, text="Carregando sinopse...", font=self.fonte_normal, text_color=COR_TEXTO_ESCURO, wraplength=550, anchor="w", justify="left")
        self.label_sinopse_filme_detalhe.grid(row=3, column=1, sticky="new", pady=(0,15))

        # Frame para informações adicionais (Data, Gêneros, etc.)
        frame_info_adicional_detalhe = customtkinter.CTkFrame(container_poster_info, fg_color="transparent")
        frame_info_adicional_detalhe.grid(row=4, column=1, sticky="new", pady=(10,0))

        self.label_data_lancamento_filme = customtkinter.CTkLabel(frame_info_adicional_detalhe, text="Data de Lançamento: ", font=self.fonte_normal, text_color=COR_TEXTO_ESCURO, anchor="w")
        self.label_data_lancamento_filme.pack(anchor="w", pady=1)
        self.label_generos_filme = customtkinter.CTkLabel(frame_info_adicional_detalhe, text="Gêneros: ", font=self.fonte_normal, text_color=COR_TEXTO_ESCURO, anchor="w")
        self.label_generos_filme.pack(anchor="w", pady=1)
        self.label_duracao_filme = customtkinter.CTkLabel(frame_info_adicional_detalhe, text="Duração: ", font=self.fonte_normal, text_color=COR_TEXTO_ESCURO, anchor="w")
        self.label_duracao_filme.pack(anchor="w", pady=1)
        self.label_avaliacao_filme = customtkinter.CTkLabel(frame_info_adicional_detalhe, text="Avaliação: ", font=self.fonte_normal, text_color=COR_TEXTO_ESCURO, anchor="w")
        self.label_avaliacao_filme.pack(anchor="w", pady=1)


    # --- Gerenciamento de Exibição das Views ---

    def _esconder_todas_views_principais(self) -> None:
        """Esconde todos os frames de view principal."""
        self.view_boas_vindas.grid_remove()
        self.view_resultados.grid_remove()
        self.view_detalhes_filme.grid_remove()
        self.frame_barra_pesquisa_superior.grid_remove() # Esconde a barra de pesquisa superior por padrão

    def _mostrar_view_boas_vindas(self) -> None:
        self._esconder_todas_views_principais()
        self.view_boas_vindas.grid(row=0, column=0, sticky="nsew")
        self.entrada_pesquisa_boas_vindas.delete(0, tk.END)
        self.entrada_pesquisa_boas_vindas.focus()
        self.title("BeeView - Bem-vindo!")

    def _mostrar_view_resultados(self) -> None:
        self._esconder_todas_views_principais()
        self.frame_barra_pesquisa_superior.grid(row=0, column=0, sticky="new", padx=0, pady=0) # Mostra barra de pesquisa no topo
        self.view_resultados.grid(row=0, column=0, sticky="nsew") # View de resultados ocupa o espaço no container
        self.entrada_pesquisa.focus()
        self.title("BeeView - Resultados da Pesquisa")

    def _mostrar_view_detalhes_filme(self, dados_filme_clicado: Dict[str, Any]) -> None:
        self._esconder_todas_views_principais()
        # A barra de pesquisa superior não é mostrada na tela de detalhes
        self.view_detalhes_filme.grid(row=0, column=0, sticky="nsew")
        self._limpar_widgets_detalhes_filme() # Limpa para placeholders
        self._exibir_placeholders_detalhes()

        filme_id = dados_filme_clicado.get('id')
        titulo_filme = dados_filme_clicado.get('title', 'Detalhes')
        self.title(f"BeeView - {titulo_filme}")

        if filme_id:
            # Inicia thread para buscar detalhes completos
            thread_detalhes = threading.Thread(
                target=self._buscar_e_preencher_detalhes_completos_filme,
                args=(filme_id,),
                daemon=True
            )
            thread_detalhes.start()
        else:
            self._preencher_detalhes_completos_filme({"erro": "ID do filme não encontrado."})


    # --- Lógica de Pesquisa e Exibição de Resultados ---

    def _iniciar_pesquisa_filmes(self, origem: str = "superior") -> None:
        """Inicia a busca de filmes com base na query da entrada de pesquisa."""
        if origem == "boas_vindas":
            query = self.entrada_pesquisa_boas_vindas.get().strip()
            self.entrada_pesquisa.delete(0, tk.END) # Limpa a outra barra
            self.entrada_pesquisa.insert(0, query) # Copia query para a barra superior
        else: # origem == "superior"
            query = self.entrada_pesquisa.get().strip()

        if not query:
            self._exibir_mensagem_temporaria("Por favor, digite um título de filme para pesquisar.", eh_erro=True)
            return

        self._mostrar_view_resultados()
        self._limpar_cards_resultados_anteriores()
        self._exibir_indicador_carregamento_resultados("Pesquisando filmes, por favor aguarde...")

        # Inicia a busca em uma nova thread para não bloquear a UI
        thread_busca = threading.Thread(target=self._thread_buscar_filmes, args=(query,), daemon=True)
        thread_busca.start()

    def _thread_buscar_filmes(self, query: str) -> None:
        """Thread para buscar filmes na API."""
        url = f"{BASE_URL_TMDB}/search/movie?api_key={self.api_key}&query={query}&language=pt-BR&page=1"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lança HTTPError para respostas ruins
            dados = response.json()
            filmes_encontrados: List[Dict[str, Any]] = dados.get('results', [])
            self.after(0, lambda: self._preencher_cards_resultados_filmes(filmes_encontrados))
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição da API de pesquisa: {e}")
            self.after(0, lambda: self._exibir_mensagem_nos_resultados(f"Erro ao buscar filmes: {e}", eh_erro=True))
        except ValueError:  # Inclui JSONDecodeError
            print("Erro ao decodificar JSON da pesquisa.")
            self.after(0, lambda: self._exibir_mensagem_nos_resultados("Erro ao processar resposta do servidor.", eh_erro=True))

    def _limpar_cards_resultados_anteriores(self) -> None:
        """Remove todos os widgets (cards de filmes) do frame interno de resultados."""
        for widget in self.frame_interno_resultados.winfo_children():
            widget.destroy()
        self.canvas_resultados.yview_moveto(0) # Reseta o scroll para o topo

    def _exibir_indicador_carregamento_resultados(self, mensagem: str) -> None:
        """Mostra uma mensagem de carregamento na área de resultados."""
        self.label_carregamento_resultados = customtkinter.CTkLabel(
            self.frame_interno_resultados,
            text=mensagem,
            font=self.fonte_grande,
            text_color=COR_TEXTO_ESCURO
        )
        # Centraliza o indicador de carregamento
        self.label_carregamento_resultados.grid(row=0, column=0, columnspan=COLUNAS_GRID_RESULTADOS, pady=50, sticky="ew")
        self.frame_interno_resultados.update_idletasks() # Garante que o widget seja desenhado
        self._atualizar_scrollregion_resultados()

    def _preencher_cards_resultados_filmes(self, filmes: List[Dict[str, Any]]) -> None:
        """Preenche a view de resultados com os cards dos filmes encontrados."""
        self._limpar_cards_resultados_anteriores() # Garante que o indicador de carregamento seja removido

        if not filmes:
            self._exibir_mensagem_nos_resultados("Nenhum filme encontrado com este termo de pesquisa.", eh_erro=False)
            return

        for i, dados_filme in enumerate(filmes):
            linha_grid = i // COLUNAS_GRID_RESULTADOS
            coluna_grid = i % COLUNAS_GRID_RESULTADOS
            self._criar_widget_card_filme(dados_filme, linha_grid, coluna_grid)

        self.frame_interno_resultados.update_idletasks() # Atualiza o layout antes de configurar o scroll
        self._atualizar_scrollregion_resultados()

    def _criar_widget_card_filme(self, dados_filme: Dict[str, Any], linha: int, coluna: int) -> None:
        """Cria um card individual para um filme na lista de resultados."""
        frame_card = customtkinter.CTkFrame(
            self.frame_interno_resultados,
            fg_color=COR_INPUT_FUNDO, # Cor de fundo do card
            border_color=COR_BORDA_CLARA,
            border_width=1,
            corner_radius=10
        )
        frame_card.grid(row=linha, column=coluna, padx=12, pady=12, sticky="nsew")
        frame_card.grid_rowconfigure(0, weight=0)  # Para o poster
        frame_card.grid_rowconfigure(1, weight=1)  # Para o título (para centralizar e dar espaço)
        frame_card.grid_columnconfigure(0, weight=1)

        # Label para o poster (com placeholder)
        label_poster = customtkinter.CTkLabel(
            frame_card, text="", width=LARGURA_POSTER_LISTA, height=ALTURA_POSTER_LISTA,
            fg_color=COR_PLACEHOLDER, text_color=COR_TEXTO_CLARO, font=self.fonte_normal,
            corner_radius=6
        )
        label_poster.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="n")

        titulo_filme_str = dados_filme.get('title', 'Título Indisponível')
        label_titulo = customtkinter.CTkLabel(
            frame_card, text=titulo_filme_str, font=self.fonte_negrito,
            text_color=COR_TEXTO_ESCURO, wraplength=LARGURA_POSTER_LISTA + 5 # Ajuste para quebra de linha
        )
        label_titulo.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="sew") # sticky="s" para alinhar na base

        # Carregar imagem do poster
        caminho_poster = dados_filme.get('poster_path')
        if caminho_poster:
            # Verifica cache antes de iniciar thread
            if caminho_poster in self.cache_poster_lista:
                label_poster.configure(image=self.cache_poster_lista[caminho_poster], text="")
            else:
                thread_poster = threading.Thread(
                    target=self._thread_carregar_poster,
                    args=(caminho_poster, label_poster, self.cache_poster_lista, (LARGURA_POSTER_LISTA, ALTURA_POSTER_LISTA)),
                    daemon=True
                )
                thread_poster.start()
        else:
            label_poster.configure(text="Sem Pôster", fg_color=COR_PLACEHOLDER, text_color=COR_TEXTO_CLARO)

        # --- Evento de clique para mostrar detalhes ---
        # Usar uma função lambda para passar os dados do filme específico
        frame_card.bind("<Button-1>", lambda event, df=dados_filme: self._mostrar_view_detalhes_filme(df))
        label_poster.bind("<Button-1>", lambda event, df=dados_filme: self._mostrar_view_detalhes_filme(df))
        label_titulo.bind("<Button-1>", lambda event, df=dados_filme: self._mostrar_view_detalhes_filme(df))

        # Efeito Hover no card
        def ao_entrar_card(event): frame_card.configure(border_color=COR_PRIMARIA, border_width=2)
        def ao_sair_card(event): frame_card.configure(border_color=COR_BORDA_CLARA, border_width=1)
        frame_card.bind("<Enter>", ao_entrar_card)
        frame_card.bind("<Leave>", ao_sair_card)

    def _thread_carregar_poster(self, caminho_poster: str, label_widget: customtkinter.CTkLabel, cache_poster: Dict, tamanho_poster: Tuple[int, int]) -> None:
        """Thread para carregar uma imagem de poster e atualizar o widget."""
        if caminho_poster in cache_poster: # Checagem dupla, caso outra thread tenha sido mais rápida
             self.after(0, lambda: self._atualizar_widget_com_poster(label_widget, cache_poster[caminho_poster]))
             return

        # Usar 'w300' ou 'w400' para melhor qualidade ao redimensionar para tamanhos menores
        url_poster_completo = f"{BASE_URL_IMG_TMDB}w342/{caminho_poster}"
        try:
            response = requests.get(url_poster_completo, timeout=10)
            response.raise_for_status()
            dados_imagem = response.content
            imagem_pil = Image.open(io.BytesIO(dados_imagem))
            imagem_pil = imagem_pil.resize(tamanho_poster, Image.Resampling.LANCZOS) # Redimensiona com alta qualidade
            imagem_ctk = ImageTk.PhotoImage(imagem_pil)

            cache_poster[caminho_poster] = imagem_ctk # Adiciona ao cache
            self.after(0, lambda: self._atualizar_widget_com_poster(label_widget, imagem_ctk))

        except requests.exceptions.RequestException as e:
            print(f"Erro ao carregar imagem {url_poster_completo}: {e}")
            self.after(0, lambda: label_widget.configure(text="Erro Img", fg_color=COR_ERRO, text_color=COR_TEXTO_CLARO))
        except Exception as e: # Captura outros erros (PIL, etc.)
            print(f"Erro ao processar imagem {url_poster_completo}: {e}")
            self.after(0, lambda: label_widget.configure(text="Falha Img", fg_color=COR_ERRO, text_color=COR_TEXTO_CLARO))

    def _atualizar_widget_com_poster(self, label_poster: customtkinter.CTkLabel, imagem_photo: ImageTk.PhotoImage) -> None:
        """Atualiza o widget de label com a imagem do poster carregada (executado na thread principal)."""
        if label_poster.winfo_exists(): # Verifica se o widget ainda existe
            label_poster.configure(image=imagem_photo, text="") # Limpa texto placeholder
            label_poster.image = imagem_photo # Mantém uma referência para evitar garbage collection

    def _exibir_mensagem_nos_resultados(self, mensagem: str, eh_erro: bool = False) -> None:
        """Exibe uma mensagem (ex: "Nenhum filme encontrado") na área de resultados."""
        self._limpar_cards_resultados_anteriores() # Limpa qualquer conteúdo anterior

        cor_texto_msg = COR_ERRO if eh_erro else COR_TEXTO_ESCURO
        label_msg_resultados = customtkinter.CTkLabel(
            self.frame_interno_resultados,
            text=mensagem,
            font=self.fonte_grande,
            text_color=cor_texto_msg,
            wraplength=self.frame_interno_resultados.winfo_width() - 60 # Para quebra de linha
        )
        label_msg_resultados.grid(row=0, column=0, columnspan=COLUNAS_GRID_RESULTADOS, pady=60, padx=30, sticky="ew")
        self.frame_interno_resultados.update_idletasks()
        self._atualizar_scrollregion_resultados()

    # --- Lógica da Tela de Detalhes do Filme ---

    def _limpar_widgets_detalhes_filme(self) -> None:
        """Limpa os campos da tela de detalhes antes de carregar novas informações."""
        self.label_poster_detalhe.configure(image=None, text="", fg_color=COR_INPUT_FUNDO) # Placeholder visual
        self.label_poster_detalhe.image = None # Remove referência
        self.label_titulo_filme_detalhe.configure(text="")
        self.label_tagline_filme_detalhe.configure(text="")
        self.label_sinopse_filme_detalhe.configure(text="")
        self.label_data_lancamento_filme.configure(text="Data de Lançamento: ")
        self.label_generos_filme.configure(text="Gêneros: ")
        self.label_duracao_filme.configure(text="Duração: ")
        self.label_avaliacao_filme.configure(text="Avaliação: ")

    def _exibir_placeholders_detalhes(self) -> None:
        """Exibe textos de 'carregando' enquanto os detalhes são buscados."""
        self.label_poster_detalhe.configure(text="Carregando Pôster...", fg_color=COR_PLACEHOLDER, text_color=COR_TEXTO_CLARO)
        self.label_titulo_filme_detalhe.configure(text="Carregando Título...")
        self.label_tagline_filme_detalhe.configure(text="...")
        self.label_sinopse_filme_detalhe.configure(text="Carregando sinopse...")
        self.label_data_lancamento_filme.configure(text="Data de Lançamento: Carregando...")
        self.label_generos_filme.configure(text="Gêneros: Carregando...")
        self.label_duracao_filme.configure(text="Duração: Carregando...")
        self.label_avaliacao_filme.configure(text="Avaliação: Carregando...")


    def _buscar_e_preencher_detalhes_completos_filme(self, filme_id: int) -> None:
        """Busca os detalhes completos de um filme pela API e preenche a view."""
        url_detalhes = f"{BASE_URL_TMDB}/movie/{filme_id}?api_key={self.api_key}&language=pt-BR&append_to_response=credits"
        try:
            response = requests.get(url_detalhes, timeout=10)
            response.raise_for_status()
            dados_completos = response.json()
            self.after(0, lambda: self._preencher_widgets_detalhes_filme(dados_completos))
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar detalhes do filme ID {filme_id}: {e}")
            self.after(0, lambda: self._preencher_widgets_detalhes_filme({"erro": f"Erro ao buscar detalhes: {e}"}))
        except ValueError:
            print(f"Erro ao decodificar JSON para detalhes do filme ID {filme_id}")
            self.after(0, lambda: self._preencher_widgets_detalhes_filme({"erro": "Erro ao processar dados do filme."}))

    def _preencher_widgets_detalhes_filme(self, detalhes: Dict[str, Any]) -> None:
        """Preenche os widgets da tela de detalhes com as informações do filme."""
        if "erro" in detalhes:
            self.label_titulo_filme_detalhe.configure(text=detalhes["erro"], text_color=COR_ERRO)
            self.label_sinopse_filme_detalhe.configure(text="") # Limpa outros campos
            return

        self.label_titulo_filme_detalhe.configure(text=detalhes.get('title', 'Título Indisponível'))
        self.label_tagline_filme_detalhe.configure(text=detalhes.get('tagline', ''))

        sinopse = detalhes.get('overview', 'Sinopse não disponível.')
        self.label_sinopse_filme_detalhe.configure(text=sinopse if sinopse else "Sinopse não disponível.")

        data_lancamento_str = "Data de Lançamento: "
        data_raw = detalhes.get('release_date')
        if data_raw:
            try:
                # Formato esperado da API: YYYY-MM-DD
                ano, mes, dia = data_raw.split('-')
                data_lancamento_str += f"{dia}/{mes}/{ano}"
            except ValueError:
                 data_lancamento_str += data_raw # Se o formato for inesperado
        else:
            data_lancamento_str += "N/A"
        self.label_data_lancamento_filme.configure(text=data_lancamento_str)

        generos_lista = [g['name'] for g in detalhes.get('genres', [])]
        self.label_generos_filme.configure(text=f"Gêneros: {', '.join(generos_lista) if generos_lista else 'N/A'}")

        duracao_minutos = detalhes.get('runtime')
        duracao_str = "Duração: "
        if duracao_minutos and isinstance(duracao_minutos, int) and duracao_minutos > 0 :
            horas = duracao_minutos // 60
            minutos_restantes = duracao_minutos % 60
            if horas > 0:
                duracao_str += f"{horas}h "
            duracao_str += f"{minutos_restantes}min"
        else:
            duracao_str += "N/A"
        self.label_duracao_filme.configure(text=duracao_str)

        avaliacao_media = detalhes.get('vote_average')
        contagem_votos = detalhes.get('vote_count')
        avaliacao_str = "Avaliação: "
        if isinstance(avaliacao_media, (float, int)) and avaliacao_media > 0:
            avaliacao_str += f"{avaliacao_media:.1f}/10 ({contagem_votos} votos)"
        else:
            avaliacao_str += "N/A"
        self.label_avaliacao_filme.configure(text=avaliacao_str)

        # Carregar poster para a tela de detalhes
        caminho_poster_detalhe = detalhes.get('poster_path')
        if caminho_poster_detalhe:
            if caminho_poster_detalhe in self.cache_poster_detalhe:
                self._atualizar_widget_com_poster(self.label_poster_detalhe, self.cache_poster_detalhe[caminho_poster_detalhe])
            else:
                thread_poster_det = threading.Thread(
                    target=self._thread_carregar_poster,
                    args=(caminho_poster_detalhe, self.label_poster_detalhe, self.cache_poster_detalhe, (LARGURA_POSTER_DETALHE, ALTURA_POSTER_DETALHE)),
                    daemon=True
                )
                thread_poster_det.start()
        else:
            self.label_poster_detalhe.configure(text="Sem Pôster", image=None, fg_color=COR_PLACEHOLDER, text_color=COR_TEXTO_CLARO)


    # --- Funções Utilitárias e de Scroll ---

    def _configurar_largura_frame_interno_canvas(self, event: Any) -> None:
        """Ajusta a largura do frame interno do canvas para preencher o canvas."""
        largura_canvas = event.width
        self.canvas_resultados.itemconfig(self.id_janela_canvas_resultados, width=largura_canvas)
        self._atualizar_scrollregion_resultados() # Chamar aqui também pode ajudar

    def _atualizar_scrollregion_resultados(self, event: Optional[Any] = None) -> None:
        """Atualiza a região de scroll do canvas de resultados."""
        # É crucial que o frame_interno_resultados tenha seu layout atualizado
        self.frame_interno_resultados.update_idletasks()
        # Define a scrollregion para o bounding box de todos os itens no frame_interno_resultados
        bbox = self.frame_interno_resultados.bbox("all")
        if bbox: # bbox pode ser None se não houver widgets
            self.canvas_resultados.config(scrollregion=bbox)
        else: # Se não houver conteúdo, reseta a scrollregion
            self.canvas_resultados.config(scrollregion=(0,0,0,0))


    def _exibir_mensagem_temporaria(self, mensagem: str, duracao_ms: int = 3000, eh_erro: bool = False) -> None:
        """Exibe uma mensagem flutuante temporária (toast)."""
        # Cria um Toplevel para a mensagem flutuante
        toast = customtkinter.CTkToplevel(self)
        toast.overrideredirect(True) # Remove decorações da janela
        toast.attributes("-alpha", 0.95) # Leve transparência
        toast.attributes("-topmost", True) # Mantém no topo

        cor_fg_toast = COR_ERRO if eh_erro else COR_PRIMARIA
        cor_texto_toast = COR_TEXTO_CLARO if eh_erro else COR_TEXTO_CLARO # Ajustar se necessário

        label_toast = customtkinter.CTkLabel(
            toast,
            text=mensagem,
            font=self.fonte_normal,
            fg_color=cor_fg_toast,
            text_color=cor_texto_toast,
            corner_radius=8,
            padx=20,
            pady=10
        )
        label_toast.pack(fill="both", expand=True)

        # Posiciona o toast
        self.update_idletasks() # Garante que as dimensões da janela principal estejam atualizadas
        main_win_x = self.winfo_x()
        main_win_y = self.winfo_y()
        main_win_width = self.winfo_width()
        # main_win_height = self.winfo_height()

        toast.update_idletasks() # Para obter as dimensões do toast
        toast_width = label_toast.winfo_width()
        toast_height = label_toast.winfo_height()

        pos_x = main_win_x + (main_win_width // 2) - (toast_width // 2)
        pos_y = main_win_y + 50 # Perto do topo da janela principal

        toast.geometry(f"{toast_width}x{toast_height}+{pos_x}+{pos_y}")

        def fechar_toast():
            if toast.winfo_exists():
                toast.destroy()
        self.after(duracao_ms, fechar_toast)

    def _ao_fechar_janela(self) -> None:
        """Chamado quando a janela principal é fechada."""
        print("Encerrando BeeView...")
        self.destroy()


if __name__ == "__main__":
    # Configurações globais do CustomTkinter
    customtkinter.set_appearance_mode("Dark")  # Ou "Light", "System" - "Dark" combina melhor com as cores escuras
    customtkinter.set_default_color_theme("blue") # Ou "green", "dark-blue"

    app = BeeViewApp()
    app.mainloop()
