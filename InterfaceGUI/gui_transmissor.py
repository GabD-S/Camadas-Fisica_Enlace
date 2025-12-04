import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue
import sys

# Permite importação de módulos do diretório pai, como 'transmissor' e 'utils'.
sys.path.append('../')

# Importa lógica de transmissão e utilitários de conversão binário/texto.
from Simulador import transmissor
from Utilidades import utils

class TransmissorGUI(ttk.Frame):
    """
    Interface gráfica do Transmissor para o simulador de camadas de rede.
    Permite configurar parâmetros de transmissão, visualizar sinais em diferentes etapas
    e iniciar o envio de dados ao receptor.
    """
    def __init__(self, master):
        """
        Inicializa a GUI do Transmissor, criando janela, variáveis e widgets principais.
        Args:
            master (tk.Tk): Janela principal do Tkinter.
        """
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Transmissor (Tx)")
        self.master.geometry("1200x800")
        self.pack(fill=tk.BOTH, expand=True)

        # Fila para comunicação segura entre threads; backend envia atualizações para GUI.
        self.update_queue = queue.Queue()

        # Variáveis de controle para configuração e entrada da transmissão.
        self.msg_var = tk.StringVar(value="00000") # Mensagem a ser transmitida (binário/texto).
        self.raw_binary_input = tk.BooleanVar(value=True) # Se True, entrada é binário puro; se False, texto para conversão.
        self.enquadramento_var = tk.StringVar(value='Bit Stuffing (Flags)') # Camada de Enlace: enquadramento.
        self.mod_digital_var = tk.StringVar(value='NRZ-Polar') # Camada Física (banda base): codificação de linha.
        self.mod_portadora_var = tk.StringVar(value='Nenhum') # Camada Física (passa-faixa): modulação de portadora.
        self.detecao_erro_var = tk.StringVar(value='CRC-32') # Camada de Enlace: detecção de erro.
        self.correcao_erro_var = tk.StringVar(value='Hamming') # Camada de Enlace: correção de erro.
        self.taxa_erros_var = tk.DoubleVar(value=0.01) # Taxa de erro no canal (ruído/interferência).

        # Variáveis para exibir o quadro antes e depois do Bit Stuffing/Framing
        self.frame_before_stuffing_var = tk.StringVar(value="N/A")
        self.frame_after_stuffing_var = tk.StringVar(value="N/A")


        # Cria e posiciona todos os widgets da interface.
        self._create_widgets()
        # Inicia processamento periódico da fila de atualizações da GUI.
        self.process_queue()

    def _create_widgets(self):
        """
        Monta a interface gráfica: painéis de configuração, status, botão de transmissão e área de gráficos.
        """
        # Layout: duas colunas (configuração à esquerda, gráficos à direita).
        self.grid_columnconfigure(0, weight=1, minsize=450)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Painel esquerdo: configurações da simulação e status.
        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Frame de configuração de parâmetros da transmissão.
        config_frame = ttk.LabelFrame(left_panel, text="Configurações da Simulação", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        config_frame.grid_columnconfigure(1, weight=1)
        config_frame.grid_columnconfigure(2, weight=1)

        # Opções de configuração para cada camada do modelo OSI.
        enquadramento_options = ["Contagem de caracteres", "Byte Stuffing (Flags)", "Bit Stuffing (Flags)"]
        detecao_erro_options = ["Nenhum", "Paridade Par", "CRC-32", "Checksum"]
        correcao_erro_options = ["Nenhum", "Hamming"]
        mod_digital_options = ["NRZ-Polar", "Manchester", "Bipolar"] # Camada Física: banda base.
        mod_portadora_options = ["Nenhum", "ASK", "FSK","QPSK", "8-QAM", "16-QAM"] # Camada Física: passa-faixa.

        # Linha de entrada da mensagem.
        self.create_control_row(config_frame, 0, "Mensagem:", ttk.Entry(config_frame, textvariable=self.msg_var))
        # Checkbox para alternar entrada binária/texto.
        ttk.Checkbutton(config_frame, text="Entrada Binária Pura (0s e 1s)", variable=self.raw_binary_input).grid(row=0, column=2, sticky="w", padx=5, pady=2)

        # Configurações de enquadramento (enlace) e modulação (física).
        self.create_control_row(config_frame, 1, "Enquadramento:", ttk.Combobox(config_frame, textvariable=self.enquadramento_var, values=enquadramento_options, state="readonly"))
        self.create_control_row(config_frame, 2, "Mod. Digital:", ttk.Combobox(config_frame, textvariable=self.mod_digital_var, values=mod_digital_options, state="readonly"))
        self.create_control_row(config_frame, 3, "Mod. Portadora:", ttk.Combobox(config_frame, textvariable=self.mod_portadora_var, values=mod_portadora_options, state="readonly"))
        self.create_control_row(config_frame, 4, "Deteção de Erro:", ttk.Combobox(config_frame, textvariable=self.detecao_erro_var, values=detecao_erro_options, state="readonly"))
        self.create_control_row(config_frame, 5, "Correção de Erro:", ttk.Combobox(config_frame, textvariable=self.correcao_erro_var, values=correcao_erro_options, state="readonly"))

        # Slider para definir taxa de erros do canal (simula ruído/interferência).
        ttk.Label(config_frame, text="Taxa de Erros no Canal:").grid(row=6, column=0, sticky="w", padx=5, pady=(10,0))
        error_scale = ttk.Scale(config_frame, from_=0.0, to_=0.1, orient=tk.HORIZONTAL,
                                variable=self.taxa_erros_var, command=lambda v: self.error_label.config(text=f"{float(v):.3f}"))
        error_scale.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5)
        self.error_label = ttk.Label(config_frame, text=f"{self.taxa_erros_var.get():.3f}")
        self.error_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=5)

        # --- Campos para exibir o quadro antes e depois do Bit Stuffing ---
        frame_display_frame = ttk.LabelFrame(left_panel, text="Detalhes do Enquadramento", padding="10")
        frame_display_frame.pack(fill=tk.X, pady=5)
        frame_display_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame_display_frame, text="Quadro (Pré-Enquadramento):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.frame_before_stuffing_label = ttk.Label(frame_display_frame, textvariable=self.frame_before_stuffing_var, wraplength=400, justify=tk.LEFT, font=('TkFixedFont', 9))
        self.frame_before_stuffing_label.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_display_frame, text="Quadro (Pós-Enquadramento):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.frame_after_stuffing_label = ttk.Label(frame_display_frame, textvariable=self.frame_after_stuffing_var, wraplength=400, justify=tk.LEFT, font=('TkFixedFont', 9))
        self.frame_after_stuffing_label.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        # -------------------------------------------------------------------------

        # Botão para iniciar transmissão de dados ao receptor.
        self.send_button = ttk.Button(left_panel, text="Iniciar Transmissão", command=self.start_transmission_thread)
        self.send_button.pack(fill=tk.X, pady=20)

        # Frame de status atual da transmissão.
        status_frame = ttk.LabelFrame(left_panel, text="Estado", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label = ttk.Label(status_frame, text="Pronto.", foreground="blue", wraplength=400)
        self.status_label.pack(fill=tk.BOTH, expand=True)

        # Painel direito: exibição gráfica dos sinais gerados nas diferentes etapas do transmissor.
        plot_container = ttk.LabelFrame(self, text="Gráficos do Sinal Transmitido", padding="10")
        plot_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Notebook de abas para gráficos (digital, modulado, constelação).
        self.plot_notebook = ttk.Notebook(plot_container)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        # Cada aba exibe um gráfico Matplotlib com barra de ferramentas interativa.
        self.ax_digital, self.canvas_digital, self.toolbar_digital = self.create_plot_tab("Sinal Digital", figsize=(10, 4.5))
        self.ax_analog, self.canvas_analog, self.toolbar_analog = self.create_plot_tab("Sinal Modulado", figsize=(10, 4.5))
        self.ax_const, self.canvas_const, self.toolbar_const = self.create_plot_tab("Constelação 16-QAM (TX)", figsize=(8, 6))

    def create_control_row(self, parent, row, label_text, widget):
        """
        Cria uma linha padrão composta por rótulo e widget de entrada/seleção.
        Usado para montar painéis de configuração na GUI.

        Args:
            parent (ttk.Frame): Frame onde será inserida a linha.
            row (int): Posição da linha na grid.
            label_text (str): Texto do rótulo da configuração.
            widget (ttk.Widget): Widget de entrada (Entry, Combobox etc.).
        """
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    def create_plot_tab(self, tab_name, figsize=(8, 3.5)):
        """
        Cria uma nova aba de gráficos, integrando figura Matplotlib,
        canvas Tkinter e barra de ferramentas de navegação padrão.
        Facilita a análise visual dos sinais gerados nas diferentes etapas do transmissor.

        Args:
            tab_name (str): Nome da aba e título inicial do gráfico.
            figsize (tuple): Tamanho da figura Matplotlib em polegadas.
        Returns:
            tuple: (Axes, FigureCanvasTkAgg, NavigationToolbar2Tk)
        """
        tab = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(tab, text=tab_name)
        fig, ax = plt.subplots(figsize=figsize)
        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        canvas._tkcanvas.pack(fill=tk.BOTH, expand=True) # Necessário para a barra de ferramentas.
        self.clear_plot_ax(ax, canvas, title=tab_name)
        return ax, canvas, toolbar

    def start_transmission_thread(self):
        """
        Inicia a transmissão em uma thread separada, mantendo a GUI responsiva.
        Valida a entrada, desabilita o botão, limpa gráficos e status antes de transmitir.
        """
        self.send_button.config(state="disabled")
        self.clear_all() # Limpa gráficos e status para nova simulação.

        # Limpa os campos de quadro antes e depois do stuffing
        self.frame_before_stuffing_var.set("N/A")
        self.frame_after_stuffing_var.set("N/A")

        message_input = self.msg_var.get()

        # Fase de codificação de fonte: identifica se a entrada é binária pura ou texto.
        if self.raw_binary_input.get():
            # Validação de entrada: apenas '0' e '1' permitidos em modo binário puro.
            if not all(bit in '01' for bit in message_input):
                self.status_label.config(
                    text="ERRO: Entrada binária pura deve conter apenas '0's e '1's.", foreground="red"
                )
                self.send_button.config(state="normal")
                return
            bits_to_send = message_input
            original_message_for_log = message_input
        else:
            # Se entrada é texto, converte para bits (ASCII, 8 bits por caractere).
            bits_to_send = utils.text_to_binary(message_input)
            original_message_for_log = message_input

        # Prepara parâmetros para a transmissão (define comportamento das camadas OSI).
        params = {
            "message": original_message_for_log, # Mensagem original (texto/binário).
            "bits_raw_input": bits_to_send, # Sequência de bits a ser transmitida.
            "enquadramento_type": self.enquadramento_var.get(), # Camada de Enlace: enquadramento.
            "mod_digital_type": self.mod_digital_var.get(), # Camada Física: codificação de linha.
            "mod_portadora_type": self.mod_portadora_var.get(), # Camada Física: modulação de portadora.
            "detecao_erro_type": self.detecao_erro_var.get(), # Camada de Enlace: detecção de erro.
            "correcao_erro_type": self.correcao_erro_var.get(), # Camada de Enlace: correção de erro.
            "taxa_erros": self.taxa_erros_var.get(), # Taxa de erro simulada no canal.
            "gui_callback": self.gui_update_callback # Passa o callback para o módulo transmissor
        }

        # Executa função de transmissão em nova thread, mantendo interface fluida.
        thread = threading.Thread(target=transmissor.run_transmitter, args=(params,))
        thread.daemon = True # Encerra thread automaticamente com o fechamento da GUI.
        thread.start()

    def gui_update_callback(self, update_dict):
        """
        Callback chamada pela thread de transmissão para enviar atualizações à GUI.
        Garante comunicação thread-safe: insere as mensagens na fila de atualizações,
        para processamento exclusivo na thread principal do Tkinter.

        Args:
            update_dict (dict): Dicionário com o tipo de atualização e dados associados.
        """
        self.update_queue.put(update_dict)

    def process_queue(self):
        """
        Processa as mensagens pendentes na fila de atualização da GUI.
        Chamada periodicamente pela thread principal (Tkinter) via master.after(),
        garante atualização assíncrona, segura e responsiva da interface.
        """
        try:
            while not self.update_queue.empty():
                msg = self.update_queue.get_nowait()
                msg_type = msg.get('type')

                # Direciona a mensagem para o método apropriado conforme o tipo.
                if msg_type == 'status':
                    self.status_label.config(text=msg['message'], foreground=msg['color'])
                    # Reabilita o botão se a transmissão foi concluída ou houve erro.
                    if "concluída" in msg['message'] or "Erro" in msg['message']:
                        self.send_button.config(state="normal")
                elif msg_type == 'plot_digital':
                    self.update_digital_plot(msg['data']) # Atualiza o gráfico de sinal digital (banda base).
                elif msg_type == 'plot_analog':
                    self.update_analog_plot(msg['data']) # Atualiza o gráfico do sinal analógico modulado.
                elif msg_type == 'plot_constellation':
                    self.update_constellation_plot(msg['data']) # Atualiza o gráfico da constelação 8-QAM.
                elif msg_type == 'frame_display': # Atualiza a exibição dos quadros
                    self.update_frame_display(msg['data'])
                elif msg_type == 'log': 
                    pass 
        finally:
            # Agenda a próxima verificação após 100 ms (mantém loop de eventos da GUI).
            self.master.after(100, self.process_queue)

    def clear_all(self):
        """
        Limpa todos os gráficos da interface, preparando para uma nova simulação.
        Remove dados, títulos e grade de todos os eixos.
        """
        self.clear_plot_ax(self.ax_digital, self.canvas_digital, "Sinal Digital")
        self.clear_plot_ax(self.ax_analog, self.canvas_analog, "Sinal Modulado")
        self.clear_plot_ax(self.ax_const, self.canvas_const, "Constelação 8-QAM (TX)")
        # Também limpa os campos de texto do quadro
        self.frame_before_stuffing_var.set("N/A")
        self.frame_after_stuffing_var.set("N/A")


    def clear_plot_ax(self, ax, canvas, title):
        """
        Limpa um gráfico Matplotlib, removendo linhas/textos e redefinindo título/grade.

        Args:
            ax (matplotlib.axes.Axes): Eixo a ser limpo.
            canvas (FigureCanvasTkAgg): Canvas associado ao eixo.
            title (str): Novo título do gráfico.
        """
        ax.clear()
        ax.set_title(title, fontsize=12)
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.8)
        canvas.draw()

    def update_digital_plot(self, plot_data):
        """
        Atualiza o gráfico de sinal digital gerado pela codificação de linha (Camada Física - Banda Base).
        Exibe a sequência de bits processada por técnicas como NRZ-Polar, Manchester ou Bipolar.

        Args:
            plot_data (dict): Contém 't' (tempo), 'signal' (valores do sinal digital), e 'config' (parâmetros de transmissão).
        """
        ax, canvas = self.ax_digital, self.canvas_digital
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        
        # DEBUG: Análise do sinal digital gerado.
        print(f"DEBUG: update_digital_plot - Tipo de Modulação Digital: {config['mod_digital_type']}")
        print(f"DEBUG: update_digital_plot - Comprimento do sinal: {len(signal)}")
        print(f"DEBUG: update_digital_plot - Primeiros 10 valores do sinal: {signal[:10]}")
        print(f"DEBUG: update_digital_plot - Últimos 10 valores do sinal: {signal[-10:]}")
        if len(signal) > 0 and config['mod_digital_type'] == 'NRZ-Polar':
            unique_vals = np.unique(signal)
            print(f"DEBUG: update_digital_plot - Valores únicos no sinal: {unique_vals}")
            if len(unique_vals) == 1 and unique_vals[0] == -1.0:
                print("DEBUG: O array do sinal é plano em -1.0 como esperado para '0's em NRZ-Polar.")
            else:
                print("DEBUG: O array do sinal NÃO é plano em -1.0. Contém variações.")
        # ---

        self.clear_plot_ax(ax, canvas, f"Sinal Digital ({config['mod_digital_type']})")
        ax.step(t, signal, where='post', label=f"{config['mod_digital_type']}", color='dodgerblue')
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude (V)")
        if len(signal) > 0:
            min_val = np.min(signal)
            max_val = np.max(signal)
            y_margin = (max_val - min_val) * 0.1 if (max_val - min_val) > 0 else 0.2
            ax.set_ylim(min_val - y_margin, max_val + y_margin)
            ax.set_xlim(left=0, right=max(t) if len(t) > 0 else 1)
        ax.legend()
        canvas.draw()

    def update_analog_plot(self, plot_data):
        """
        Atualiza o gráfico do sinal modulado (analógico), pronto para transmissão (Camada Física - Passa-faixa).
        Mostra o resultado da modulação por portadora (ASK, FSK, QAM etc) do sinal digital.

        Args:
            plot_data (dict): Contém 't' (tempo), 'signal' (sinal analógico), e 'config' (parâmetros de transmissão).
        """
        ax, canvas = self.ax_analog, self.canvas_analog
        t, signal, config = plot_data['t'], plot_data['signal'], plot_data['config']
        self.clear_plot_ax(ax, canvas, f"Sinal Modulado ({config['mod_portadora_type']})")
        ax.plot(t, signal, label=f"{config['mod_portadora_type']}", color='coral')
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude (V)")

        window_duration = 2.5
        max_time = t[-1] if len(t) > 0 else 0
        xlim_end = min(window_duration, max_time)
        ax.set_xlim(0, xlim_end)

        if len(signal) > 0:
            margin = (max(signal) - min(signal)) * 0.1
            ax.set_ylim(min(signal) - margin, max(signal) + margin)

        ax.legend()
        canvas.draw()

    def update_constellation_plot(self, plot_data):
        """
        Atualiza o gráfico do diagrama de constelação para modulações como 8-QAM (Camada Física).
        Cada ponto representa um símbolo transmitido no plano I (Em Fase) e Q (Quadratura).

        Args:
            plot_data (dict): Contém 'points' (lista de números complexos representando a constelação).
        """
        ax, canvas = self.ax_const, self.canvas_const
        points = plot_data['points']
        self.clear_plot_ax(ax, canvas, "Constelação 8-QAM (TX)")


        # Separa os pontos em suas componentes de fase (I) e quadratura (Q).
        real = [p.real for p in points]
        imag = [p.imag for p in points]
        ax.scatter(real, imag, color='purple', s=40, alpha=0.8)


        # Linhas de referência dos eixos centrais (I=0, Q=0).
        ax.axhline(0, color='gray', lw=0.5)
        ax.axvline(0, color='gray', lw=0.5)
        ax.set_xlabel("Em Fase (I)")
        ax.set_ylabel("Quadratura (Q)")

        # Ajusta limites dos eixos para abranger todos os pontos e a origem, com margem visual.
        all_coords = real + imag
        if all_coords:
            max_abs_val = max(abs(val) for val in all_coords)
            limit = max_abs_val * 1.2
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
        else:
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)



        ax.set_aspect('equal', 'box') # Garante escala igual nos eixos.



        # Anota cada ponto da constelação com identificadores (S0, S1...), ligeiramente deslocados.
        for i, point in enumerate(points):
            ax.annotate(f'S{i}', (point.real + 0.05, point.imag + 0.05), fontsize=8)


        canvas.draw()

    # --- MÉTODO PARA ATUALIZAR OS TEXTOS DOS QUADROS ---
    def update_frame_display(self, frame_data):
        """
        Atualiza os labels na GUI com os valores binários do quadro antes e depois do enquadramento.

        Args:
            frame_data (dict): Dicionário contendo 'payload_before_stuffing' e 'frame_after_stuffing'.
        """
        if 'payload_before_stuffing' in frame_data:
            self.frame_before_stuffing_var.set(frame_data['payload_before_stuffing'])
        if 'frame_after_stuffing' in frame_data:
            self.frame_after_stuffing_var.set(frame_data['frame_after_stuffing'])
    # --------------------------------------------------------

if __name__ == '__main__':
    # Inicializa e executa a aplicação GUI do Transmissor.
    root = tk.Tk()
    app = TransmissorGUI(root)
    root.mainloop()