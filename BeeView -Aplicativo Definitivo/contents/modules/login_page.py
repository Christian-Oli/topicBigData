import customtkinter as ctk
import math

class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login_attempt_callback, on_show_registration_callback):
        super().__init__(master, fg_color="#000000") # Main background black
        self.master = master
        self.on_login_attempt_callback = on_login_attempt_callback
        self.on_show_registration_callback = on_show_registration_callback

        # Styling constants from the image
        self.PRIMARY_YELLOW = "#F5B82E"
        self.DARK_YELLOW_HOVER = "#EAA620"
        self.TEXT_COLOR_LIGHT = "#FFFFFF"
        self.TEXT_COLOR_MEDIUM = "#DDDDDD"
        self.TEXT_COLOR_DARK_LINK = "#BBBBBB"
        self.INPUT_BG_COLOR = "#2B2B2B" # Dark background for input fields
        self.HEXAGON_OUTLINE_COLOR = "#A0522D" # Sienna/darker yellow-brown for hexagon outlines
        self.HEXAGON_HOVER_FILL_COLOR = self.PRIMARY_YELLOW
        self.HEXAGON_RADIUS = 55 # Base radius for hexagons
        self.SEPARATOR_COLOR = "#666666" # Color for the vertical line

        self.hexagons_data = [] # Stores data for each hexagon [id, vertices, is_hovered]

        # Configure main LoginPage frame grid (will hold the canvas and content_frame)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_hexagon_canvas()
        self._create_content_frame() # This frame will sit on top of the canvas
        self._create_widgets_in_content_frame()

        # Initial drawing of hexagons after a short delay for canvas to get dimensions
        self.master.after(100, self._draw_hexagons_on_resize)
        self.bg_canvas.bind("<Configure>", self._draw_hexagons_on_resize) # Redraw on resize

    def _create_hexagon_canvas(self):
        self.bg_canvas = ctk.CTkCanvas(self, bg="#000000", highlightthickness=0)
        self.bg_canvas.grid(row=0, column=0, sticky="nsew")
        self.bg_canvas.bind("<Motion>", self._on_canvas_mouse_move)
        self.bg_canvas.bind("<Leave>", self._on_canvas_mouse_leave)

    def _create_content_frame(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid for the content_frame (left form, separator, right branding)
        # Weights define proportion, uniform ensures they resize together
        self.content_frame.grid_columnconfigure(0, weight=45, uniform="page_sections") # Left part
        self.content_frame.grid_columnconfigure(1, weight=0)                      # Separator (no weight)
        self.content_frame.grid_columnconfigure(2, weight=55, uniform="page_sections") # Right part
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _calculate_hexagon_vertices(self, center_x, center_y, radius):
        vertices = []
        for i in range(6):
            angle_deg = 60 * i - 30 # Flat top/bottom
            angle_rad = math.pi / 180 * angle_deg
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            vertices.append((x, y))
        return vertices

    def _draw_hexagons_on_resize(self, event=None):
        self.bg_canvas.delete("all_hexagons") # Use a specific tag
        self.hexagons_data = []
        
        width = self.bg_canvas.winfo_width()
        height = self.bg_canvas.winfo_height()

        if width <= 1 or height <= 1: # Canvas not yet realized
            self.master.after(100, self._draw_hexagons_on_resize)
            return

        # Normalized positions (fraction of width/height) and radius scaling
        # (norm_x, norm_y, radius_scale_factor)
        norm_hex_positions = [
            (0.12, 0.25, 1.0), (0.06, 0.75, 0.8), (0.25, 0.55, 1.1), # Left-ish
            (0.92, 0.20, 0.9), (0.80, 0.80, 1.0), (0.65, 0.90, 0.75), # Right-ish
            (0.45, 0.10, 0.8) # Top-mid
        ]

        for norm_x, norm_y, radius_scale in norm_hex_positions:
            center_x = width * norm_x
            center_y = height * norm_y
            radius = self.HEXAGON_RADIUS * radius_scale
            
            vertices = self._calculate_hexagon_vertices(center_x, center_y, radius)
            flat_vertices = [coord for point in vertices for coord in point]
            
            poly_id = self.bg_canvas.create_polygon(
                flat_vertices,
                outline=self.HEXAGON_OUTLINE_COLOR,
                fill="", # No fill initially
                width=2, # Outline width
                tags="all_hexagons" # Tag for easy deletion
            )
            self.hexagons_data.append({"id": poly_id, "vertices": vertices, "is_hovered": False})

    def _is_point_in_polygon(self, x, y, polygon_vertices):
        num_vertices = len(polygon_vertices)
        if num_vertices < 3: return False
        inside = False
        p1x, p1y = polygon_vertices[0]
        for i in range(num_vertices + 1):
            p2x, p2y = polygon_vertices[i % num_vertices]
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def _on_canvas_mouse_move(self, event):
        mouse_x, mouse_y = event.x, event.y
        something_hovered_now = False
        for i, hex_data in enumerate(self.hexagons_data):
            is_inside = self._is_point_in_polygon(mouse_x, mouse_y, hex_data["vertices"])
            if is_inside:
                something_hovered_now = True
                if not hex_data["is_hovered"]:
                    self.bg_canvas.itemconfig(hex_data["id"], fill=self.HEXAGON_HOVER_FILL_COLOR)
                    self.hexagons_data[i]["is_hovered"] = True
            elif hex_data["is_hovered"]: # Was hovered, but mouse is no longer inside THIS polygon
                self.bg_canvas.itemconfig(hex_data["id"], fill="")
                self.hexagons_data[i]["is_hovered"] = False
        
        # This ensures if mouse moves from one hexagon to another directly, the old one unhovers
        if something_hovered_now:
            for i, hex_data in enumerate(self.hexagons_data):
                if not self._is_point_in_polygon(mouse_x, mouse_y, hex_data["vertices"]) and hex_data["is_hovered"]:
                    self.bg_canvas.itemconfig(hex_data["id"], fill="")
                    self.hexagons_data[i]["is_hovered"] = False


    def _on_canvas_mouse_leave(self, event):
        for i, hex_data in enumerate(self.hexagons_data):
            if hex_data["is_hovered"]:
                self.bg_canvas.itemconfig(hex_data["id"], fill="")
                self.hexagons_data[i]["is_hovered"] = False

    def _create_widgets_in_content_frame(self):
        # Padding for the content within the overall window borders
        content_outer_padx = (self.master.winfo_width() * 0.05) # Dynamic padding based on window width
        content_outer_pady = (self.master.winfo_height() * 0.1)

        # Left Frame (for login form)
        left_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(content_outer_padx, 20), pady=content_outer_pady, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1) # Spacer top
        left_frame.grid_rowconfigure(1, weight=0) # Form content
        left_frame.grid_rowconfigure(2, weight=1) # Spacer bottom

        # Frame to hold all form elements for better centering and spacing
        form_elements_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        form_elements_frame.grid(row=1, column=0, sticky="ew")
        form_elements_frame.grid_columnconfigure(0, weight=1)

        # Vertical Separator
        separator = ctk.CTkFrame(self.content_frame, width=1.5, fg_color=self.SEPARATOR_COLOR, corner_radius=0)
        separator.grid(row=0, column=1, sticky="ns", pady=content_outer_pady * 0.8) # Make separator a bit shorter

        # Right Frame (for branding)
        right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=(20, content_outer_padx), pady=content_outer_pady, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1) # Spacer top
        right_frame.grid_rowconfigure(1, weight=0) # Branding content
        right_frame.grid_rowconfigure(2, weight=1) # Spacer bottom
        
        branding_content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        branding_content_frame.grid(row=1, column=0, sticky="ew")
        branding_content_frame.grid_columnconfigure(0, weight=1)


        # --- Populate Left Frame (Login Form) ---
        input_width = 300 # Desired width for entry fields
        input_height = 45
        input_corner_radius = 22
        input_font = ctk.CTkFont(size=14)
        label_font = ctk.CTkFont(size=14)

        email_label = ctk.CTkLabel(form_elements_frame, text="Email:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        email_label.grid(row=0, column=0, padx=10, pady=(0, 3), sticky="ew")

        self.email_entry = ctk.CTkEntry(form_elements_frame, placeholder_text="", width=input_width, height=input_height,
                                           font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                           text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=2)
        self.email_entry.grid(row=1, column=0, padx=10, pady=(0,15), sticky="ew")

        password_label = ctk.CTkLabel(form_elements_frame, text="Senha:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        password_label.grid(row=2, column=0, padx=10, pady=(0, 3), sticky="ew")

        self.password_entry = ctk.CTkEntry(form_elements_frame, placeholder_text="", show="*", width=input_width, height=input_height,
                                            font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                            text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=2)
        self.password_entry.grid(row=3, column=0, padx=10, pady=(0,10), sticky="ew")

        options_frame = ctk.CTkFrame(form_elements_frame, fg_color="transparent")
        options_frame.grid(row=4, column=0, padx=10, pady=(8,8), sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1) 
        options_frame.grid_columnconfigure(1, weight=1) 

        self.keep_logged_in_checkbox = ctk.CTkCheckBox(options_frame, text=" manter conectado",
                                                       font=ctk.CTkFont(size=11), text_color=self.TEXT_COLOR_LIGHT,
                                                       fg_color=self.PRIMARY_YELLOW, hover_color=self.DARK_YELLOW_HOVER,
                                                       checkmark_color="#000000", checkbox_width=18, checkbox_height=18,
                                                       corner_radius=9) # Makes it round
        self.keep_logged_in_checkbox.grid(row=0, column=0, sticky="w")

        forgot_password_button = ctk.CTkButton(options_frame, text="Esqueceu a senha?",
                                             command=self._handle_forgot_password, fg_color="transparent",
                                             text_color=self.TEXT_COLOR_DARK_LINK, hover=False,
                                             font=ctk.CTkFont(size=11), anchor="e")
        forgot_password_button.grid(row=0, column=1, sticky="e")
        def on_enter_forgot(e): forgot_password_button.configure(text_color=self.PRIMARY_YELLOW, font=ctk.CTkFont(size=11, underline=True))
        def on_leave_forgot(e): forgot_password_button.configure(text_color=self.TEXT_COLOR_DARK_LINK, font=ctk.CTkFont(size=11, underline=False))
        forgot_password_button.bind("<Enter>", on_enter_forgot)
        forgot_password_button.bind("<Leave>", on_leave_forgot)

        login_button = ctk.CTkButton(form_elements_frame, text="Entrar", command=self._process_login_submission,
                                     width=input_width, height=input_height, font=ctk.CTkFont(size=15, weight="bold"),
                                     fg_color=self.PRIMARY_YELLOW, text_color="#000000", hover_color=self.DARK_YELLOW_HOVER,
                                     corner_radius=input_corner_radius)
        login_button.grid(row=5, column=0, padx=10, pady=(20, 5), sticky="ew")

        self.error_label = ctk.CTkLabel(form_elements_frame, text="", text_color="#FF5555", font=ctk.CTkFont(size=11), anchor="w", wraplength=input_width-20)
        self.error_label.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")
        self._show_error("") # Initially hide by removing content

        # --- Populate Right Frame (Branding) ---
        logo_font_size = max(40, min(70, int(self.master.winfo_height() / 12))) # Dynamic font size
        
        logo_frame = ctk.CTkFrame(branding_content_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(0,25), sticky="s")

        bee_label = ctk.CTkLabel(logo_frame, text="Bee", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.PRIMARY_YELLOW)
        bee_label.pack(side="left", anchor="s")
        view_label = ctk.CTkLabel(logo_frame, text="View", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.TEXT_COLOR_LIGHT)
        view_label.pack(side="left", anchor="s")

        no_account_label = ctk.CTkLabel(branding_content_frame, text="Não possue conta em nossa aplicação?",
                                        font=ctk.CTkFont(size=14), text_color=self.TEXT_COLOR_MEDIUM,
                                        wraplength=280, justify="center")
        no_account_label.grid(row=1, column=0, padx=20, pady=(10,5), sticky="n")

        register_button_styled = ctk.CTkButton(branding_content_frame, text="Faça sua conta aqui",
                                             command=self._handle_show_registration, fg_color="transparent",
                                             text_color=self.PRIMARY_YELLOW, hover=False,
                                             font=ctk.CTkFont(size=14, weight="bold"))
        register_button_styled.grid(row=2, column=0, padx=20, pady=(0,10), sticky="n")
        def on_enter_reg(e): register_button_styled.configure(font=ctk.CTkFont(size=14, weight="bold", underline=True))
        def on_leave_reg(e): register_button_styled.configure(font=ctk.CTkFont(size=14, weight="bold", underline=False))
        register_button_styled.bind("<Enter>", on_enter_reg)
        register_button_styled.bind("<Leave>", on_leave_reg)

    def _process_login_submission(self):
        username = self.email_entry.get()
        password = self.password_entry.get()
        keep_logged_in = bool(self.keep_logged_in_checkbox.get())

        if not username or not password:
            self._show_error("Email e senha são obrigatórios.")
            return
        success, message = self.on_login_attempt_callback(username, password, keep_logged_in)
        if success:
            self._show_error("") # Clear error on success
            # Main application will handle screen transition
        else:
            self._show_error(message)

    def _handle_show_registration(self):
        if self.on_show_registration_callback:
            self.on_show_registration_callback()

    def _show_error(self, message):
        self.error_label.configure(text=message)
        if message:
            self.error_label.grid()
        else:
            self.error_label.grid_remove() # Hide if no message

    def _handle_forgot_password(self):
        print("Forgot password clicked")
        self._show_error("Funcionalidade 'Esqueci a senha' não implementada.")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    # ctk.set_default_color_theme("blue") # Not essential as we customize heavily

    test_root_window = ctk.CTk()
    test_root_window.title("BeeView Login")
    test_root_window.geometry("960x720") # Adjusted for a good aspect ratio and space
    test_root_window.minsize(800, 600) # Minimum size
    test_root_window.grid_columnconfigure(0, weight=1)
    test_root_window.grid_rowconfigure(0, weight=1)

    def _mock_login_attempt(username, password, keep_logged_in):
        print(f"TESTE: Tentativa de login: {username}, senha: {password}, Manter conectado: {keep_logged_in}")
        if username == "test@example.com" and password == "123":
            print("TESTE: Login mock bem-sucedido!")
            # login_frame_instance._show_error("Login bem-sucedido!") # Test success message display if needed
            return True, "Login bem-sucedido!"
        return False, "Email ou senha inválidos."

    def _mock_show_registration():
        print("TESTE: Mostrar página de registro.")
        # login_frame_instance._show_error("Redirecionando para registro...")

    login_frame_instance = LoginPage(master=test_root_window,
                                     on_login_attempt_callback=_mock_login_attempt,
                                     on_show_registration_callback=_mock_show_registration)
    login_frame_instance.grid(row=0, column=0, sticky="nsew")
    
    test_root_window.mainloop()