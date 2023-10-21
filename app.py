from flask import Flask, request, render_template, redirect, session, flash, make_response
import PyPDF2 
import pyttsx3
import mysql.connector
from flask_session import Session
from datetime import timedelta


#PWA converte o app como pagina de celular


#para q n de erro se por 2 pdf para ler
pdf_processing = False

app = Flask(__name__)
app.secret_key = 'alura'
app.permanent_session_lifetime = timedelta (days=7)
  
app.config['SESSION_TYPE'] = 'filesystem'  
Session(app)

# Configurações do banco de dados
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "multimidia",
}

def check_existing_cadastro(email):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Consulta para verificar se o e-mail ou nome já existem
        sql = "SELECT * FROM cadastro WHERE email = %s"
        val = (email,)

        cursor.execute(sql, val)
        result = cursor.fetchone()

        return result is not None  # Retorna True se já existe um cadastro com o e-mail ou nome

    except mysql.connector.Error as error:
        print("Erro ao verificar cadastro existente:", error)
        return True  # Se houver um erro, considera como existente

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_into_cadastro(nome, email, senha):
    connection = None  # Inicializa a variável connection

    try:
        # Verifica se o cadastro já existe
        if check_existing_cadastro(email,):
            flash("Um Cadastro com esse Email já existe, Tente com outro email !")
            return

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Inserir dados na tabela "cadastro"
        sql = "INSERT INTO cadastro (nome, email, senha) VALUES (%s, %s, %s)"
        val = (nome, email, senha)

        cursor.execute(sql, val)
        connection.commit()
        print("Dados de cadastro inseridos com sucesso!")

    except mysql.connector.Error as error:
        print("Erro ao inserir dados de cadastro no banco de dados:", error)

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



# Função para inserir dados no banco de dados
def insert_into_database(pdf_file_name, text):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Inserir dados na tabela
        sql = "INSERT INTO tb_arquivos (arquivo_nome, arquivo_titulo, arquivo_conteudo, arquivo_tipo) VALUES (%s, %s, %s, %s)"
        val = (pdf_file_name, "Título do PDF", text, "pdf")
        
        cursor.execute(sql, val)
        connection.commit()
        print("Dados inseridos com sucesso!")

    except mysql.connector.Error as error:
        print("Erro ao inserir dados no banco de dados:", error)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect('/interface') # se o cara tiver logado ele vai pra enviar pdf
    return render_template('index.html') # se n, ele fica la mesmo

#adiciona o Cache-Control pra resposta HTTP, faz os navegador não armazenarem o cache da página.
@app.before_request
def before_request():
    if 'logged_in' not in session:
        return

# pra a resposta não ir pro cache mesmo quando você visita a página pela primeira vez
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/interface')
def inter():
    # Verifica se a variável de sessão 'cadastro_success' existe
    if 'cadastro_success' in session:
        # mostra a mensagem se o cadastro foi 
        flash("Cadastro realizado com sucesso, você está logado!", 'success')
        # tira a variavel de sessão e a mensagem não é mostrada denovo
        session.pop('cadastro_success', None)

    # Adicione a condição para exibir a mensagem de upload concluído
    upload_message = "Upload do arquivo concluído e texto extraído e armazenado no banco de dados."
    processing_message = "Um PDF está sendo processado. Aguarde até que a leitura seja concluída."

    return render_template('interface.html', upload_message=upload_message, processing_message=processing_message)

    
# mudei a rota para q se um pdf estiver sendo lido mande a mnsagem para esperar
@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    global pdf_processing

    # Verificar se um PDF está sendo processado
    if pdf_processing:
        flash("Um PDF está sendo processado. Aguarde até que a leitura seja concluída.", 'warning')
        return redirect('/interface')

    pdf_processing = True  # Marcar que um PDF está sendo processado

    try:
        pdf_file = request.files['pdf_file']

        # Verificar se o arquivo é um PDF
        if pdf_file and verificar_se_e_PDF(pdf_file.filename):
            pdf_file.save('upload_pdf.pdf')

            # Processar o arquivo PDF
            pdf_reader = PyPDF2.PdfReader('upload_pdf.pdf')  
            text = ""  # Inicializa a variável de texto para armazenar o texto de todas as páginas

            for page_number in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_number]
                text += page.extract_text()

            # Configurar a voz Maria
            voice_id = 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_PT-BR_MARIA_11.0'
            speak = pyttsx3.init()
            speak.setProperty('voice', voice_id)

            speak.say(text)
            speak.runAndWait()

            # Inserir dados no banco de dados
            insert_into_database(pdf_file.filename, text)

            flash("Upload do arquivo concluído e texto extraído e armazenado no banco de dados.", 'success')
            return render_template('interface.html')# Redireciona para qualquer pagina após o processamento bem-sucedido, so mudar o link ai ( mas n faça isso)

        else:
            flash("Nenhum arquivo PDF foi enviado ou o arquivo não é um PDF válido.", 'error')

    except Exception as e:
        # Trata exceções, se tiver alguma
        flash(f"Erro durante o processamento do PDF: {str(e)}")
        flash("Erro durante o processamento do PDF. Tente novamente.", 'error')

    finally:
        pdf_processing = False

    return redirect('/interface')

# Função para verificar se o arquivo é pdf ( deu um erro uma vez na hora de ler entao coloquei essa função)
def verificar_se_e_PDF(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/cadastro')
def cadastro():
    if 'logged_in' in session and session['logged_in']:
        flash("Cadastro realizado com sucesso, você está logado!.", 'info')
        return redirect('/interface')  # coloca os usuários logados para a interface, no caso, o enviar pdf
    return render_template('cadastro.html') # se n, fica no cadastro


@app.route('/submit_cadastro', methods=['POST'])
def submit_cadastro():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    # Verificar se o cadastro já existe
    if check_existing_cadastro(email):
        flash("Um Cadastro com esse Email já existe, Tente com outro email !", 'error')
        return redirect('/cadastro')

    # Se não existe, inserir dados de login na tabela "login"
    insert_into_cadastro(nome, email, senha)

    # Verificar o login para criar a sessão
    if verify_login(email, senha):
        # Redirecionar para a interface
        return redirect('/interface')
    else:
        # mostrar uma mensagem de erro se algo der errado
        flash("Erro ao criar a sessão. Tente fazer login manualmente.", 'error')
        return redirect('/login')


@app.route('/sobre_nos3')
def sobre():
    return render_template('sobre_nos3.html')


# Função para verificar os dados de login no banco de dados
def verify_login(email, senha):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Consulta para verificar os dados de login
        sql = "SELECT * FROM cadastro WHERE email = %s AND senha = %s"
        val = (email, senha)

        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result:
            # Dados de login válidos, definir a sessão
            session['logged_in'] = True
            session['user_email'] = email  # Adiciona o email do usuário à sessão
            return True
        else:
            # Dados de login inválidos
            return False

    except mysql.connector.Error as error:
        print("Erro ao verificar dados de login:", error)
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
   #tempo da sessão
        session.permanent = True

        # Verificar os dados de login
        if verify_login(email, senha):
            # Redirecionar para a página de interface se os dados forem válidos
            return redirect('/interface')
        else:
            # Exibir uma mensagem de erro se os dados forem inválidos
            flash ("Dados de login inválidos. Tente novamente.")
            return redirect('/')

    # Verificar a sessão antes de ir pro login
    if 'logged_in' in session and session['logged_in']:
        return redirect('/interface')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    # session clear tira a sessão :)
    session.clear()
    
    # ir para a página de login ou pra onde quiser
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

