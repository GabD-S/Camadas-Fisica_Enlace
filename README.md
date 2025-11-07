# Camadas-Fisica_Enlace

Simulador das camadas Física e de Enlace para a disciplina de **Teleinformática e Redes 1 (TR1)**.

Permite simular técnicas essenciais como enquadramento (byte stuffing, bit stuffing, contagem de caracteres), modulação digital e analógica, e métodos de detecção e correção de erros, como paridade e CRC.

---

## 🧱 Pré-requisitos

- Python **3.10 ou superior**
- Git (para clonar o projeto)
- Acesso à linha de comando (Linux/macOS: terminal | Windows: PowerShell, CMD ou GitBash)

---

## ⚙️ Instalação

### 1. Clone o repositório

Clone o repositório usando:

```bash
git clone https://github.com/GabD-S/Camadas-Fisica_Enlace.git
```

Entre na pasta criada:

```bash
cd Camadas-Fisica_Enlace
```

---

### 2. Crie e ative um ambiente virtual (recomendado)

> Um ambiente virtual **evita conflitos** de dependências com outros projetos Python.

#### Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows:

```cmd
python -m venv venv
.\venv\Scripts\activate
```

---

### 3. Instale as dependências

O projeto contém um arquivo `requirements.txt` com todas as dependências necessárias:

```bash
pip install -r requirements.txt
```

> **Nota:** O arquivo `requirements.txt` é atualizado automaticamente ao adicionar novas dependências.

---

## ▶️ Executando o Simulador

Com o ambiente virtual ativado e dependências instaladas, acesse a pasta da interface gráfica:

```bash
cd InterfaceGUI
```

Execute o transmissor e o receptor em terminais separados:

### 🛰️ Transmissor:
```bash
python gui_transmissor.py
```

### 📡 Receptor:
```bash
python gui_receptor.py
```

Uma interface gráfica será aberta permitindo simular técnicas como enquadramento, modulação digital e analógica, além de métodos para controle de erros como paridade e CRC.

---

## 🙋‍♂️ Problemas Comuns

- **Ambiente virtual (`venv`) indisponível no Linux:**
  ```bash
  sudo apt install python3-venv
  ```

- **Erro com o módulo gráfico `tkinter` (Linux):**
  ```bash
  sudo apt install python3-tk
  ```

---

## 🧼 Arquivos ignorados

Este projeto utiliza `.gitignore` para excluir automaticamente do controle de versão:

- Ambientes virtuais (`venv/`)
- Arquivos temporários, cache, logs
- Arquivos específicos do sistema operacional

---