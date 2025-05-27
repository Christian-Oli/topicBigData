```bash
# BeeView - Aplicação de Análise Facial e Autenticação

Bem-vindo ao repositório do **BeeView**, uma aplicação desktop que combina um sistema robusto de autenticação de usuários com funcionalidades de análise facial. Desenvolvido em Python utilizando a biblioteca `CustomTkinter` para uma interface gráfica moderna e responsiva.

## Visão Geral do Projeto

O BeeView oferece uma experiência de usuário fluida, começando com telas de login e registro visualmente atraentes. Após a autenticação, os usuários têm acesso a uma aplicação de análise facial que pode carregar dados de um dataset CSV e, potencialmente, utilizar modelos de aprendizado de máquina para processamento de imagens (indicado pela estrutura de módulos).

### Funcionalidades Principais:

* **Autenticação Segura:** Login e registro de usuários com validação de entrada e feedback visual.
* **Design Moderno:** Interface de usuário construída com `CustomTkinter`, apresentando elementos gráficos personalizados como hexágonos de fundo interativos na tela de login.
* **Análise Facial (Módulo Principal):** Um aplicativo independente para processamento e análise de dados faciais, sugerindo o uso de algoritmos de visão computacional.
* **Estrutura Modular:** Código bem organizado em módulos para facilitar a manutenção e escalabilidade.

## Estrutura de Arquivos

A organização do projeto segue uma estrutura lógica para separar componentes da UI, módulos de lógica de negócio, dados e recursos visuais.

BEEVIEW - APLICATIVO DEFINITIVO/
├── contents/
│   ├── dataset/
│   │   └── Dataset_ADD.csv      # Exemplo de dataset para análise.
│   ├── icons/                   # Contém ícones da aplicação.
│   ├── images/                  # Contém outras imagens da aplicação.
│   └── modules/
│       ├── pycache/         # Cache de módulos Python.
│       ├── init.py          # Inicialização do pacote modules.
│       ├── homepage_model.py    # Lógica ou modelo para a página inicial (ainda não implementado na UI).
│       ├── login_page.py        # Implementação da tela de Login.
│       ├── registration_page.py # Implementação da tela de Registro.
│       └── standalone_search_app.py # Aplicação principal de análise facial.
├── face_app.py                  # Orquestra as diferentes telas da aplicação.
└── users_data.json              # Armazenamento (simulado) de dados de usuários.


## Como Executar

Para rodar a aplicação BeeView em sua máquina, siga os passos abaixo:

### Pré-requisitos

Certifique-se de ter o Python instalado (versão 3.x recomendada).

Você precisará instalar as bibliotecas necessárias:

```bash
pip install customtkinter
Passos para Executar
Clone o Repositório (se estiver em um sistema de controle de versão) ou faça o download de todos os arquivos.

Navegue até o Diretório Principal: Abra seu terminal ou prompt de comando e navegue até a pasta BEEVIEW - APLICATIVO DEFINITIVO/.

Bash

cd "BEEVIEW - APLICATIVO DEFINITIVO"
Execute o Aplicativo Principal:

Bash

python face_app.py
Isso iniciará a janela principal do BeeView, apresentando a tela de Login.

Detalhes das Telas
1. Tela de Login (login_page.py)
A tela de login é a porta de entrada para a aplicação, com um design moderno e elementos interativos.

Campos: Email, Senha.
Opções: Checkbox "Manter conectado", link "Esqueceu a senha?".
Ações: Botão "Entrar" para autenticação, link "Faça sua conta aqui" para redirecionar à tela de registro.
Feedback: Exibe mensagens de erro (e sucesso, em testes) para o usuário.
Animação: Possui hexágonos de fundo que interagem visualmente ao passar o mouse.
Mock de Login:
Para testar, você pode usar as seguintes credenciais (conforme o bloco if __name__ == "__main__": em login_page.py):

Email: test@example.com
Senha: 123
2. Tela de Registro (registration_page.py)
A tela de registro permite que novos usuários criem uma conta.

Campos: Email, Senha, Repetir Senha, Data de Nascimento (Dia, Mês, Ano via CTkOptionMenu).
Opções: Checkbox "Aceite os Termos".
Ações: Botão "Registrar" para submeter o registro, link "← Voltar pra tela de login".
Validação: Realiza validações básicas (campos preenchidos, senhas coincidentes, comprimento da senha, termos aceitos, e data de nascimento completa).
Feedback: Exibe mensagens de sucesso ou erro.
Mock de Registro:
Conforme o bloco if __name__ == "__main__": em registration_page.py:

Um email deve terminar com @example.com.
O email registered@example.com já está "registrado" para fins de teste.
3. Aplicação Principal / Análise Facial (standalone_search_app.py)
Este é o módulo central da aplicação após o login. Embora o código completo não tenha sido fornecido para esta parte, a nomenclatura sugere que ela lida com:

Pesquisa: Funcionalidades de busca.
Análise Facial: Interação com um modelo ou dataset (Dataset_ADD.csv) para operações relacionadas a reconhecimento ou análise de faces.
Independência: O nome "standalone" implica que pode ser executado separadamente para testes ou uso específico, mas é parte integrante do fluxo principal do face_app.py.
Desenvolvimento
Bibliotecas Utilizadas
customtkinter: Para a construção da interface gráfica do usuário.
datetime: Para manipulação de datas (usado na tela de registro).
Notas para Desenvolvedores
Callbacks: As telas de Login e Registro utilizam callbacks para comunicar eventos (tentativas de login/registro, troca de tela) de volta ao face_app.py, garantindo uma arquitetura limpa.
Estilo: Constantes de estilo (PRIMARY_YELLOW, TEXT_COLOR_LIGHT, etc.) são definidas em cada classe de página para manter a consistência visual.
Responsividade: O uso de grid_columnconfigure e grid_rowconfigure com weight e uniform ajuda na responsividade da interface.
Armazenamento de Usuários: Atualmente, users_data.json parece ser usado para um armazenamento muito básico (ou simulado) de usuários. Para uma aplicação real, considere um banco de dados adequado.
