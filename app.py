from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash, make_response, send_from_directory
import mariadb
import os
from werkzeug.utils import secure_filename
import pandas as pd
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'jpeg', 'jpg', 'png'}

app.secret_key = 'admin'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_unique_file(file, upload_folder):
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    base, ext = os.path.splitext(filename)
    counter = 1

    # Verificar se o arquivo já existe e adicionar um número incremental
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(upload_folder, filename)
        counter += 1

    file.save(filepath)
    return filename  # Retorna apenas o nome do arquivo

# Função para conectar ao banco de dados
def get_db_connection():
    conn = mariadb.connect(
        host="localhost",
        user="tijolos_user",
        password="kimi",  # Substitua pela senha correta
        database="tijolos_cadastro"
    )
    return conn

# Função para criar a tabela de clientes, se não existir
def criar_tabela():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Configura o cursor para retornar dicionários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            telefone VARCHAR(20) NOT NULL,
            email VARCHAR(255) NOT NULL,
            cidade_origem VARCHAR(255) NOT NULL,
            cidade_obra VARCHAR(255) NOT NULL,
            quantidade_tijolos INT NOT NULL,
            valor DECIMAL(10, 2) NOT NULL,  -- Valor calculado
            observacao TEXT,  -- Observações adicionais
            origem_cliente VARCHAR(255),  -- Origem do cliente
            documento VARCHAR(255),  -- Caminho do arquivo anexado
            cpf_cnpj VARCHAR(20)  -- CPF ou CNPJ do cliente
        )
    ''')
    conn.commit()
    conn.close()

# Página inicial
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT id, nome, telefone, email, cidade_origem, cidade_obra, quantidade_tijolos, valor, observacao, origem_cliente, documento, cpf_cnpj
        FROM clientes
    ''')
    clientes = cursor.fetchall()
    conn.close()
    return render_template('index.html', clientes=clientes, pesquisa=None)

# Rota para cadastro de cliente
@app.route('/cadastro', methods=['POST'])
def cadastro():
    nome = request.form['nome']
    telefone = request.form['telefone']
    email = request.form['email']
    cidade_origem = request.form['cidade_origem']
    cidade_obra = request.form['cidade_obra']
    quantidade_tijolos = int(request.form['quantidade_tijolos'])
    valor = quantidade_tijolos * 2  # R$ 2,00 por tijolo
    observacao = request.form['observacao']
    origem_cliente = request.form['origem_cliente']
    cpf_cnpj = request.form['cpf_cnpj']

    documento = None
    if 'documento' in request.files:
        file = request.files['documento']
        if file and allowed_file(file.filename):
            documento = save_unique_file(file, app.config['UPLOAD_FOLDER'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clientes (nome, telefone, email, cidade_origem, cidade_obra, quantidade_tijolos, valor, observacao, origem_cliente, documento, cpf_cnpj)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (nome, telefone, email, cidade_origem, cidade_obra, quantidade_tijolos, valor, observacao, origem_cliente, documento, cpf_cnpj))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

# Rota para editar cliente
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        cidade_origem = request.form['cidade_origem']
        cidade_obra = request.form['cidade_obra']
        quantidade_tijolos = int(request.form['quantidade_tijolos'])
        valor = quantidade_tijolos * 2  # R$ 2,00 por tijolo
        observacao = request.form.get('observacao', '')  # Use `get` para evitar KeyError
        origem_cliente = request.form.get('origem_cliente', '')  # Use `get` para evitar KeyError
        cpf_cnpj = request.form['cpf_cnpj']
        cursor.execute('''
            UPDATE clientes
            SET nome = ?, telefone = ?, email = ?, cidade_origem = ?, cidade_obra = ?, quantidade_tijolos = ?, valor = ?, observacao = ?, origem_cliente = ?, cpf_cnpj = ?
            WHERE id = ?
        ''', (nome, telefone, email, cidade_origem, cidade_obra, quantidade_tijolos, valor, observacao, origem_cliente, cpf_cnpj, id))
        conn.commit()
        conn.close()
        flash("Dados alterados com sucesso!")  # Mensagem de sucesso
        return redirect(url_for('clientes'))
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (id,))
    cliente = cursor.fetchone()
    conn.close()
    return render_template('editar.html', cliente=cliente)

# Rota para excluir cliente
@app.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Rota para upload de documento
@app.route('/upload/<int:id>', methods=['POST'])
def upload(id):
    if 'documento' not in request.files:
        flash("Nenhum arquivo selecionado.")
        return redirect(url_for('index'))
    file = request.files['documento']
    if file.filename == '':
        flash("Nenhum arquivo selecionado.")
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        documento = save_unique_file(file, app.config['UPLOAD_FOLDER'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE clientes SET documento = ? WHERE id = ?', (documento, id))
        conn.commit()
        conn.close()
        flash("Documento anexado com sucesso!")
    return redirect(url_for('index'))

# Rota para filtrar clientes
@app.route('/filtrar', methods=['GET'])
def filtrar():
    termo = request.args.get('termo', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM clientes
        WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ? OR cidade_origem LIKE ? OR cidade_obra LIKE ? OR cpf_cnpj LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%'))
    pesquisa = cursor.fetchall()
    conn.close()
    clientes = []  # Não exibir todos os clientes na pesquisa
    return render_template('index.html', clientes=clientes, pesquisa=pesquisa)

# Rota para exportar clientes para Excel
@app.route('/exportar', methods=['GET'])
def exportar():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT id, nome, telefone, email, cidade_origem, cidade_obra, quantidade_tijolos, valor, observacao, origem_cliente, documento, cpf_cnpj
        FROM clientes
    ''')
    clientes = cursor.fetchall()
    conn.close()

    # Converter os dados para um DataFrame do pandas
    df = pd.DataFrame(clientes, columns=['id', 'nome', 'telefone', 'email', 'cidade_origem', 'cidade_obra', 'quantidade_tijolos', 'valor', 'observacao', 'origem_cliente', 'documento', 'cpf_cnpj'])

    # Salvar a planilha em um arquivo temporário
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cadastros_clientes.xlsx')
    df.to_excel(excel_path, index=False, engine='openpyxl')

    # Retornar o arquivo para download
    flash("Arquivo baixado com sucesso!")
    return send_file(excel_path, as_attachment=True, download_name='cadastros_clientes.xlsx')

# Rota para pesquisa de clientes via API
@app.route('/pesquisa', methods=['GET'])
def pesquisa():
    termo = request.args.get('termo', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM clientes
        WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ? OR cidade_origem LIKE ? OR cidade_obra LIKE ? OR cpf_cnpj LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%'))
    pesquisa = cursor.fetchall()
    conn.close()

    # Converter os resultados para uma lista de dicionários
    resultados = [dict(zip([column[0] for column in cursor.description], row)) for row in pesquisa]
    return jsonify(resultados)

# Rota para exibir clientes
@app.route('/clientes', methods=['GET'])
def clientes():
    termo = request.args.get('termo', '').strip()
    print(f"Termo de pesquisa: {termo}")  # Log para depuração
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if termo:
        query = '''
            SELECT * FROM clientes
            WHERE nome LIKE %s OR email LIKE %s OR cidade_origem LIKE %s OR cidade_obra LIKE %s OR CAST(valor AS CHAR) LIKE %s
        '''
        termo_pesquisa = f"%{termo}%"  # Adiciona os curingas para a busca
        cursor.execute(query, (termo_pesquisa, termo_pesquisa, termo_pesquisa, termo_pesquisa, termo_pesquisa))
        print(f"Consulta executada com termo: {termo_pesquisa}")  # Log para depuração
    else:
        cursor.execute('SELECT * FROM clientes')

    clientes = cursor.fetchall()
    print(f"Clientes encontrados: {clientes}")  # Log para depuração
    conn.close()

    return render_template('clientes.html', clientes=clientes, termo=termo)

# Função para adicionar texto com quebra de linha
def adicionar_texto(pdf, texto, x, y, largura_maxima):
    from reportlab.lib.utils import simpleSplit
    linhas = simpleSplit(texto, "Helvetica", 12, largura_maxima)
    for linha in linhas:
        if y < 50:  # Verifica se o texto ultrapassa o limite inferior da página
            pdf.showPage()  # Cria uma nova página
            pdf.setFont("Helvetica", 12)  # Redefine a fonte na nova página
            y = A4[1] - 50  # Redefine a posição vertical no topo da nova página
        pdf.drawString(x, y, linha)
        y -= 20  # Espaçamento entre linhas
    return y

# Rota para gerar contrato
@app.route('/gerar-contrato/<int:id>', methods=['GET'])
def gerar_contrato(id):
    # Obter o valor antecipado da query string
    valor_antecipado = request.args.get('valor_antecipado', None)

    # Obter os dados do cliente pelo ID
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (id,))
    cliente = cursor.fetchone()
    conn.close()

    # Verificar se o cliente foi encontrado
    if not cliente:
        flash("Cliente não encontrado.")
        return redirect(url_for('clientes'))

    # Criar o PDF em memória
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Configurações de layout
    largura, altura = A4
    margem_esquerda = 50
    margem_superior = altura - 50
    linha_altura = 20  # Espaçamento entre linhas

    # Título do contrato
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margem_esquerda, margem_superior, "CONTRATO DE COMPRA E VENDA DE TIJOLOS ECOLÓGICOS")
    pdf.setFont("Helvetica", 12)

    # Informações do vendedor
    margem_superior -= 40
    margem_superior = adicionar_texto(pdf, "VENDEDOR:", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Razão Social: RUBENS SOARES DE OLIVEIRA", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Nome Fantasia: CRIAR TIJOLOS ECOLÓGICOS", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "CNPJ: 20.545.592/0001-34", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Endereço: Rua Severo Veloso, nº 2327, Bairro Bela Vista, Piumhi - MG, CEP 37925-000", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Telefone: (37) 99812-5237", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "E-mail: rubens.lvr@gmail.com", margem_esquerda, margem_superior, largura - 100)

    # Informações do comprador
    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "COMPRADOR:", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"Nome: {cliente['nome']}", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"CPF/CNPJ: {cliente['cpf_cnpj']}", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"Telefone: {cliente['telefone']}", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"E-mail: {cliente['email']}", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"Cidade de origem: {cliente['cidade_origem']}", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"Cidade da obra: {cliente['cidade_obra']}", margem_esquerda, margem_superior, largura - 100)

    # Cláusulas do contrato
    margem_superior -= 40
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 1 - OBJETO", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "1.1. O presente contrato tem por objeto a compra e venda de tijolos ecológicos com 2 furos,", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "com as seguintes dimensões aproximadas:", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Altura: 7 cm, Largura: 12,5 cm, Comprimento: 25 cm", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"Na quantidade de {cliente['quantidade_tijolos']} unidades.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 2 - PREÇO E CONDIÇÕES DE PAGAMENTO", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"2.1. O valor total da venda será de R$ {cliente['valor']:.2f}, pagos por meio de [PIX / transferência / boleto / dinheiro / outro].", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "2.2. O COMPRADOR declara ciência de que a venda é feita à vista, salvo acordo expresso em contrário.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, f"2.3. Para início da produção dos tijolos, o COMPRADOR se compromete a realizar o pagamento antecipado de R$ {float(valor_antecipado):.2f}, a título de sinal.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 3 - FRETE E ENTREGA", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "3.1. O frete é de inteira responsabilidade do COMPRADOR, incluindo custos, contratação de transportadora, seguro, descarga e logística.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "3.2. O VENDEDOR se compromete a disponibilizar os tijolos para retirada em local combinado, ou entregar em endereço previamente definido, desde que o frete seja providenciado ou custeado pelo COMPRADOR.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "3.3. É responsabilidade do COMPRADOR indicar se a entrega será feita na cidade de origem ou na cidade da obra, devendo essa informação constar no pedido formal.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 4 - RESPONSABILIDADES E GARANTIAS", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "4.1. O VENDEDOR garante que os tijolos entregues correspondem às especificações descritas na Cláusula 1.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "4.2. O VENDEDOR não se responsabiliza por avarias, perdas ou danos após a retirada ou entrega dos produtos ao transportador indicado pelo COMPRADOR.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "4.3. Eventuais reclamações quanto à qualidade ou quantidade deverão ser feitas em até 2 (dois) dias úteis após o recebimento dos tijolos.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "4.4. É de responsabilidade do COMPRADOR garantir o armazenamento adequado dos tijolos em local seco, plano e protegido das intempéries.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 5 - CANCELAMENTO DA COMPRA", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "5.1. Em caso de cancelamento do pedido por parte do COMPRADOR, após o início da produção, o valor antecipado será devolvido em apenas 50% (cinquenta por cento), devido aos custos operacionais, mão de obra e materiais já empenhados.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "5.2. Caso o cancelamento ocorra antes do início da produção, o COMPRADOR poderá negociar a devolução do valor antecipado, descontando-se eventuais custos administrativos.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "5.3. O VENDEDOR se reserva o direito de reter valores proporcionais a prejuízos comprovadamente causados pelo cancelamento.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 6 - CONDIÇÕES GERAIS", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "6.1. O presente contrato é celebrado em caráter irrevogável e irretratável.", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "6.2. Qualquer tolerância de uma das partes quanto ao descumprimento das cláusulas não constituirá renúncia, podendo ser exigido o cumprimento a qualquer momento.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 20
    margem_superior = adicionar_texto(pdf, "CLÁUSULA 7 - FORO", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "7.1. Fica eleito o foro da Comarca de Piumhi - MG para dirimir quaisquer dúvidas ou controvérsias oriundas deste contrato, com renúncia a qualquer outro.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 40
    margem_superior = adicionar_texto(pdf, "Piumhi - MG, ___ de ______________ de 20___.", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 40
    margem_superior = adicionar_texto(pdf, "VENDEDOR:", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Rubens Soares de Oliveira", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Assinatura: ________________________", margem_esquerda, margem_superior, largura - 100)

    margem_superior -= 40
    margem_superior = adicionar_texto(pdf, "COMPRADOR:", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Nome: _____________________________", margem_esquerda, margem_superior, largura - 100)
    margem_superior = adicionar_texto(pdf, "Assinatura: ________________________", margem_esquerda, margem_superior, largura - 100)

    # Finalizar o PDF
    pdf.save()
    buffer.seek(0)

    # Adicionar mensagem de sucesso
    flash("Contrato gerado com sucesso!")

    # Retornar o PDF como resposta
    return send_file(buffer, as_attachment=True, download_name="contrato.pdf", mimetype='application/pdf')

# Rota para download de arquivos
@app.route('/uploads/<path:filename>')
def download_file(filename):
    try:
        print(f"Solicitando arquivo: {filename}")  # Log para depuração
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash("Erro ao baixar anexo: arquivo não encontrado.")
        return redirect(url_for('clientes'))
    except Exception as e:
        flash(f"Erro ao baixar anexo: {str(e)}")
        return redirect(url_for('clientes'))

if __name__ == '__main__':
    criar_tabela()  # Criar a tabela se necessário
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
