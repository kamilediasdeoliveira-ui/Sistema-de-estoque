import sqlite3
import random
import os
import matplotlib
matplotlib.use('TkAgg') # Define o backend do Matplotlib para o Tkinter
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

db_path = "mercado.db"
LIMITE_ESTOQUE_BAIXO = 100

def criar_banco():
    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE produtos (
                codigo TEXT PRIMARY KEY,
                produto TEXT NOT NULL,
                categoria TEXT NOT NULL,
                unidade TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                valor_unitario REAL NOT NULL,
                valor_total REAL NOT NULL,
                fornecedor TEXT NOT NULL,
                dia INTEGER NOT NULL 
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE historico_saidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_produto TEXT NOT NULL,
                quantidade_saida INTEGER NOT NULL,
                data_saida TIMESTAMP NOT NULL,
                FOREIGN KEY (codigo_produto) REFERENCES produtos (codigo)
            )
            ''')

            categorias = {
                "Alimentos": ["Arroz", "Feijão", "Macarrão", "Carne Bovina", "Frango", "Leite", "Pão", "Queijo", "Fruta", "Verdura"],
                "Bebidas": ["Água", "Refrigerante", "Suco", "Cerveja", "Vinho", "Energético", "Leite Fermentado", "Chá", "Café", "Achocolatado"],
                "Higiene": ["Sabonete", "Shampoo", "Condicionador", "Pasta de Dente", "Escova de Dente", "Desodorante", "Papel Higiênico", "Creme Hidratalim", "Cotonete", "Fio Dental"],
                "Limpeza": ["Detergente", "Sabão em Pó", "Amaciante", "Desinfetante", "Água Sanitária", "Lustra Móveis", "Esponja", "Saco de Lixo", "Pano de Chão", "Limpa Vidros"]
            }

            unidades = ["un", "kg", "g", "l", "ml"]
            fornecedores = [
                "SuperMix Distribuidora", "Comercial Silva LTDA", "Empório Bom Sabor", "Brasil Food Supply",
                "Grupo Monte Verde", "Distribuidora União", "Central das Bebidas", "Higiclean Importadora",
                "Limpex Brasil", "Delícia Alimentos", "NutriMais Comércio", "Bela Vista Atacadista",
                "EcoHigiene", "Top Frutas Distribuidora", "PuraVida Produtos Naturais", "Rio Minas Alimentos",
                "Nordeste Food Service", "Casa do Café", "LimpMais Produtos de Limpeza", "Max Suprimentos"
            ]

            codigo = 1
            total_itens = 800
            itens_baixo_estoque = 20
            
            def inserir_produto(qtd_min, qtd_max):
                nonlocal codigo
                categoria = random.choice(list(categorias.keys()))
                produto_base = random.choice(categorias[categoria])
                unidade = random.choice(unidades)
                quantidade = random.randint(qtd_min, qtd_max)
                valor_unitario = round(random.uniform(1.0, 50.0), 2)
                valor_total = round(valor_unitario * quantidade, 2)
                fornecedor = random.choice(fornecedores)
                dia = random.randint(1, 7)

                codigo_produto = f"P{codigo:04d}"
                codigo += 1

                cursor.execute('''
                    INSERT INTO produtos (codigo, produto, categoria, unidade, quantidade, valor_unitario, valor_total, fornecedor, dia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo_produto, produto_base, categoria, unidade, quantidade, valor_unitario, valor_total, fornecedor, dia))

            for _ in range(total_itens - itens_baixo_estoque):
                inserir_produto(100, 500)
            
            for _ in range(itens_baixo_estoque):
                inserir_produto(1, 99)

            conn.commit()
    else:
        pass

def obter_proximo_codigo(cursor):
    cursor.execute("SELECT MAX(codigo) FROM produtos WHERE codigo LIKE 'P____'")
    max_codigo = cursor.fetchone()[0]
    if max_codigo:
        try:
            ultimo_numero = int(max_codigo[1:])
            proximo_numero = ultimo_numero + 1
        except ValueError:
            proximo_numero = 1
    else:
        proximo_numero = 1
    return f"P{proximo_numero:04d}"

def obter_metricas_dashboard(cursor):
    cursor.execute(f"SELECT COUNT(*) FROM produtos WHERE quantidade < ?", (LIMITE_ESTOQUE_BAIXO,))
    estoque_baixo = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(quantidade) FROM produtos")
    qtd_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(valor_total) FROM produtos")
    custo_total = cursor.fetchone()[0]
    
    return {
        "baixo": estoque_baixo if estoque_baixo else 0,
        "total_itens": qtd_total if qtd_total else 0,
        "custo_total": custo_total if custo_total else 0.0
    }

def obter_produtos_estoque_baixo(cursor):
    query = f"SELECT codigo, produto, quantidade FROM produtos WHERE quantidade < ? ORDER BY quantidade ASC"
    cursor.execute(query, (LIMITE_ESTOQUE_BAIXO,))
    return cursor.fetchall()

def main():
    criar_banco()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    app = tk.Tk()
    app.title("Controle de Estoque do Mercado")
    app.geometry("1100x700")
    
    cor_sidebar = "#2c3e50"
    cor_fundo = "#ecf0f1"
    cor_letra = "#ffffff"
    cor_card = "#ffffff"

    app.configure(bg=cor_fundo)

    frame_menu = tk.Frame(app, width=250, bg=cor_sidebar)
    frame_menu.pack(side="left", fill="y")
    frame_menu.pack_propagate(False)

    frame_conteudo = ttk.Frame(app, padding=20)
    frame_conteudo.pack(side="right", fill="both", expand=True)

    tk.Label(
        frame_menu, 
        text="PÁGINA PRINCIPAL", 
        font=("Arial", 16, "bold"),
        bg=cor_sidebar, 
        fg=cor_letra
    ).pack(pady=(20, 10))

    tk.Frame(frame_menu, height=1, bg=cor_letra, width=200).pack(pady=(0, 10))

    global_tree = None
    global_tree_alertas = None
    global_entry_busca_nome = None
    global_combo_busca_categoria = None
    
    global_sort_col = "produto"
    global_sort_dir = "ASC"

    def limpar_frame_conteudo():
        for widget in frame_conteudo.winfo_children():
            widget.destroy()

    def _criar_janela_grafico(figura, titulo):
        janela_grafico = tk.Toplevel(app)
        janela_grafico.title(titulo)
        janela_grafico.geometry("800x600")
        janela_grafico.transient(app)
        janela_grafico.grab_set()

        canvas = FigureCanvasTkAgg(figura, master=janela_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, janela_grafico)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def acao_dashboard():
        nonlocal global_tree_alertas
        limpar_frame_conteudo()
        
        ttk.Label(frame_conteudo, text="Dashboard", font=("Arial", 24, "bold")).pack(anchor="w")

        frame_metricas = tk.Frame(frame_conteudo, bg=cor_fundo)
        frame_metricas.pack(fill="x", pady=20)

        metricas = obter_metricas_dashboard(cursor)
        
        card1 = tk.Frame(frame_metricas, bg=cor_card, relief="solid", bd=1, width=200, height=100)
        card1.pack(side="left", padx=10, fill="x", expand=True)
        card1.pack_propagate(False)
        tk.Label(card1, text=f"ESTOQUE BAIXO ( < {LIMITE_ESTOQUE_BAIXO} )", font=("Arial", 9), bg=cor_card).pack(pady=(10,0))
        tk.Label(card1, text=f"{metricas['baixo']}", font=("Arial", 24, "bold"), bg=cor_card).pack(pady=10)

        card2 = tk.Frame(frame_metricas, bg=cor_card, relief="solid", bd=1, width=200, height=100)
        card2.pack(side="left", padx=10, fill="x", expand=True)
        card2.pack_propagate(False)
        tk.Label(card2, text="QUANTIDADE TOTAL DE ITENS", font=("Arial", 9), bg=cor_card).pack(pady=(10,0))
        tk.Label(card2, text=f"{metricas['total_itens']}", font=("Arial", 24, "bold"), bg=cor_card).pack(pady=10)

        card3 = tk.Frame(frame_metricas, bg=cor_card, relief="solid", bd=1, width=200, height=100)
        card3.pack(side="left", padx=10, fill="x", expand=True)
        card3.pack_propagate(False)
        tk.Label(card3, text="CUSTO TOTAL DO ESTOQUE", font=("Arial", 9), bg=cor_card).pack(pady=(10,0))
        tk.Label(card3, text=f"R$ {metricas['custo_total']:,.2f}", font=("Arial", 24, "bold"), bg=cor_card).pack(pady=10)
        
        ttk.Label(frame_conteudo, text="Atalhos", font=("Arial", 20, "bold")).pack(anchor="w", pady=(20, 10))
        
        frame_atalhos = tk.Frame(frame_conteudo, bg=cor_fundo)
        frame_atalhos.pack(fill="x")

        atalho1 = tk.Button(frame_atalhos, text="Produtos\n(Listar Todos)", font=("Arial", 12), command=acao_listar_todos, width=20, height=5, bg=cor_card, relief="solid", bd=1)
        atalho1.pack(side="left", padx=10)

        atalho2 = tk.Button(frame_atalhos, text="Compras\n(Registrar Entrada)", font=("Arial", 12), command=acao_comprar_estoque, width=20, height=5, bg=cor_card, relief="solid", bd=1)
        atalho2.pack(side="left", padx=10)
        
        atalho3 = tk.Button(frame_atalhos, text="Vendas\n(Registrar Saída)", font=("Arial", 12), command=acao_vender_estoque, width=20, height=5, bg=cor_card, relief="solid", bd=1)
        atalho3.pack(side="left", padx=10)

        ttk.Label(frame_conteudo, text="Alertas de Estoque Baixo", font=("Arial", 20, "bold")).pack(anchor="w", pady=(30, 10))
        
        frame_alertas_container = ttk.Frame(frame_conteudo)
        frame_alertas_container.pack(fill="x")
        
        frame_alertas_tabela = ttk.Frame(frame_alertas_container)
        frame_alertas_tabela.pack(fill="x", expand=True)
        
        cols_alertas = ('codigo', 'produto', 'quantidade')
        global_tree_alertas = ttk.Treeview(frame_alertas_tabela, columns=cols_alertas, show='headings', height=6)
        
        global_tree_alertas.column('codigo', width=100, anchor='center')
        global_tree_alertas.column('produto', width=300, anchor='w')
        global_tree_alertas.column('quantidade', width=100, anchor='e')
        
        global_tree_alertas.heading('codigo', text='Código')
        global_tree_alertas.heading('produto', text='Produto')
        global_tree_alertas.heading('quantidade', text='Qtd. Atual')

        sb_alertas = ttk.Scrollbar(frame_alertas_tabela, orient="vertical", command=global_tree_alertas.yview)
        global_tree_alertas.configure(yscrollcommand=sb_alertas.set)

        sb_alertas.pack(side="right", fill="y")
        global_tree_alertas.pack(side="left", fill="x", expand=True)

        try:
            produtos_baixos = obter_produtos_estoque_baixo(cursor)
            if not produtos_baixos:
                global_tree_alertas.insert('', 'end', values=("", "Nenhum produto com estoque baixo!", ""))
            else:
                for row in produtos_baixos:
                    global_tree_alertas.insert('', 'end', values=list(row))
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível buscar os alertas: {e}")

        ttk.Button(frame_alertas_container, text="Comprar Item Selecionado", command=acao_comprar_alerta).pack(anchor="e", pady=(10,0))


    def atualizar_tabela_produtos(filtro_nome="", filtro_categoria="Todas", ordenar_por="produto", ordem="ASC"):
        nonlocal global_tree
        if global_tree is None:
            return
            
        for item in global_tree.get_children():
            global_tree.delete(item)

        try:
            query = "SELECT codigo, produto, categoria, unidade, quantidade, valor_unitario, valor_total, fornecedor FROM produtos WHERE 1=1"
            params = []

            if filtro_nome:
                query += " AND produto LIKE ?"
                params.append(f"%{filtro_nome}%")
            
            if filtro_categoria != "Todas":
                query += " AND categoria = ?"
                params.append(filtro_categoria)

            query += f" ORDER BY {ordenar_por} {ordem}"

            cursor.execute(query, params)
            for row in cursor.fetchall():
                global_tree.insert('', 'end', values=list(row))
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível buscar os produtos: {e}")

    def executar_busca():
        nonlocal global_entry_busca_nome, global_combo_busca_categoria, global_sort_col, global_sort_dir
        filtro_nome = global_entry_busca_nome.get() if global_entry_busca_nome else ""
        filtro_categoria = global_combo_busca_categoria.get() if global_combo_busca_categoria else "Todas"
        
        atualizar_tabela_produtos(filtro_nome, filtro_categoria, global_sort_col, global_sort_dir)

    def on_sort_column_click(coluna_clicada):
        nonlocal global_sort_col, global_sort_dir
        
        if global_sort_col == coluna_clicada:
            global_sort_dir = "DESC" if global_sort_dir == "ASC" else "ASC"
        else:
            global_sort_col = coluna_clicada
            global_sort_dir = "ASC"
            
        executar_busca()

    def acao_listar_todos():
        nonlocal global_tree, global_entry_busca_nome, global_combo_busca_categoria, global_sort_col, global_sort_dir
        limpar_frame_conteudo()
        
        frame_busca_filtro = ttk.Frame(frame_conteudo)
        frame_busca_filtro.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_busca_filtro, text="Buscar por Nome:").pack(side="left", padx=(0, 5))
        global_entry_busca_nome = ttk.Entry(frame_busca_filtro, width=30)
        global_entry_busca_nome.pack(side="left", padx=5)

        ttk.Label(frame_busca_filtro, text="Categoria:").pack(side="left", padx=(10, 5))
        categorias_filtro = ["Todas", "Alimentos", "Bebidas", "Higiene", "Limpeza"]
        global_combo_busca_categoria = ttk.Combobox(frame_busca_filtro, values=categorias_filtro, width=15)
        global_combo_busca_categoria.set("Todas")
        global_combo_busca_categoria.pack(side="left", padx=5)

        ttk.Button(frame_busca_filtro, text="Buscar / Filtrar", command=executar_busca).pack(side="left", padx=10)

        frame_tabela = ttk.Frame(frame_conteudo)
        frame_tabela.pack(fill="both", expand=True)

        cols = ('codigo', 'produto', 'categoria', 'unidade', 'quantidade', 'valor_unitario', 'valor_total', 'fornecedor')
        global_tree = ttk.Treeview(frame_tabela, columns=cols, show='headings', height=500)
        
        col_map = {
            'codigo': ('Código', 80, 'center'),
            'produto': ('Produto', 200, 'w'),
            'categoria': ('Categoria', 120, 'w'),
            'unidade': ('Un.', 60, 'center'),
            'quantidade': ('Qtd.', 60, 'e'),
            'valor_unitario': ('Val. Unit.', 100, 'e'),
            'valor_total': ('Val. Total', 100, 'e'),
            'fornecedor': ('Fornecedor', 150, 'w')
        }

        for col_id, (texto, largura, anchor) in col_map.items():
            global_tree.column(col_id, width=largura, anchor=anchor, stretch=True)
            global_tree.heading(col_id, text=texto, anchor=anchor, command=lambda c=col_id: on_sort_column_click(c))

        sb = ttk.Scrollbar(frame_tabela, orient="vertical", command=global_tree.yview)
        global_tree.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        global_tree.pack(side="left", fill="both", expand=True)

        global_sort_col = "produto"
        global_sort_dir = "ASC"
        executar_busca()

    def acao_cadastrar():
        janela_cadastro = tk.Toplevel(app)
        janela_cadastro.title("Cadastrar Novo Produto")
        janela_cadastro.geometry("400x450")
        janela_cadastro.transient(app)
        janela_cadastro.grab_set()
        janela_cadastro.configure(bg=cor_fundo)
        
        frame_form = ttk.Frame(janela_cadastro, padding=20)
        frame_form.pack(fill="both", expand=True)

        entradas = {}
        
        ttk.Label(frame_form, text="Nome do Produto:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
        entradas['produto'] = ttk.Entry(frame_form, width=40, font=("Arial", 12))
        entradas['produto'].grid(row=1, column=0, columnspan=2, sticky="w")

        ttk.Label(frame_form, text="Categoria:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        entradas['categoria'] = ttk.Combobox(frame_form, width=38, font=("Arial", 12),
                                             values=["Alimentos", "Bebidas", "Higiene", "Limpeza"])
        entradas['categoria'].grid(row=3, column=0, columnspan=2, sticky="w")
        
        ttk.Label(frame_form, text="Unidade:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=5)
        entradas['unidade'] = ttk.Combobox(frame_form, width=15, font=("Arial", 12),
                                           values=["un", "kg", "g", "l", "ml"])
        entradas['unidade'].grid(row=5, column=0, sticky="w")

        ttk.Label(frame_form, text="Quantidade:", font=("Arial", 12)).grid(row=4, column=1, sticky="w", pady=5)
        entradas['quantidade'] = ttk.Entry(frame_form, width=16, font=("Arial", 12))
        entradas['quantidade'].grid(row=5, column=1, sticky="e")

        ttk.Label(frame_form, text="Valor Unitário (R$):", font=("Arial", 12)).grid(row=6, column=0, sticky="w", pady=5)
        entradas['valor_unitario'] = ttk.Entry(frame_form, width=15, font=("Arial", 12))
        entradas['valor_unitario'].grid(row=7, column=0, sticky="w")
        
        ttk.Label(frame_form, text="Fornecedor:", font=("Arial", 12)).grid(row=8, column=0, sticky="w", pady=5)
        entradas['fornecedor'] = ttk.Entry(frame_form, width=40, font=("Arial", 12))
        entradas['fornecedor'].grid(row=9, column=0, columnspan=2, sticky="w")

        def salvar_produto():
            try:
                produto = entradas['produto'].get()
                categoria = entradas['categoria'].get()
                unidade = entradas['unidade'].get()
                fornecedor = entradas['fornecedor'].get()
                
                if not all([produto, categoria, unidade, fornecedor]):
                    messagebox.showerror("Erro de Validação", "Todos os campos de texto devem ser preenchidos.", parent=janela_cadastro)
                    return

                quantidade = int(entradas['quantidade'].get())
                valor_unitario = float(entradas['valor_unitario'].get().replace(',', '.'))
                
                if quantidade <= 0 or valor_unitario <= 0:
                     messagebox.showerror("Erro de Validação", "Quantidade e Valor devem ser maiores que zero.", parent=janela_cadastro)
                     return

                codigo_produto = obter_proximo_codigo(cursor)
                valor_total = round(quantidade * valor_unitario, 2)
                dia_hoje = datetime.now().day

                cursor.execute("""
                    INSERT INTO produtos (codigo, produto, categoria, unidade, quantidade, valor_unitario, valor_total, fornecedor, dia)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (codigo_produto, produto, categoria, unidade, quantidade, valor_unitario, valor_total, fornecedor, dia_hoje))
                conn.commit()
                
                messagebox.showinfo("Sucesso", f"Produto {produto} (Código: {codigo_produto}) cadastrado!", parent=janela_cadastro)
                janela_cadastro.destroy()
                
                if global_tree:
                    executar_busca()
                else:
                    acao_listar_todos()

            except ValueError:
                messagebox.showerror("Erro de Validação", "Quantidade deve ser um número inteiro.\nValor Unitário deve ser um número (ex: 10.99).", parent=janela_cadastro)
            except Exception as e:
                messagebox.showerror("Erro no Banco de Dados", f"Não foi possível salvar: {e}", parent=janela_cadastro)

        btn_salvar = ttk.Button(frame_form, text="Salvar Produto", command=salvar_produto)
        btn_salvar.grid(row=10, column=0, columnspan=2, sticky="e", pady=20)


    def acao_buscar():
        acao_listar_todos()

    def _abrir_popup_quantidade(titulo, label_texto, callback_sql, item_selecionado, callback_refresh):
        try:
            codigo, nome, qtd_atual = item_selecionado

            janela_popup = tk.Toplevel(app)
            janela_popup.title(titulo)
            janela_popup.geometry("350x200")
            janela_popup.transient(app)
            janela_popup.grab_set()
            janela_popup.configure(bg=cor_fundo)
            
            frame_popup = ttk.Frame(janela_popup, padding=20)
            frame_popup.pack(fill="both", expand=True)

            ttk.Label(frame_popup, text=f"Produto: {nome} (Atual: {qtd_atual})", font=("Arial", 12, "bold")).pack(pady=5)
            
            ttk.Label(frame_popup, text=f"Quantidade a {label_texto}:", font=("Arial", 12)).pack(pady=5)
            entry_qtd = ttk.Entry(frame_popup, width=15, font=("Arial", 12))
            entry_qtd.pack(pady=5)
            entry_qtd.focus()

            def salvar_alteracao():
                try:
                    qtd_movimentar = int(entry_qtd.get())
                    if qtd_movimentar <= 0:
                        messagebox.showerror("Erro", "A quantidade deve ser maior que zero.", parent=janela_popup)
                        return
                    
                    callback_sql(codigo, qtd_movimentar, qtd_atual)
                    
                    janela_popup.destroy()
                    if callback_refresh:
                        callback_refresh()
                    
                except ValueError:
                    messagebox.showerror("Erro", "Por favor, digite um número válido.", parent=janela_popup)
                except Exception as e:
                    if "Estoque insuficiente" not in str(e):
                        messagebox.showerror("Erro no Banco de Dados", f"Não foi possível atualizar: {e}", parent=janela_popup)

            btn_salvar = ttk.Button(frame_popup, text="Confirmar", command=salvar_alteracao)
            btn_salvar.pack(pady=20)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao abrir a janela: {e}")

    def acao_comprar_estoque():
        nonlocal global_tree
        if not global_tree:
            messagebox.showwarning("Aviso", "Por favor, vá para a tela 'Listar/Buscar Produtos' para selecionar um item.")
            return

        selected_item_id = global_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Aviso", "Por favor, selecione um produto na tabela primeiro.")
            return
        
        item_data = global_tree.item(selected_item_id)
        codigo = item_data['values'][0]
        nome = item_data['values'][1]
        qtd_atual = item_data['values'][4]
        item_selecionado = (codigo, nome, qtd_atual)
        
        def _salvar_compra(codigo, qtd_adicionar, qtd_antiga):
            cursor.execute("SELECT valor_unitario FROM produtos WHERE codigo = ?", (codigo,))
            valor_unitario = cursor.fetchone()[0]
            
            nova_quantidade = qtd_antiga + qtd_adicionar
            novo_valor_total = round(nova_quantidade * valor_unitario, 2)
            
            cursor.execute("UPDATE produtos SET quantidade = ?, valor_total = ? WHERE codigo = ?", 
                           (nova_quantidade, novo_valor_total, codigo))
            conn.commit()
            messagebox.showinfo("Sucesso", f"{qtd_adicionar} unidades compradas e adicionadas ao produto {codigo}.")

        _abrir_popup_quantidade("Comprar (Entrada)", "COMPRAR", _salvar_compra, item_selecionado, executar_busca)
        
    def acao_vender_estoque():
        nonlocal global_tree
        if not global_tree:
            messagebox.showwarning("Aviso", "Por favor, vá para a tela 'Listar/Buscar Produtos' para selecionar um item.")
            return

        selected_item_id = global_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Aviso", "Por favor, selecione um produto na tabela primeiro.")
            return
        
        item_data = global_tree.item(selected_item_id)
        codigo = item_data['values'][0]
        nome = item_data['values'][1]
        qtd_atual = item_data['values'][4]
        item_selecionado = (codigo, nome, qtd_atual)
        
        def _salvar_venda(codigo, qtd_vender, qtd_antiga):
            if qtd_vender > qtd_antiga:
                messagebox.showerror("Erro", f"Estoque insuficiente. Você só tem {qtd_antiga} unidades para vender.")
                raise Exception("Estoque insuficiente") 

            cursor.execute("SELECT valor_unitario FROM produtos WHERE codigo = ?", (codigo,))
            valor_unitario = cursor.fetchone()[0]
            
            nova_quantidade = qtd_antiga - qtd_vender
            novo_valor_total = round(nova_quantidade * valor_unitario, 2)
            
            cursor.execute("UPDATE produtos SET quantidade = ?, valor_total = ? WHERE codigo = ?", 
                           (nova_quantidade, novo_valor_total, codigo))
            
            cursor.execute("INSERT INTO historico_saidas (codigo_produto, quantidade_saida, data_saida) VALUES (?, ?, ?)",
                           (codigo, qtd_vender, datetime.now()))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"{qtd_vender} unidades vendidas e baixadas do produto {codigo}.")

        _abrir_popup_quantidade("Vender (Saída)", "VENDER", _salvar_venda, item_selecionado, executar_busca)

    def acao_comprar_alerta():
        nonlocal global_tree_alertas
        if not global_tree_alertas:
            messagebox.showwarning("Aviso", "Tabela de alertas não encontrada.")
            return

        selected_item_id = global_tree_alertas.focus()
        if not selected_item_id:
            messagebox.showwarning("Aviso", "Por favor, selecione um produto na lista de alertas.")
            return
        
        item_data = global_tree_alertas.item(selected_item_id)
        codigo = item_data['values'][0]
        nome = item_data['values'][1]
        qtd_atual = item_data['values'][2]
        item_selecionado = (codigo, nome, qtd_atual)
        
        def _salvar_compra(codigo, qtd_adicionar, qtd_antiga):
            cursor.execute("SELECT valor_unitario FROM produtos WHERE codigo = ?", (codigo,))
            valor_unitario = cursor.fetchone()[0]
            
            nova_quantidade = qtd_antiga + qtd_adicionar
            novo_valor_total = round(nova_quantidade * valor_unitario, 2)
            
            cursor.execute("UPDATE produtos SET quantidade = ?, valor_total = ? WHERE codigo = ?", 
                           (nova_quantidade, novo_valor_total, codigo))
            conn.commit()
            messagebox.showinfo("Sucesso", f"{qtd_adicionar} unidades compradas e adicionadas ao produto {codigo}.")

        _abrir_popup_quantidade("Comprar (Entrada)", "COMPRAR", _salvar_compra, item_selecionado, acao_dashboard)

    def acao_excluir():
        nonlocal global_tree
        if not global_tree:
            messagebox.showwarning("Aviso", "Vá para a tela 'Listar/Buscar Produtos' para selecionar um item.")
            return

        selected_item_id = global_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Aviso", "Por favor, selecione um produto na tabela para excluir.")
            return
            
        try:
            item_data = global_tree.item(selected_item_id)
            codigo = item_data['values'][0]
            nome = item_data['values'][1]

            if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o produto?\n\nCÓDIGO: {codigo}\nPRODUTO: {nome}"):
                return
                
            cursor.execute("DELETE FROM produtos WHERE codigo = ?", (codigo,))
            conn.commit()
            
            global_tree.delete(selected_item_id)
            messagebox.showinfo("Sucesso", f"Produto '{nome}' foi excluído.")

        except Exception as e:
            messagebox.showerror("Erro no Banco de Dados", f"Não foi possível excluir: {e}")


    def acao_grafico_evolucao():
        try:
            cursor.execute("SELECT dia, SUM(quantidade) FROM produtos GROUP BY dia ORDER BY dia")
            dados = cursor.fetchall()
            if not dados:
                messagebox.showinfo("Sem Dados", "Sem dados para mostrar evolução do estoque.")
                return
            
            dias, quantidades = zip(*dados)
            
            fig = Figure(figsize=(8, 5), dpi=100)
            plot = fig.add_subplot(111)
            plot.plot(dias, quantidades, marker='o', color='b')
            plot.set_title('Evolução do Estoque Total (por Dia simulado)')
            plot.set_xlabel('Dia')
            plot.set_ylabel('Quantidade Total em Estoque')
            plot.grid(True)
            
            _criar_janela_grafico(fig, "Gráfico: Evolução do Estoque")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o gráfico: {e}")

    def acao_grafico_categorias():
        try:
            cursor.execute("SELECT categoria, SUM(valor_total) FROM produtos GROUP BY categoria")
            dados = cursor.fetchall()
            if not dados:
                messagebox.showinfo("Sem Dados", "Sem dados para comparar categorias.")
                return
            
            categorias, valores = zip(*dados)
            
            fig = Figure(figsize=(9, 6), dpi=100)
            plot = fig.add_subplot(111)
            plot.bar(categorias, valores, color='skyblue')
            plot.set_title('Valor Total do Estoque por Categoria')
            plot.set_xlabel('Categorias')
            plot.set_ylabel('Valor Total (R$)')
            plot.set_xticklabels(categorias, rotation=45, ha='right')
            fig.tight_layout()
            
            _criar_janela_grafico(fig, "Gráfico: Valor por Categoria")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o gráfico: {e}")

    def acao_grafico_abc():
        try:
            cursor.execute("SELECT produto, valor_total FROM produtos ORDER BY valor_total DESC")
            dados = cursor.fetchall()
            if not dados:
                messagebox.showinfo("Sem Dados", "Sem dados para gerar curva ABC.")
                return

            produtos, valores = zip(*dados)
            total_geral = sum(valores)
            cumvals = []
            cumul = 0
            for val in valores:
                cumul += val
                cumvals.append(cumul / total_geral * 100)

            fig = Figure(figsize=(10, 6), dpi=100)
            ax1 = fig.add_subplot(111)
            
            indices = range(len(produtos))
            
            ax1.bar(indices, valores, color='lightblue', label='Valor Total')
            ax1.set_xlabel('Produtos (Ordenados por Custo)')
            ax1.set_ylabel('Valor Total (R$)', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')

            ax2 = ax1.twinx()
            ax2.plot(indices, cumvals, color='red', marker='o', markersize=4, label='Percentual Acumulado')
            ax2.set_ylabel('Acumulado %', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            ax2.set_ylim(0, 105)

            fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
            fig.suptitle('Curva ABC - Custos de Estoque')
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            _criar_janela_grafico(fig, "Gráfico: Curva ABC")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o gráfico: {e}")

    def acao_custo_manutencao():
        try:
            taxa_percentual = simpledialog.askfloat("Custo de Manutenção", 
                                                    "Digite a taxa de manutenção (ex: '2' para 2%):", 
                                                    parent=app, minvalue=0.01, maxvalue=100.0)
            
            if taxa_percentual is None:
                return

            cursor.execute("SELECT SUM(valor_total) FROM produtos")
            valor_total_estoque = cursor.fetchone()[0]
            
            if valor_total_estoque:
                custo_manutencao = valor_total_estoque * (taxa_percentual / 100)
                resultado_str = f"Valor Total do Estoque: R$ {valor_total_estoque:,.2f}\n" \
                                f"Taxa Aplicada: {taxa_percentual:.2f}%\n" \
                                f"Custo de Manutenção: R$ {custo_manutencao:,.2f}"
                messagebox.showinfo("Relatório de Custo de Manutenção", resultado_str)
            else:
                messagebox.showinfo("Relatório", "Estoque vazio, custo de manutenção é R$ 0,00.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao calcular: {e}")

    def acao_relatorio_giro():
        try:
            dias_analise = simpledialog.askinteger("Relatório de Giro e Demanda", 
                                                   "Analisar o histórico de quantos dias para trás? (ex: 30):", 
                                                   parent=app, minvalue=1, maxvalue=3650)
            
            if dias_analise is None:
                return

            data_limite = datetime.now() - timedelta(days=dias_analise)
            
            cursor.execute("SELECT SUM(quantidade_saida) FROM historico_saidas WHERE data_saida >= ?", (data_limite,))
            total_saidas_periodo = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(quantidade) FROM produtos")
            total_estoque_atual = cursor.fetchone()[0] or 0
            
            giro_estoque = 0
            if total_estoque_atual > 0:
                giro_estoque = total_saidas_periodo / total_estoque_atual

            demanda_media_diaria = total_saidas_periodo / dias_analise

            resultado_str = f"--- Relatório Gerencial (Últimos {dias_analise} dias) ---\n\n" \
                            f"--- Desempenho de Vendas (Demanda) ---\n" \
                            f"Total de Unidades Vendidas: {total_saidas_periodo}\n" \
                            f"Demanda Diária Média: {demanda_media_diaria:.2f} unidades/dia\n\n" \
                            f"--- Saúde do Estoque ---\n" \
                            f"Total de Unidades em Estoque (Atual): {total_estoque_atual}\n" \
                            f"Giro de Estoque (no período): {giro_estoque:.2f}\n\n" \
                            f"--- Interpretação ---\n" \
                            f"* O Giro de '{giro_estoque:.2f}' significa que, nos últimos {dias_analise} dias, " \
                            f"você vendeu o equivalente a {giro_estoque:.2f} vezes o seu estoque atual."
            
            messagebox.showinfo("Relatório de Giro e Demanda", resultado_str)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")


    botoes_menu = [
        ("Dashboard", acao_dashboard),
        ("Cadastrar Produto", acao_cadastrar),
        ("Listar/Buscar Produtos", acao_listar_todos),
        ("Comprar (Entrada)", acao_comprar_estoque),
        ("Vender (Saída)", acao_vender_estoque),
        ("Excluir Produto", acao_excluir),
        ("Gráfico: Evolução", acao_grafico_evolucao),
        ("Gráfico: Categorias", acao_grafico_categorias),
        ("Gráfico: Curva ABC", acao_grafico_abc),
        ("Relatório: Custo Manutenção", acao_custo_manutencao),
        ("Relatório: Giro e Demanda", acao_relatorio_giro)
    ]

    for texto, comando in botoes_menu:
        btn = tk.Button(
            frame_menu, 
            text=texto, 
            command=comando, 
            font=("Arial", 11),
            bg=cor_sidebar,
            fg=cor_letra,
            relief="flat",
            anchor="w",
            padx=20,
            pady=8
        )
        btn.pack(fill="x")

    acao_dashboard()

    app.mainloop()

    conn.close()


if __name__ == "__main__":
    main()
