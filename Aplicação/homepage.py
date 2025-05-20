import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import requests
import io
import platform
from concurrent.futures import ThreadPoolExecutor
import logging
import gc # Garbage Collector
import sys # Para adicionar ao path, se necessário

# Configure logging to catch and display errors
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

# --- Constants ---
class Estilo:
    """Styling constants for the application."""
    BACKGROUND_COLOR = "#1a1a1a"
    CONTAINER_COLOR = "#242424"
    TEXT_COLOR = "#ffffff"
    ACCENT_COLOR = "#ffdb58"  # A vibrant yellow, like honey
    FRAME_COLOR = "#323232"
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_SMALL = 10
    FONT_SIZE_LARGE = 16
    FONT_SIZE_XLARGE = 24
    FONT_SIZE_XXLARGE = 48

class API:
    """API constants for The Movie Database (TMDB)."""
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    KEY = "5968e0e2ae961359489ef818f486a395" # Replace with your actual TMDB API key
    LANGUAGE = "pt-BR"
    BASE_URL = "https://api.themoviedb.org/3"
    TRENDING_MOVIES_URL = f"{BASE_URL}/trending/movie/week?api_key={KEY}&language={LANGUAGE}"
    BRAZILIAN_MOVIES_URL = f"{BASE_URL}/discover/movie?api_key={KEY}&language={LANGUAGE}&region=BR&with_original_language=pt&sort_by=vote_average.desc,popularity.desc"
    MOVIE_DETAILS_URL_TEMPLATE = f"{BASE_URL}/movie/{{movie_id}}?api_key={KEY}&language={LANGUAGE}"

# --- Helper Functions ---
def fetch_api_data(url):
    """Fetches data from the specified API URL."""
    try:
        response = requests.get(url, timeout=10) # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return None

def load_image_from_url(url):
    """Loads an image from a URL."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=10) # Added timeout
        response.raise_for_status()
        image_data = response.content
        return Image.open(io.BytesIO(image_data))
    except requests.exceptions.RequestException as e:
        logging.error(f"Error loading image from {url}: {e}")
        return None
    except IOError as e:
        logging.error(f"Error opening image data from {url}: {e}")
        return None

class BeeViewApp(ctk.CTk):
    """
    Main application class for BeeView, a movie browsing and analysis tool.
    """
    def __init__(self):
        super().__init__()

        self.title("BeeView - Análise de Filmes")
        self.geometry("960x540")
        self.configure(bg=Estilo.BACKGROUND_COLOR)
        self.resizable(True, True)

        # --- Core App Setup ---
        self.executor = ThreadPoolExecutor(max_workers=5) # For background tasks
        self.image_cache = {} # Cache for loaded ImageTk.PhotoImage objects

        # --- Main Layout ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_canvas = tk.Canvas(self, borderwidth=0, background=Estilo.BACKGROUND_COLOR, highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview,
                                      bg=Estilo.CONTAINER_COLOR, troughcolor=Estilo.BACKGROUND_COLOR,
                                      highlightthickness=0, bd=0, activebackground=Estilo.ACCENT_COLOR)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.main_content_frame = ctk.CTkFrame(self.main_canvas, fg_color=Estilo.BACKGROUND_COLOR)
        self.main_content_frame.grid_rowconfigure(0, weight=1) 
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.main_content_frame, anchor="nw")

        self.main_content_frame.bind("<Configure>", self._on_frame_configure)
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel_scrolling()

        # --- Navigation and State ---
        self.current_view = None 
        self.back_button = None 

        self.display_home_screen()

    def _on_frame_configure(self, event=None):
        """Updates the scroll region of the canvas when main_content_frame size changes."""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        """Updates the width of the frame inside the canvas when canvas size changes."""
        self.main_canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel_scrolling(self):
        """Binds mouse wheel scrolling to the main canvas for different platforms."""
        def _on_mousewheel(event):
            if platform.system() == "Windows":
                scroll_delta = int(-1 * (event.delta / 120))
            elif platform.system() == "Darwin": # macOS
                scroll_delta = int(-1 * event.delta)
            else: # Linux and other X11
                if event.num == 4: 
                    scroll_delta = -1
                elif event.num == 5: 
                    scroll_delta = 1
                else:
                    scroll_delta = 0
            self.main_canvas.yview_scroll(scroll_delta, "units")

        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.main_canvas.bind_all("<Button-4>", _on_mousewheel)
        self.main_canvas.bind_all("<Button-5>", _on_mousewheel)

    def _clear_main_content_frame(self):
        """Destroys all widgets within the main_content_frame and collects garbage."""
        if self.back_button and self.back_button.winfo_exists():
            self.back_button.destroy()
            self.back_button = None
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        gc.collect()

    def _create_static_home_elements(self):
        """Creates the static elements of the home screen (title, buttons, section containers)."""
        title_label = ctk.CTkLabel(self.main_content_frame, text="BeeView",
                                   font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_XXLARGE, "bold"),
                                   text_color=Estilo.ACCENT_COLOR)
        title_label.pack(pady=(30, 10), anchor="center")

        buttons_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        buttons_frame.pack(pady=10, anchor="center", fill="x", padx=50)
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="btn")

        button_style = {
            "fg_color": Estilo.ACCENT_COLOR,
            "text_color": Estilo.BACKGROUND_COLOR,
            "hover_color": "#e5c100", 
            "width": 180, "height": 120,
            "corner_radius": 12,
            "font": (Estilo.FONT_FAMILY, Estilo.FONT_SIZE_LARGE, "bold")
        }

        ctk.CTkButton(buttons_frame, text="🎥\nAnálise de Filme", **button_style,
                      command=self.display_analise_filme_screen).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(buttons_frame, text="🏆\nBrasileiros no Oscar", **button_style).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(buttons_frame, text="🎬\nAnálise de Sequência", **button_style).grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        effect_phrase = ctk.CTkLabel(self.main_content_frame, text="Onde a análise encontra a magia do cinema.",
                                     font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL, "italic"),
                                     text_color="#aaa")
        effect_phrase.pack(pady=(5, 20), anchor="center")

        self.trending_section = self._create_movie_section_container("🔥 Filmes Populares Internacionais")
        self.brazilian_section = self._create_movie_section_container("🇧🇷 Top Filmes Brasileiros")

    def _create_movie_section_container(self, title):
        """Creates a container for a movie section with a title and a frame for movie boxes."""
        container = ctk.CTkFrame(self.main_content_frame, fg_color=Estilo.CONTAINER_COLOR, corner_radius=12)
        container.pack(pady=15, padx=20, fill="x", expand=True, anchor="center")

        label = ctk.CTkLabel(container, text=title,
                             font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_XLARGE, "bold"),
                             text_color=Estilo.TEXT_COLOR, anchor="w")
        label.pack(padx=15, pady=(10, 5), fill="x")

        movies_display_frame = ctk.CTkFrame(container, fg_color="transparent")
        movies_display_frame.pack(padx=10, pady=(0, 10), fill="x", expand=True)
        
        for i in range(5): 
            movies_display_frame.grid_columnconfigure(i, weight=1, uniform="movie_col")

        return {"container": container, "label": label, "movies_frame": movies_display_frame}

    def display_home_screen(self):
        """Clears the main frame and displays the home screen elements."""
        logging.info("Displaying home screen.")
        self._clear_main_content_frame()
        self.current_view = 'home'

        self._create_static_home_elements()

        self.executor.submit(self._fetch_and_populate_home_movies)
        self.main_canvas.yview_moveto(0)

    def _fetch_and_populate_home_movies(self):
        """Fetches trending and Brazilian movies and schedules UI update."""
        try:
            trending_movies_data = fetch_api_data(API.TRENDING_MOVIES_URL)
            brazilian_movies_data = fetch_api_data(API.BRAZILIAN_MOVIES_URL)

            trending_movies = trending_movies_data.get('results', [])[:5] if trending_movies_data else []
            brazilian_movies = brazilian_movies_data.get('results', [])[:5] if brazilian_movies_data else []

            self.after(0, self._update_home_movie_sections, trending_movies, brazilian_movies)
        except Exception as e:
            logging.error(f"Error fetching or processing home movies: {e}")
            self.after(0, self._show_error_message, "Não foi possível carregar os filmes.")

    def _update_home_movie_sections(self, trending_movies, brazilian_movies):
        """Populates the movie sections on the home screen. Called from main thread."""
        if not self.winfo_exists(): return

        if trending_movies:
            self._populate_movie_section_ui(self.trending_section["movies_frame"], trending_movies)
        else:
            self._show_message_in_section(self.trending_section["movies_frame"], "Nenhum filme popular encontrado.")

        if brazilian_movies:
            self._populate_movie_section_ui(self.brazilian_section["movies_frame"], brazilian_movies)
        else:
            self._show_message_in_section(self.brazilian_section["movies_frame"], "Nenhum filme brasileiro encontrado.")
        
        self._on_frame_configure()
        gc.collect()

    def _populate_movie_section_ui(self, movies_frame, movies_list):
        """Creates and places movie boxes into the given movies_frame."""
        if not movies_frame.winfo_exists(): return

        for widget in movies_frame.winfo_children():
            widget.destroy()

        for i, movie_data in enumerate(movies_list):
            col = i % 5 
            row = i // 5
            
            movie_box_container = ctk.CTkFrame(movies_frame, fg_color="transparent")
            movie_box_container.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            movie_box = self._create_movie_box_widget(movie_box_container, movie_data)
            movie_box.pack(expand=True, fill="both")

    def _create_movie_box_widget(self, parent_frame, movie_data):
        """Creates a single movie box widget."""
        movie_id = movie_data.get('id')
        
        box = ctk.CTkFrame(parent_frame, width=160, height=280,
                           corner_radius=10, fg_color=Estilo.FRAME_COLOR,
                           border_width=1, border_color="#444")
        box.pack_propagate(False)
        box.grid_columnconfigure(0, weight=1)

        poster_label = self._create_movie_poster_widget(box, movie_data.get('poster_path'), movie_id, (140, 200))
        poster_label.pack(pady=(10,5), padx=10)

        title_text = movie_data.get('title', 'Título Desconhecido')
        title_label = ctk.CTkLabel(box, text=title_text,
                                   font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL, "bold"),
                                   text_color=Estilo.TEXT_COLOR, wraplength=140, justify="center")
        title_label.pack(pady=(0,5), padx=5, fill="x")
        self._bind_click_to_details(title_label, movie_id)

        vote_avg = movie_data.get('vote_average')
        if vote_avg:
            info_text = f"Nota: {vote_avg:.1f} ⭐"
            info_label = ctk.CTkLabel(box, text=info_text,
                                      font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_SMALL),
                                      text_color="#ccc")
            info_label.pack(pady=(0,10), padx=5)
            self._bind_click_to_details(info_label, movie_id)
            
        self._bind_click_to_details(box, movie_id)
        box.configure(cursor="hand2")
        return box

    def _create_movie_poster_widget(self, parent_widget, poster_path, movie_id, size=(130, 110)):
        """Loads and displays a movie poster, using cache."""
        placeholder_text = "Sem Imagem"
        tk_image = None 
        
        cache_key = f"{poster_path}_{size[0]}x{size[1]}"

        if poster_path and cache_key in self.image_cache:
            tk_image = self.image_cache[cache_key]
        elif poster_path:
            image_url = f"{API.IMAGE_BASE_URL}{poster_path}"
            pil_image = load_image_from_url(image_url)
            if pil_image:
                try:
                    pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
                    tk_image = ImageTk.PhotoImage(pil_image)
                    self.image_cache[cache_key] = tk_image 
                except Exception as e:
                    logging.error(f"Error processing image {poster_path} with size {size}: {e}")
                    tk_image = None
                    placeholder_text = "Erro Imagem"
            else:
                tk_image = None
                placeholder_text = "Falha Carga"
        else:
            tk_image = None

        if tk_image:
            image_label = tk.Label(parent_widget, image=tk_image, bg=Estilo.FRAME_COLOR, relief="flat")
            image_label.image = tk_image 
        else:
            image_label = ctk.CTkLabel(parent_widget, text=placeholder_text,
                                       font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL),
                                       fg_color=Estilo.BACKGROUND_COLOR, 
                                       text_color="#777", width=size[0], height=size[1],
                                       corner_radius=8)
        
        if movie_id: 
             self._bind_click_to_details(image_label, movie_id)
             image_label.configure(cursor="hand2")
        else:
            image_label.configure(cursor="arrow")

        return image_label

    def _bind_click_to_details(self, widget, movie_id):
        """Binds a click event to a widget to show movie details."""
        if movie_id: 
            widget.bind("<Button-1>", lambda event, mid=movie_id: self.display_movie_details_screen(mid))

    def display_movie_details_screen(self, movie_id):
        """Displays the detailed information for a specific movie."""
        if not movie_id:
            logging.warning("Attempted to display details for invalid movie_id.")
            return
            
        logging.info(f"Displaying details for movie ID: {movie_id}")
        self._clear_main_content_frame()
        self.current_view = 'details'
        
        self.back_button = ctk.CTkButton(self.main_content_frame, text="⬅ Voltar",
                                         command=self.display_home_screen,
                                         fg_color=Estilo.ACCENT_COLOR, text_color=Estilo.BACKGROUND_COLOR,
                                         hover_color="#e5c100", corner_radius=8,
                                         font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL, "bold"))
        self.back_button.pack(pady=15, padx=20, anchor="nw")

        loading_label = ctk.CTkLabel(self.main_content_frame, text="Carregando detalhes...",
                                     font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_LARGE), text_color=Estilo.TEXT_COLOR)
        loading_label.pack(pady=50, anchor="center")

        self.main_canvas.yview_moveto(0)
        self.executor.submit(self._fetch_and_display_movie_details, movie_id, loading_label)

    def _fetch_and_display_movie_details(self, movie_id, loading_label_ref):
        """Fetches movie details and schedules UI update."""
        try:
            details_url = API.MOVIE_DETAILS_URL_TEMPLATE.format(movie_id=movie_id)
            movie_details = fetch_api_data(details_url)
            
            self.after(0, self._populate_movie_details_ui, movie_details, loading_label_ref)
        except Exception as e:
            logging.error(f"Error fetching details for movie {movie_id}: {e}")
            self.after(0, self._show_error_message, f"Não foi possível carregar detalhes do filme ID: {movie_id}.", loading_label_ref)

    def _populate_movie_details_ui(self, movie_details, loading_label_to_remove=None):
        """Populates the UI with movie details. Called from main thread."""
        if not self.winfo_exists(): return

        if loading_label_to_remove and loading_label_to_remove.winfo_exists():
            loading_label_to_remove.destroy()

        if not movie_details:
            self._show_error_message("Detalhes do filme não encontrados ou erro na API.")
            return

        try:
            title_label = ctk.CTkLabel(self.main_content_frame, text=movie_details.get('title', 'Sem Título'),
                                       font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_XXLARGE, "bold"),
                                       text_color=Estilo.TEXT_COLOR, wraplength=800, justify="center")
            title_label.pack(pady=(0, 20), padx=20, anchor="center")

            details_container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
            details_container.pack(pady=10, padx=20, fill="x", anchor="center")
            details_container.grid_columnconfigure(0, weight=1) 
            details_container.grid_columnconfigure(1, weight=2) 

            poster_frame = ctk.CTkFrame(details_container, fg_color="transparent")
            poster_frame.grid(row=0, column=0, padx=(0,20), sticky="n")
            poster_widget = self._create_movie_poster_widget(poster_frame, movie_details.get('poster_path'), None, size=(250, 375))
            poster_widget.pack(anchor="center")


            info_frame = ctk.CTkFrame(details_container, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="nw")

            def add_detail_label(text_value, bold=False):
                font_weight = "bold" if bold else "normal"
                label = ctk.CTkLabel(info_frame, text=text_value,
                                     font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL + (2 if bold else 0), font_weight),
                                     text_color=Estilo.TEXT_COLOR, wraplength=550, justify="left", anchor="w")
                label.pack(pady=(2,5), fill="x")
                return label

            if movie_details.get('tagline'):
                add_detail_label(f"\"{movie_details['tagline']}\"", bold=True).configure(font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL, "italic"))
            
            add_detail_label("Sinopse:", bold=True)
            overview_text = movie_details.get('overview', 'Sinopse não disponível.')
            overview_label = ctk.CTkLabel(info_frame, text=overview_text,
                                          font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL),
                                          text_color="#ddd", wraplength=550, justify="left", anchor="w")
            overview_label.pack(pady=(0,10), fill="x")

            add_detail_label(f"Data de Lançamento: {movie_details.get('release_date', 'N/A')}")
            vote_avg_text = 'N/A'
            if movie_details.get('vote_average') is not None:
                vote_avg_text = f"{movie_details.get('vote_average'):.1f}"
            add_detail_label(f"Avaliação: {vote_avg_text} ⭐ ({movie_details.get('vote_count', 0)} votos)")
            
            genres = ", ".join([genre['name'] for genre in movie_details.get('genres', [])])
            add_detail_label(f"Gêneros: {genres if genres else 'N/A'}")
            
            runtime = movie_details.get('runtime')
            if runtime: add_detail_label(f"Duração: {runtime // 60}h {runtime % 60}min")
            
            add_detail_label(f"Idioma Original: {movie_details.get('original_language', 'N/A').upper()}")
            
            companies = ", ".join([comp['name'] for comp in movie_details.get('production_companies', [])[:2]])
            if companies: add_detail_label(f"Produção: {companies}")
            
            if movie_details.get('budget', 0) > 0:
                add_detail_label(f"Orçamento: ${movie_details['budget']:,}")
            if movie_details.get('revenue', 0) > 0:
                add_detail_label(f"Receita: ${movie_details['revenue']:,}")

        except Exception as e:
            logging.error(f"Error creating movie details UI: {e}")
            self._show_error_message("Erro ao exibir detalhes do filme.")
        finally:
            self._on_frame_configure()
            gc.collect()

    def display_analise_filme_screen(self):
        """Displays the 'Análise de Filme' screen."""
        logging.info("Displaying Análise de Filme screen.")
        self._clear_main_content_frame()
        self.current_view = 'analise_filme'

        self.back_button = ctk.CTkButton(self.main_content_frame, text="⬅ Voltar para Home",
                                         command=self.display_home_screen,
                                         fg_color=Estilo.ACCENT_COLOR, text_color=Estilo.BACKGROUND_COLOR,
                                         hover_color="#e5c100", corner_radius=8,
                                         font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL, "bold"))
        self.back_button.pack(pady=15, padx=20, anchor="nw")

        title_label = ctk.CTkLabel(self.main_content_frame, text="Análise Detalhada de Filme",
                                   font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_XLARGE, "bold"),
                                   text_color=Estilo.TEXT_COLOR)
        title_label.pack(pady=(10, 20), padx=20, anchor="center")

        # --- Integration of analise_filmes.py content ---
        try:
            # Tentativa de adicionar o diretório do script ao sys.path
            # Isso é útil se analise_filmes.py não estiver no mesmo diretório ou no PYTHONPATH
            # NOTA: O caminho fornecido pelo usuário é absoluto. Se o arquivo estiver em um local fixo,
            # pode ser necessário ajustar esta lógica ou garantir que o PYTHONPATH esteja configurado.
            # Para este exemplo, vamos assumir que 'analise_filmes.py' está em um diretório chamado 'Aplicação'
            # que é irmão do diretório onde este script principal está, ou que está no PYTHONPATH.
            # Exemplo de como adicionar um caminho específico se necessário:
            # script_dir = os.path.dirname(os.path.abspath(__file__)) # Diretório do script atual
            # analise_module_path = os.path.join(script_dir, "Aplicação") # Exemplo
            # if analise_module_path not in sys.path:
            # sys.path.append(analise_module_path)

            from analise_filmes import create_ui as create_analise_filme_ui # Tenta importar
            # Passa o frame pai, as constantes de estilo e o executor de threads para o módulo de análise
            create_analise_filme_ui(self.main_content_frame, Estilo, self.executor) 
            logging.info("analise_filmes.py UI loaded successfully.")
        except ImportError as e:
            logging.error(f"Could not import 'create_ui' from analise_filmes.py: {e}. Make sure the file exists and is in PYTHONPATH.")
            error_message = ("Erro: Módulo 'analise_filmes.py' não encontrado ou não configurado corretamente.\n"
                             "Verifique se o arquivo está no local esperado e se o nome da função de UI está correto (ex: create_ui).")
            error_label = ctk.CTkLabel(self.main_content_frame, 
                                       text=error_message,
                                       font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL), text_color="red",
                                       wraplength=700, justify="center")
            error_label.pack(pady=20, padx=20, anchor="center", expand=True)
        except Exception as e:
            logging.error(f"Error loading UI from analise_filmes.py: {e}")
            error_label = ctk.CTkLabel(self.main_content_frame, 
                                       text=f"Erro ao carregar a interface de análise: {e}",
                                       font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL), text_color="red",
                                       wraplength=700, justify="center")
            error_label.pack(pady=20, padx=20, anchor="center", expand=True)
        # --- End of integration ---

        self.main_canvas.yview_moveto(0) 
        self._on_frame_configure() 

    def _show_error_message(self, message, label_to_remove=None):
        """Displays an error message in the main content frame."""
        if not self.winfo_exists(): return

        if label_to_remove and label_to_remove.winfo_exists():
            label_to_remove.destroy()
        
        # Limpa o conteúdo anterior, exceto o botão de voltar, se existir
        # e se a visão atual permitir um botão de voltar.
        widgets_to_destroy = []
        for widget in self.main_content_frame.winfo_children():
            if widget != self.back_button:
                 widgets_to_destroy.append(widget)
        for widget in widgets_to_destroy:
            widget.destroy()


        error_label = ctk.CTkLabel(self.main_content_frame, text=message,
                                   font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_LARGE),
                                   text_color="red", wraplength=800, justify="center")
        
        # Garante que o botão de voltar (se aplicável à view) seja empacotado novamente
        # se tiver sido destruído inadvertidamente ou se a tela de erro o cobrir.
        # No entanto, _clear_main_content_frame já lida com a destruição do back_button.
        # Se um erro ocorre, e um back_button existia (ex: na tela de detalhes),
        # ele é destruído por _clear_main_content_frame ANTES de _show_error_message ser chamada
        # (geralmente _show_error_message é chamada após _clear_main_content_frame).
        # Se a tela de erro DEVE ter um botão de voltar, ele precisa ser criado aqui.
        # Por ora, a tela de erro substitui todo o conteúdo, incluindo um possível botão de voltar anterior.
        # Se o erro ocorre na home (onde não há back_button), nada muda.
        # Se ocorre em 'details' ou 'analise_filme', o back_button específico daquela tela é limpo.
        # Um botão "Voltar para Home" genérico poderia ser adicionado aqui se desejado para todas as telas de erro.

        error_label.pack(pady=20, padx=20, anchor="center", expand=True)
        self._on_frame_configure()

    def _show_message_in_section(self, section_frame, message):
        """Displays a message (e.g., 'No movies found') within a movie section frame."""
        if not section_frame.winfo_exists(): return
        for widget in section_frame.winfo_children():
            widget.destroy()
        msg_label = ctk.CTkLabel(section_frame, text=message,
                                 font=(Estilo.FONT_FAMILY, Estilo.FONT_SIZE_NORMAL),
                                 text_color="#aaa")
        msg_label.pack(pady=20, padx=10, anchor="center")

    def run(self):
        """Starts the Tkinter main event loop."""
        self.mainloop()

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) 
    except Exception:
        logging.info("Could not set DPI awareness (not on Windows or ctypes issue).")

    ctk.set_appearance_mode("Dark") 
    ctk.set_default_color_theme("blue") 
    
    app = BeeViewApp()
    app.run()
