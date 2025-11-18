# Sistema de Gestão de Estoque
Um projeto completo de sistema de gestão de estoque focado em um mercado, desenvolvido totalmente em Python. O sistema conta com uma interface gráfica e um banco de dados local para controle total das operações.

<img width="1353" height="717" alt="image" src="https://github.com/user-attachments/assets/cc58e709-dc1b-4d50-96f4-50ed4d4f2783" />


## Funcionalidades
  Dashboard Interativo: Métricas rápidas (custo total, itens totais, estoque baixo) e atalhos.

  Alertas Visuais: Lista de produtos com estoque baixo direto na página principal, com botão para "Comprar" imediato.

  Gestão Completa (CRUD): Cadastro, Exclusão, Compra (Entrada) e Venda (Saída) de produtos.

  Busca e Ordenação Avançada: Tela de produtos com filtros por nome/categoria e ordenação clicável em colunas.

  Relatórios Gerenciais:
  
  → Gráficos (Matplotlib): Curva ABC, Valor por Categoria e Evolução de Estoque.
  
  → Relatórios (Texto): Cálculo de Custo de Manutenção e Giro de Estoque.

## Tecnologias Utilizadas
→ Python 3

→ Tkinter

→ SQLite3

→ Matplotlib

# Como Executar
Este projeto tem duas formas de instalação, escolha a sua:

## 1. Para Usuários (Recomendado)
Se você quer apenas usar o programa no Windows, baixe o pacote pronto:

Vá para a Página de Releases deste projeto.

Baixe o arquivo .zip da versão mais recente (gestao_estoque_v1.0.zip).

Descompacte o arquivo em qualquer pasta.

Abra a pasta mercado_gui e dê dois cliques no mercado_gui.exe.

(Importante: O .exe e o mercado.db devem estar sempre na mesma pasta para funcionar.)

## 2. Para Desenvolvedores (Código-Fonte)
   Se você quer rodar o código, modificar ou estudar:
   
        1. Clone o repositório
        
        2. Instale as dependências
        pip install matplotlib, tkinter, sqlite3
        
        3. (Se o mercado.db não existir) Apague o .gitignore (ou comente a linha *.db)
        para que o script crie o banco na primeira vez que rodar.
        
        # 4. Rode o programa python mercado_gui.py
