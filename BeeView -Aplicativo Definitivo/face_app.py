# face_app.py
import customtkinter as ctk
import json
import os

# Make sure these imports match your directory structure
from contents.modules.login_page import LoginPage
from contents.modules.registration_page import RegistrationPage
from contents.modules.homepage_model import HomePageTestApp # <<< UPDATED IMPORT

class MainApplication(ctk.CTk):
    """
    Classe principal da aplicação. Gerencia a janela e a troca de 'páginas' (frames).
    """
    USER_DATA_FILE = "users_data.json"
    SESSION_FILE = "session.json"

    def __init__(self):
        super().__init__()

        self.title("Meu Aplicativo BeeView")
        self.geometry("1350x950") # Adjusted to typical size for HomePageTestApp

        # Configure the main window grid to allow the content frame to expand
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_user = None
        self.current_frame = None

        self._ensure_user_data_file()
        self._check_active_session()

    def _ensure_user_data_file(self):
        if not os.path.exists(self.USER_DATA_FILE):
            with open(self.USER_DATA_FILE, 'w') as f:
                json.dump({"users": {}}, f, indent=4)

    def _load_user_data(self):
        try:
            with open(self.USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}}

    def _save_user_data(self, data):
        with open(self.USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def _save_session(self, username):
        with open(self.SESSION_FILE, 'w') as f:
            json.dump({"logged_in_user": username}, f, indent=4)

    def _load_session(self):
        if os.path.exists(self.SESSION_FILE):
            try:
                with open(self.SESSION_FILE, 'r') as f:
                    session_data = json.load(f)
                    return session_data.get("logged_in_user")
            except (FileNotFoundError, json.JSONDecodeError):
                return None
        return None

    def _clear_session(self):
        if os.path.exists(self.SESSION_FILE):
            os.remove(self.SESSION_FILE)

    def _check_active_session(self):
        logged_in_user = self._load_session()
        if logged_in_user:
            users_data = self._load_user_data()
            if logged_in_user in users_data.get("users", {}):
                self.current_user = logged_in_user
                print(f"MainApplication: Usuário '{self.current_user}' restaurado da sessão.")
                self._show_main_content_page() # Show HomePageTestApp directly
                return
            else:
                self._clear_session()
        self._show_login_page()

    def _handle_login_attempt(self, username, password, keep_logged_in):
        users_data = self._load_user_data()
        user_credentials = users_data.get("users", {})

        if username in user_credentials and user_credentials[username] == password:
            self.current_user = username
            print(f"MainApplication: Usuário '{username}' logado com sucesso!")

            if keep_logged_in:
                self._save_session(username)
            else:
                self._clear_session()

            if self.current_frame: # Destroy login frame
                self.current_frame.destroy()
                self.current_frame = None
            self._show_main_content_page() # Show HomePageTestApp
            return True, "Login bem-sucedido!"
        else:
            return False, "Usuário ou senha inválidos."

    def _handle_registration_attempt(self, username, password):
        users_data = self._load_user_data()
        users = users_data.get("users", {})

        if not username.strip() or not password.strip():
             return False, "Nome de usuário e senha não podem ser vazios."
        if username in users:
            return False, "Nome de usuário já existe."

        users[username] = password
        self._save_user_data(users_data)
        print(f"MainApplication: Usuário '{username}' registrado com sucesso!")
        return True, "Registro bem-sucedido! Faça o login."

    def _show_login_page(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        
        login_frame = LoginPage(
            master=self,
            on_login_attempt_callback=self._handle_login_attempt,
            on_show_registration_callback=self._show_registration_page
        )
        login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="")
        self.current_frame = login_frame


    def _show_registration_page(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

        registration_frame = RegistrationPage(
            master=self,
            on_register_attempt_callback=self._handle_registration_attempt,
            on_show_login_callback=self._show_login_page
        )
        registration_frame.grid(row=0, column=0, padx=20, pady=20, sticky="")
        self.current_frame = registration_frame

    def _show_main_content_page(self):
        """Cria e exibe a HomePageTestApp após o login."""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        
        self.geometry("1350x950")

        home_page_instance = HomePageTestApp(
            master=self,
            current_user=self.current_user,
            logout_callback=self._logout
        )
        home_page_instance.grid(row=0, column=0, sticky="nsew")
        self.current_frame = home_page_instance

    def _logout(self):
        """Realiza o logout do usuário e volta para a tela de login."""
        print(f"MainApplication: Usuário '{self.current_user}' deslogado.")
        
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
            
        self.current_user = None
        self._clear_session()
        self._show_login_page()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = MainApplication()
    app.mainloop()