# Yahoo Finance Crawler

Este projeto é um crawler desenvolvido em Python para extrair dados do Yahoo Finance, utilizando **Selenium** para navegação e **BeautifulSoup** para parsing de HTML.

## 📋 Pré-requisitos

Para executar este projeto, você precisará ter instalado:

- **Python 3.13+**
- **[Poetry](https://python-poetry.org/docs/#installation)** (Gerenciador de dependências)

## 🚀 Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/buguno/crawler.git
   cd crawler
   ```

2. Instale as dependências do projeto utilizando o Poetry:

   ```bash
   poetry install
   ```

3. Configure as variáveis de ambiente:

   Crie um arquivo `.env` na raiz do projeto com base no arquivo de exemplo (`.env.example`).

   ```bash
   cp .env.example .env
   ```

   Certifique-se de que a variável `BASE_URL` está definida corretamente no arquivo `.env`.

## 💻 Como Rodar

Existem duas formas principais de rodar a aplicação: ativando o shell do Poetry ou utilizando os comandos configurados via `taskipy`.

### Opção 1: Via Shell do Poetry (Recomendado para uso manual)

1. Ative o ambiente virtual do Poetry:

   ```bash
   poetry shell
   ```

2. Execute a aplicação:

   ```bash
   task crawler
   ```

#### Flags Disponíveis

Você pode customizar a execução utilizando as seguintes flags:

- `--region`: Define a região para filtrar os dados (Padrão: "Brazil").
- `--show-browser`: Abre o navegador visualmente (desativa o modo *headless*). Útil para debugging.

**Exemplos:**

Rodar para a região "United Kingdom":

```bash
task crawler --region "United Kingdom"
```

Rodar visualizando o navegador (não headless):

```bash
task crawler --show-browser
```

Combinando flags:

```bash
task crawler --region "Argentina" --show-browser
```

### Opção 2: Via Taskipy (Atalhos)

O projeto possui atalhos configurados no `pyproject.toml` para facilitar o uso.

## 🧪 Testes

Para garantir que tudo está funcionando corretamente, você pode rodar a suíte de testes.

1. Execute os testes com cobertura:

   ```bash
   poetry run task test
   ```

   Ou, se já estiver no shell (`poetry shell`):

   ```bash
   task test
   ```

   Este comando executará o `pytest` com configurações de verbosidade e cobertura de código.

2. Para ver o relatório de cobertura HTML (após rodar os testes):

   ```bash
   poetry run task post_test
   ```

## 🛠 Comandos de Desenvolvimento

Além de rodar e testar, existem comandos úteis para manter a qualidade do código:

- **Lint (verificação):**

  ```bash
  task lint
  ```

- **Formatação (automática):**

  ```bash
  task format
  ```
