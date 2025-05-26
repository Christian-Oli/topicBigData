# contents/modules/homepage_model.py
import customtkinter as ctk
import requests
from PIL import Image, ImageDraw, ImageTk
from io import BytesIO
import math
import tkinter as tk # Para o after, e tk.font
import time
import os
import sys

# --- Paleta de Cores BeeView ---
COLOR_BACKGROUND = "#040500"
COLOR_YELLOW_BASE = "#fff400"
COLOR_WHITE_CREAM = "#fffdd0"
COLOR_YELLOW_DARK = "#ffcf00"
COLOR_BUTTON_TEXT = COLOR_WHITE_CREAM
COLOR_YELLOW_BUTTON_TEXT = "#000000"

# --- Configurações da API TMDB ---
API_KEY = "5968e0e2ae961359489ef818f486a395"
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w300"
TRENDING_GLOBAL_URL = f"https://api.themoviedb.org/3/trending/movie/week?api_key={API_KEY}&language=pt-BR"
DISCOVER_BRASIL_URL = f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=pt-BR&region=BR&sort_by=popularity.desc&with_original_language=pt&with_origin_country=BR&include_adult=false"

# --- Configurações do Hexágono ---
HEXAGON_BASE_WIDTH = 150
HEXAGON_BASE_HEIGHT = int(HEXAGON_BASE_WIDTH * 2 / math.sqrt(3))
HEXAGON_HOVER_SCALE = 1.12
HEXAGON_HOVER_WIDTH = int(HEXAGON_BASE_WIDTH * HEXAGON_HOVER_SCALE)
HEXAGON_HOVER_HEIGHT = int(HEXAGON_BASE_HEIGHT * HEXAGON_HOVER_SCALE)
HEXAGON_BORDER_COLOR = COLOR_YELLOW_BASE
HEXAGON_BORDER_WIDTH = 3

PROGRESS_BAR_UPDATE_INTERVAL_MS = 50

class HomePageTestApp(ctk.CTkFrame): # Inherits from CTkFrame
    def __init__(self, master, current_user, logout_callback):
        super().__init__(master)
        
        self.master_window = master
        self.current_user = current_user
        self.logout_callback = logout_callback

        self.configure(fg_color=COLOR_BACKGROUND)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # For loading screen, then row 1 for content

        self.pil_image_cache = {}
        self.movie_card_images = {}
        self.placeholder_image_ctk = None
        
        self.fetched_global_movies = []
        self.fetched_brasil_movies = []
        
        self.total_assets_to_load = 0
        self.assets_loaded_count = 0

        self._show_loading_screen()

    def _init_main_ui(self):
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._create_top_bar()

        self.main_content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(1, weight=1)
        
        self.placeholder_image_ctk = self._create_placeholder_ctk_image((HEXAGON_BASE_WIDTH, HEXAGON_BASE_HEIGHT))
        
        self._populate_sections_with_loaded_data()

    def _create_top_bar(self):
        self.top_bar_frame = ctk.CTkFrame(self, height=80, fg_color="transparent", corner_radius=0)
        self.top_bar_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar_frame.grid_columnconfigure(0, weight=1)
        self.top_bar_frame.grid_columnconfigure(1, weight=0)

        title_container = ctk.CTkFrame(self.top_bar_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, padx=35, pady=20, sticky="w")
        
        try:
            title_font_family = "Bahnschrift"
            ctk.CTkFont(family=title_font_family)
        except:
            title_font_family = "Arial"
        title_font = ctk.CTkFont(family=title_font_family, size=44, weight="bold")

        bee_label = ctk.CTkLabel(title_container, text="Bee", font=title_font, text_color=COLOR_YELLOW_BASE)
        bee_label.pack(side="left")
        view_label = ctk.CTkLabel(title_container, text="View", font=title_font, text_color=COLOR_WHITE_CREAM)
        view_label.pack(side="left")

        buttons_container = ctk.CTkFrame(self.top_bar_frame, fg_color="transparent")
        buttons_container.grid(row=0, column=1, padx=(0,25), pady=10, sticky="e")

        button_font = ctk.CTkFont(family="Segoe UI Semibold" if "Segoe UI Semibold" in tk.font.families() else "Arial",
                                  size=14, weight="bold")
        
        common_button_height = 45
        common_button_corner_radius = 22

        common_button_args = {
            "text_color": COLOR_YELLOW_BUTTON_TEXT,
            "hover_color": COLOR_YELLOW_DARK,
            "font": button_font,
            "height": common_button_height,
            "corner_radius": common_button_corner_radius
        }
        
        btn_pesquisar = ctk.CTkButton(buttons_container, text="Pesquisar", width=150, fg_color=COLOR_YELLOW_BASE, **common_button_args)
        btn_pesquisar.pack(side="left", padx=5)
        
        btn_analise = ctk.CTkButton(buttons_container, text="Análise de Sequência", width=200, fg_color=COLOR_YELLOW_BASE, **common_button_args)
        btn_analise.pack(side="left", padx=5)
        
        btn_oscar = ctk.CTkButton(buttons_container, text="Brasil No Oscar", width=180, fg_color=COLOR_YELLOW_BASE, **common_button_args)
        btn_oscar.pack(side="left", padx=5)

        btn_logout = ctk.CTkButton(
            buttons_container,
            text=f"Logout ({self.current_user[:10]})",
            width=150,
            height=common_button_height,
            corner_radius=common_button_corner_radius,
            font=button_font,
            fg_color="#555555",
            text_color=COLOR_WHITE_CREAM,
            hover_color="#777777",
            command=self.logout_callback
        )
        btn_logout.pack(side="left", padx=(10,5))

    def _show_loading_screen(self):
        self.loading_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        self.loading_frame.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.loading_frame.grid_columnconfigure(0, weight=1)
        self.loading_frame.grid_rowconfigure(0, weight=1) 
        self.loading_frame.grid_rowconfigure(1, weight=0) 
        self.loading_frame.grid_rowconfigure(2, weight=1) 

        loading_label = ctk.CTkLabel(self.loading_frame, text="Carregando BeeView...",
                                     font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
                                     text_color=COLOR_WHITE_CREAM)
        loading_label.grid(row=0, column=0, pady=(0, 20), sticky="s")

        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400, height=20, corner_radius=10,
                                               progress_color=COLOR_YELLOW_BASE, fg_color=COLOR_YELLOW_DARK) 
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, pady=20, sticky="n")
        
        self.after(100, self._start_asset_loading_process)

    def _update_loading_progress(self):
        if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            progress = 0
            if self.total_assets_to_load > 0:
                progress = self.assets_loaded_count / self.total_assets_to_load
            self.progress_bar.set(progress)

    def _start_asset_loading_process(self):
        self.assets_loaded_count = 0
        self.total_assets_to_load = 2 
        self._update_loading_progress()
        self.after(10, self._fetch_all_json_data_then_images)

    def _fetch_all_json_data_then_images(self):
        if not self.winfo_exists(): return

        print("Buscando dados JSON globais...")
        self.fetched_global_movies = self._fetch_api_data(TRENDING_GLOBAL_URL)
        self.assets_loaded_count += 1
        self._update_loading_progress()
        if self.winfo_exists(): self.update_idletasks()

        if not self.winfo_exists(): return

        print("Buscando dados JSON do Brasil...")
        self.fetched_brasil_movies = self._fetch_api_data(DISCOVER_BRASIL_URL)
        self.assets_loaded_count += 1
        self._update_loading_progress()
        if self.winfo_exists(): self.update_idletasks()
        
        if not self.winfo_exists(): return

        num_global_to_show = len(self.fetched_global_movies[:10])
        num_brasil_to_show = len(self.fetched_brasil_movies[:5])
        self.total_assets_to_load = 2 + num_global_to_show + num_brasil_to_show
        
        self.all_movies_to_process = self.fetched_global_movies[:10] + self.fetched_brasil_movies[:5]
        self.current_image_processing_index = 0
        
        if self.total_assets_to_load > 2 and self.winfo_exists():
            self.after(10, self._process_next_image)
        elif self.winfo_exists():
            self._finish_loading_and_init_ui()
            
    def _process_next_image(self):
        if not self.winfo_exists(): return

        if self.current_image_processing_index < len(self.all_movies_to_process):
            movie = self.all_movies_to_process[self.current_image_processing_index]
            movie_id = movie.get("id", f"unknown_idx_{self.current_image_processing_index}")
            poster_path = movie.get("poster_path")
            image_url = f"{BASE_IMAGE_URL}{poster_path}" if poster_path else None
            
            print(f"Processando imagem para: {movie.get('title', movie_id)} ({self.current_image_processing_index + 1}/{len(self.all_movies_to_process)})")
            self._prepare_image_versions_for_movie(movie_id, image_url)
            
            self.assets_loaded_count += 1
            self._update_loading_progress()
            if self.winfo_exists(): self.update_idletasks()

            self.current_image_processing_index += 1
            if self.winfo_exists(): self.after(10, self._process_next_image)
        elif self.winfo_exists():
            print("Todas as imagens processadas.")
            self._finish_loading_and_init_ui()

    def _finish_loading_and_init_ui(self):
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy() 
        if self.winfo_exists(): self._init_main_ui()

    def _create_placeholder_ctk_image(self, hex_size):
        placeholder_base = Image.new('RGBA', hex_size, (40, 40, 40, 255))
        placeholder_hex_pil = self._apply_hexagonal_mask_and_border(
            placeholder_base, hex_size, COLOR_YELLOW_DARK, HEXAGON_BORDER_WIDTH - 1
        )
        return ctk.CTkImage(light_image=placeholder_hex_pil, dark_image=placeholder_hex_pil, size=hex_size)

    def _fetch_api_data(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados da API ({url}): {e}")
            return []

    def _create_hexagon_mask(self, size):
        width, height = int(size[0]), int(size[1])
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        points = [
            (width / 2, 0), (width, height / 4), (width, 3 * height / 4),
            (width / 2, height), (0, 3 * height / 4), (0, height / 4)
        ]
        draw.polygon(points, fill=255)
        return mask

    def _apply_hexagonal_mask_and_border(self, pil_image, target_hex_size, border_color, border_width):
        hex_width, hex_height = int(target_hex_size[0]), int(target_hex_size[1])
        original_width, original_height = pil_image.size
        target_aspect_ratio = hex_width / hex_height
        original_aspect_ratio = original_width / original_height

        if original_aspect_ratio > target_aspect_ratio:
            new_height = hex_height
            new_width = int(new_height * original_aspect_ratio)
        else:
            new_width = hex_width
            new_height = int(new_width / original_aspect_ratio)
        
        image_scaled = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - hex_width) / 2
        top = (new_height - hex_height) / 2
        right = (new_width + hex_width) / 2
        bottom = (new_height + hex_height) / 2
        image_cropped = image_scaled.crop((left, top, right, bottom))
        
        if image_cropped.size != (hex_width, hex_height):
            image_cropped = image_cropped.resize((hex_width, hex_height), Image.Resampling.LANCZOS)

        image_rgba = image_cropped.convert("RGBA")
        hexagon_mask = self._create_hexagon_mask((hex_width, hex_height))
        image_rgba.putalpha(hexagon_mask)

        if border_width > 0 and border_color:
            border_draw = ImageDraw.Draw(image_rgba)
            points = [
                (hex_width / 2, 0), (hex_width, hex_height / 4), (hex_width, 3 * hex_height / 4),
                (hex_width / 2, hex_height), (0, 3 * hex_height / 4), (0, hex_height / 4) 
            ]
            border_draw.polygon(points, outline=border_color, width=border_width)
        return image_rgba

    def _prepare_image_versions_for_movie(self, movie_id, image_url):
        if movie_id in self.movie_card_images: return

        pil_original = None
        if image_url:
            if movie_id in self.pil_image_cache:
                pil_original = self.pil_image_cache[movie_id]
            else:
                try:
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    img_data = response.content
                    pil_original = Image.open(BytesIO(img_data))
                    self.pil_image_cache[movie_id] = pil_original
                except Exception as e:
                    print(f"Erro ao baixar imagem ({image_url}): {e}")
        
        if not pil_original: 
            if movie_id in self.pil_image_cache and self.pil_image_cache[movie_id].mode == 'RGBA': 
                 pil_original = self.pil_image_cache[movie_id]
            else:
                pil_original = Image.new('RGBA', (HEXAGON_BASE_WIDTH, HEXAGON_BASE_HEIGHT), (50, 50, 50, 255))
                self.pil_image_cache[movie_id] = pil_original

        hex_normal_pil = self._apply_hexagonal_mask_and_border(pil_original, (HEXAGON_BASE_WIDTH, HEXAGON_BASE_HEIGHT), HEXAGON_BORDER_COLOR, HEXAGON_BORDER_WIDTH)
        ctk_normal = ctk.CTkImage(light_image=hex_normal_pil, dark_image=hex_normal_pil, size=(HEXAGON_BASE_WIDTH, HEXAGON_BASE_HEIGHT))
        hex_hover_pil = self._apply_hexagonal_mask_and_border(pil_original, (HEXAGON_HOVER_WIDTH, HEXAGON_HOVER_HEIGHT), HEXAGON_BORDER_COLOR, HEXAGON_BORDER_WIDTH + 1)
        ctk_hover = ctk.CTkImage(light_image=hex_hover_pil, dark_image=hex_hover_pil, size=(HEXAGON_HOVER_WIDTH, HEXAGON_HOVER_HEIGHT))
        
        self.movie_card_images[movie_id] = {"original": ctk_normal, "hover": ctk_hover}

    def _on_movie_hover(self, event, movie_id, poster_label, card_frame):
        if movie_id in self.movie_card_images:
            poster_label.configure(image=self.movie_card_images[movie_id]["hover"])
            card_frame.lift()

    def _on_movie_leave(self, event, movie_id, poster_label):
        if movie_id in self.movie_card_images:
            poster_label.configure(image=self.movie_card_images[movie_id]["original"])

    def _create_movie_card(self, parent, movie_info, rank):
        movie_id = movie_info.get("id", f"unknown_{rank}_{time.time()}")
        card_frame = ctk.CTkFrame(parent, fg_color="transparent", width=HEXAGON_HOVER_WIDTH, height=HEXAGON_HOVER_HEIGHT)
        card_frame.pack_propagate(False)
        initial_image = self.movie_card_images.get(movie_id, {}).get("original", self.placeholder_image_ctk)
        
        poster_label = ctk.CTkLabel(card_frame, text="", image=initial_image, width=HEXAGON_BASE_WIDTH, height=HEXAGON_BASE_HEIGHT)
        poster_label.place(relx=0.5, rely=0.5, anchor="center")

        poster_label.bind("<Enter>", lambda e, mid=movie_id, pl=poster_label, cf=card_frame: self._on_movie_hover(e, mid, pl, cf))
        poster_label.bind("<Leave>", lambda e, mid=movie_id, pl=poster_label: self._on_movie_leave(e, mid, pl))
        card_frame.bind("<Enter>", lambda e, mid=movie_id, pl=poster_label, cf=card_frame: self._on_movie_hover(e, mid, pl, cf))
        card_frame.bind("<Leave>", lambda e, mid=movie_id, pl=poster_label: self._on_movie_leave(e, mid, pl))

        rank_label_size = 28
        rank_label = ctk.CTkLabel(card_frame, text=str(rank), font=ctk.CTkFont(size=13, weight="bold"), fg_color=COLOR_YELLOW_BASE, text_color=COLOR_YELLOW_BUTTON_TEXT, width=rank_label_size, height=rank_label_size, corner_radius=rank_label_size//2)
        rank_label.place(relx=0.5, rely=0.85, anchor="center")
        return card_frame

    def _display_movie_section(self, parent_frame, section_title_text, movies_data, max_movies):
        if not self.winfo_exists(): return
        section_outer_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        section_outer_frame.pack(pady=20, padx=5, fill="x", expand=True, anchor="n")
        section_outer_frame.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(section_outer_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(0,25))
        section_title = ctk.CTkLabel(title_frame, text=section_title_text, font=ctk.CTkFont(size=30, weight="bold"), text_color=COLOR_WHITE_CREAM)
        section_title.pack()
        
        movies_display_frame = ctk.CTkFrame(section_outer_frame, fg_color="transparent")
        movies_display_frame.grid(row=1, column=0)

        if max_movies == 10: items_per_row_pattern = [3, 4, 3]
        elif max_movies == 5: items_per_row_pattern = [3, 2]
        elif max_movies == 4: items_per_row_pattern = [4]
        else: items_per_row_pattern = [max_movies]

        current_movie_index_in_section = 0
        for row_index, num_items_in_row in enumerate(items_per_row_pattern):
            if not self.winfo_exists() or current_movie_index_in_section >= max_movies: break
            row_frame = ctk.CTkFrame(movies_display_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            should_indent = False
            if len(items_per_row_pattern) > 1:
                if items_per_row_pattern == [3,4,3] and (row_index == 0 or row_index == 2): should_indent = True
                elif items_per_row_pattern == [3,2] and row_index == 1: should_indent = True
            if should_indent:
                indent_width = HEXAGON_HOVER_WIDTH / 2.3
                ctk.CTkFrame(row_frame, width=int(indent_width), fg_color="transparent").pack(side="left", fill="y")
            for _ in range(num_items_in_row):
                if not self.winfo_exists() or current_movie_index_in_section >= max_movies: break
                movie = movies_data[current_movie_index_in_section]
                card_frame = self._create_movie_card(row_frame, movie, current_movie_index_in_section + 1)
                card_frame.pack(side="left", padx=5, pady=3)
                current_movie_index_in_section += 1
    
    def _populate_sections_with_loaded_data(self):
        if not self.winfo_exists(): return

        self.global_section_container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.global_section_container.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        if self.winfo_exists(): self._display_movie_section(self.global_section_container, "Em Alta no Mundo", self.fetched_global_movies, 10)
        
        brazilian_in_global_count = sum(1 for movie in self.fetched_global_movies[:10] if movie.get('original_language') == 'pt')
        info_text = "Nenhum filme brasileiro no top 10 global."
        if brazilian_in_global_count == 1: info_text = "1 filme brasileiro em posições globais."
        elif brazilian_in_global_count > 1: info_text = f"{brazilian_in_global_count} filmes brasileiros em posições globais."
        
        if self.winfo_exists() and self.global_section_container.winfo_exists():
            info_label_container = ctk.CTkFrame(self.global_section_container, fg_color="transparent")
            info_label_container.pack(pady=20)
            ctk.CTkLabel(info_label_container, text=info_text, font=ctk.CTkFont(size=15), text_color=COLOR_WHITE_CREAM, fg_color="transparent").pack()

        if not self.winfo_exists(): return

        self.brasil_section_container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.brasil_section_container.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        if self.winfo_exists(): self._display_movie_section(self.brasil_section_container, "Populares no Brasil", self.fetched_brasil_movies, 5)

if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Standalone Home Page Frame Test")
    root.geometry("1350x950")
    root.configure(fg_color=COLOR_BACKGROUND)
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    test_user = "TestUser"
    def mock_logout_action():
        print(f"Logout action called for {test_user}!")
        root.destroy()

    home_frame_instance = HomePageTestApp(master=root, current_user=test_user, logout_callback=mock_logout_action)
    home_frame_instance.pack(fill="both", expand=True)

    root.mainloop()