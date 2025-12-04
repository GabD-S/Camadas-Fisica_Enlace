# InterfaceGui/gui_receptor.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import queue
import sys

# Permite importação de módulos de um diretório acima, como 'receptor'.
sys.path.append('../')

# Importa o backend do receptor, responsável pelo processamento das camadas físicas e superiores.
from Simulador import receptor

class ReceptorGUI(ttk.Frame):
    """
    Interface gráfica para o Receptor do simulador de comunicação em camadas.
    Exibe status da recepção, configurações, resultados de detecção/correção de erro,
    mensagem final decodificada e gráficos dos sinais.
    """
    def __init__(self, master):
        """
        Inicializa a interface gráfica do receptor e seus componentes principais.

        Args:
            master (tk.Tk): Janela principal do Tkinter.
        """
        super().__init__(master, padding="10")
        self.master = master
        self.master.title("Simulador de Transmissão - Receptor (Rx)")  # Título da janela.
        self.master.geometry("1200x800")  # Tamanho inicial da janela.
        self.pack(fill=tk.BOTH, expand=True)

        # Fila para troca de mensagens entre thread do backend e thread da interface,
        # evitando travamentos e mantendo a GUI responsiva.
        self.update_queue = queue.Queue()

        # Criação das variáveis de controle (StringVar) para vincular dados aos widgets da interface.
        self._create_variables()
        # Montagem dos elementos gráficos (widgets) na janela.
        self._create_widgets()

        # Inicia o servidor do receptor em uma thread separada,
        # permitindo a espera por conexões sem bloquear a interface gráfica.
        self.start_listening_thread()
        # Inicia o processamento assíncrono das atualizações da fila (update_queue)
        # garantindo que a interface permaneça atualizada conforme a recepção de dados.
        self.process_queue()

    def _create_variables(self):
        """
        Inicializa todas as variáveis StringVar do Tkinter para exibir dinamicamente
        o status da comunicação, resultados de processamento e parâmetros recebidos.
        Variáveis vinculam a lógica do backend com a interface gráfica.
        """
        self.connection_status_var = tk.StringVar(value="Iniciando...")      # Status da conexão TCP/IP.
        self.decode_status_var = tk.StringVar(value="Inativo")               # Status geral da decodificação do pacote recebido.
        self.detection_method_var = tk.StringVar(value="Detecção:")          # Tipo de método de detecção de erro (camada de enlace).
        self.detection_status_var = tk.StringVar(value="N/A")                # Resultado da detecção de erro (ex: "OK", "INVÁLIDO").
        self.detection_details_var = tk.StringVar(value="")                  # Informações adicionais sobre detecção (ex: valor CRC).
        self.hamming_status_var = tk.StringVar(value="N/A")                  # Status da correção de erro por código Hamming.

        # Variáveis para exibir configurações de transmissão recebidas como metadados,
        # incluindo parâmetros das camadas de enlace e física.
        self.received_enquadramento_var = tk.StringVar(value="N/A")          # Enquadramento (Camada de Enlace).
        self.received_mod_digital_var = tk.StringVar(value="N/A")            # Modulação digital (Camada Física - banda base).
        self.received_mod_portadora_var = tk.StringVar(value="N/A")          # Modulação por portadora (Camada Física - passa-faixa).
        self.received_detecao_erro_var = tk.StringVar(value="N/A")           # Detecção de erro (Camada de Enlace).
        self.received_correcao_erro_var = tk.StringVar(value="N/A")          # Correção de erro (Camada de Enlace).
        self.received_bit_rate_var = tk.StringVar(value="N/A")               # Taxa de bits (Camada Física).
        self.received_freq_var = tk.StringVar(value="N/A")                   # Frequência da portadora (Camada Física).
        self.received_amplitude_var = tk.StringVar(value="N/A")              # Amplitude do sinal (Camada Física).
        self.received_sampling_rate_var = tk.StringVar(value="N/A")          # Taxa de amostragem (Camada Física).
        self.received_error_rate_var = tk.StringVar(value="N/A")             # Taxa de erro aplicada no canal (simulação).

    def _create_widgets(self):
        """
        Monta a interface gráfica do receptor, distribuindo painéis, frames e widgets para
        exibir informações de status, configuração e visualização gráfica dos sinais.
        """
        # Organiza o layout principal da janela: coluna esquerda (status/configuração) e coluna direita (gráficos).
        self.grid_columnconfigure(0, weight=1, minsize=450)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Painel esquerdo – informações de configuração, status do processamento e mensagem decodificada.
        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Frame: exibe as configurações recebidas (metadados do transmissor).
        received_config_frame = ttk.LabelFrame(left_panel, text="Configurações Recebidas", padding="10")
        received_config_frame.pack(fill=tk.X, pady=5)
        received_config_frame.grid_columnconfigure(1, weight=1)

        # Lista de pares (label, StringVar) para criar dinamicamente rótulos e valores de configuração.
        configs = [
            ("Enquadramento:", self.received_enquadramento_var),
            ("Mod. Digital:", self.received_mod_digital_var),
            ("Mod. Portadora:", self.received_mod_portadora_var),
            ("Detecção Erro:", self.received_detecao_erro_var),
            ("Correção Erro:", self.received_correcao_erro_var),
            ("Taxa de Bits:", self.received_bit_rate_var),
            ("Frequência:", self.received_freq_var),
            ("Amplitude:", self.received_amplitude_var),
            ("Taxa Amostragem:", self.received_sampling_rate_var),
            ("Taxa de Erros Aplicada:", self.received_error_rate_var)
        ]
        for i, (label_text, var) in enumerate(configs):
            ttk.Label(received_config_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=2, pady=1)
            ttk.Label(received_config_frame, textvariable=var, foreground="#333").grid(row=i, column=1, sticky="w", padx=2, pady=1)

        # Frame: status de cada etapa do processamento (conexão, decodificação, correção de erro).
        status_process_frame = ttk.LabelFrame(left_panel, text="Status do Processamento", padding="10")
        status_process_frame.pack(fill=tk.X, pady=10)
        status_process_frame.grid_columnconfigure(1, weight=1)

        # Linhas de status para conexão TCP, decodificação e correção Hamming.
        self.connection_status_label = self.create_status_row(status_process_frame, 0, "Status Conexão:", self.connection_status_var)
        self.decode_status_label = self.create_status_row(status_process_frame, 1, "Status Decodificação:", self.decode_status_var)
        self.hamming_status_label = self.create_status_row(status_process_frame, 2, "Status Hamming:", self.hamming_status_var)

        # Status do método de detecção de erro (Camada de Enlace) e detalhes do processo.
        self.detection_method_label = ttk.Label(status_process_frame, textvariable=self.detection_method_var)
        self.detection_method_label.grid(row=3, column=0, sticky="w", padx=2, pady=1)
        self.detection_status_label = ttk.Label(status_process_frame, textvariable=self.detection_status_var)
        self.detection_status_label.grid(row=3, column=1, sticky="w", padx=2, pady=1)
        self.detection_details_label = ttk.Label(status_process_frame, textvariable=self.detection_details_var, font=('TkFixedFont', 8), wraplength=350)
        self.detection_details_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=1)

        # Frame: mensagem final decodificada (com scrollbar).
        received_msg_frame = ttk.LabelFrame(left_panel, text="Mensagem Final Recebida", padding="10")
        received_msg_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.received_message_text = scrolledtext.ScrolledText(received_msg_frame, wrap=tk.WORD, height=4, state="disabled", font=("Helvetica", 12))
        self.received_message_text.pack(fill=tk.BOTH, expand=True)

        # Painel direito – área de gráficos dos sinais recebidos.
        plot_container_frame = ttk.LabelFrame(self, text="Gráficos do Sinal Recebido", padding="10")
        plot_container_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Notebook (abas) para visualização gráfica de diferentes etapas do sinal.
        self.plot_notebook = ttk.Notebook(plot_container_frame)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)

        # Gráfico do sinal recebido no canal (Camada Física).
        self.ax_pre, self.canvas_pre = self.create_plot_tab("Sinal RX")
        # Gráfico dos bits após demodulação (Camada Física - banda base).
        self.ax_post, self.canvas_post = self.create_plot_tab("Bits RX")
        # Gráfico da constelação 8-QAM recebida (para análise de ruído/interferência).
        self.ax_const_rx, self.canvas_const_rx = self.create_plot_tab("Constelação 16-QAM (RX)", figsize=(8, 6))

    def create_plot_tab(self, name, figsize=(6, 3)):
        """
        Cria uma nova aba no notebook de gráficos, associando um gráfico Matplotlib com
        canvas Tkinter e barra de ferramentas interativa (zoom, pan, salvar).
        Permite a visualização de diferentes etapas do processamento do sinal.
        
        Args:
            name (str): Nome/título da aba e do gráfico.
            figsize (tuple): Tamanho da figura Matplotlib em polegadas (largura, altura).
        Returns:
            tuple: (Axes do Matplotlib, FigureCanvasTkAgg do Tkinter)
        """
        tab = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(tab, text=name)
        fig, ax = plt.subplots(figsize=figsize)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        toolbar = NavigationToolbar2Tk(canvas, tab)  # Ferramentas de navegação para análise do gráfico.
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.clear_plot_ax(ax, canvas, title=name)
        return ax, canvas

    def clear_plot_ax(self, ax, canvas, title):
        """
        Limpa o gráfico (Axes) e prepara para uma nova plotagem, definindo título e grade.
        
        Args:
            ax (matplotlib.axes.Axes): Eixo do Matplotlib a ser limpo.
            canvas (FigureCanvasTkAgg): Canvas Tkinter do gráfico.
            title (str): Título a ser definido para o gráfico.
        """
        ax.clear()
        ax.set_title(title, fontsize=10)
        ax.grid(True, linestyle='--', linewidth=0.5)
        canvas.draw()

    def plot_pre_demod(self, data):
        """
        Atualiza o gráfico do sinal recebido no canal (antes da demodulação),
        representando a Camada Física do modelo OSI.
        Exibe o sinal analógico/ruidoso recebido pelo receptor.

        Args:
            data (dict): Contém 't' (tempo), 'signal_real' (sinal recebido) e
                        'config' (parâmetros de transmissão para o título).
        """
        ax, canvas = self.ax_pre, self.canvas_pre
        # Atualiza o título do gráfico conforme o tipo de modulação por portadora utilizada.
        self.clear_plot_ax(ax, canvas, f"Sinal Recebido (Pré-Demod) - {data['config']['mod_portadora_type']}")
        ax.plot(data['t'], data['signal_real'], color='blue', linewidth=1)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude")
        
        # Ajusta janela do eixo X para exibir até 2.5 segundos ou o tamanho total do sinal (o que for menor).
        window_duration = 2.5
        ax.set_xlim(0, min(window_duration, data['t'][-1] if len(data['t']) > 0 else 1))
        
        # Garante visibilidade total do sinal no eixo Y, adicionando uma margem ao topo e base.
        if len(data['signal_real']) > 0:
            margin = (max(data['signal_real']) - min(data['signal_real'])) * 0.1
            ax.set_ylim(min(data['signal_real']) - margin, max(data['signal_real']) + margin)
        canvas.draw()


    def plot_post_demod(self, data):
        """
        Atualiza o gráfico do sinal digital reconstruído após demodulação.
        Representa o sinal banda base já extraído da portadora, caracterizando a
        Camada Física após demodulação (ex: NRZ-Polar, Manchester).
        
        Args:
            data (dict): Contém 't' (tempo), 'signal' (níveis digitais), e 'config' (parâmetros para título).
        """
        ax, canvas = self.ax_post, self.canvas_post
        config = data['config']
        # Define o título conforme o tipo de modulação digital recebida.
        self.clear_plot_ax(ax, canvas, f"Bits Recuperados ({config['mod_digital_type']})")
        # Plota a forma de onda digital usando degraus, evidenciando transições de bit.
        ax.step(data['t'], data['signal'], where='post', color='dodgerblue', linewidth=1.2)
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Nível Lógico")
        
        # Janela do eixo X limitada para visualização detalhada de poucos bits.
        window_duration = 0.05
        ax.set_xlim(0, min(window_duration, data['t'][-1] if len(data['t']) > 0 else 1))
        
        # Ajusta eixo Y para acomodar todos os níveis, adicionando margem visual.
        if len(data['signal']) > 0:
            min_val = np.min(data['signal'])
            max_val = np.max(data['signal'])
            y_margin = (max_val - min_val) * 0.1 if (max_val - min_val) > 0 else 0.2
            ax.set_ylim(min_val - y_margin, max_val + y_margin)
        canvas.draw()

    def plot_constellation_rx(self, plot_data):
        """
        Atualiza o gráfico de constelação I/Q após demodulação, visualizando a dispersão dos símbolos
        causada por ruído/interferências no canal. Permite análise visual da qualidade da transmissão.
        
        Args:
            plot_data (dict): Contém 'points', lista de símbolos complexos (I + jQ).
        """
        ax, canvas = self.ax_const_rx, self.canvas_const_rx
        points = plot_data['points']

        # Verifique o tipo de modulação para definir título apropriado
        modulation_type = plot_data.get('modulation', '8-QAM')
    
        if modulation_type == '16-QAM':
            title = "Constelação 16-QAM Recebida (com Ruído)"
        elif modulation_type == 'QPSK':
            title = "Constelação QPSK Recebida (com Ruído)"
        else:
            title = "Constelação 8-QAM Recebida (com Ruído)"
        
        self.clear_plot_ax(ax, canvas, title)
        
        real = [p.real for p in points]
        imag = [p.imag for p in points]
        ax.scatter(real, imag, color='purple', s=40, alpha=0.8, edgecolors='black', linewidths=0.5)
        
        # Eixos centrais
        ax.axhline(0, color='gray', lw=0.5)
        ax.axvline(0, color='gray', lw=0.5)
        ax.set_xlabel("Em Fase (I)")
        ax.set_ylabel("Quadratura (Q)")
        
        # Adicionar pontos de referência da constelação ideal
        if modulation_type == 'QPSK':
            # Pontos de referência do QPSK
            qpsk_ref_points = [
                1/np.sqrt(2) + 1j/np.sqrt(2),   # 00 (45°)
                -1/np.sqrt(2) + 1j/np.sqrt(2),  # 01 (135°)
                -1/np.sqrt(2) - 1j/np.sqrt(2),  # 10 (225°)
                1/np.sqrt(2) - 1j/np.sqrt(2)    # 11 (315°)
            ]
            real_ref = [p.real for p in qpsk_ref_points]
            imag_ref = [p.imag for p in qpsk_ref_points]
            ax.scatter(real_ref, imag_ref, color='red', s=80, alpha=0.3, marker='x', label='Ideal')
            ax.legend()
        
        # Ajuste automático dos limites
        all_coords = real + imag
        if all_coords:
            max_abs_val = max(abs(val) for val in all_coords)
            limit = max_abs_val * 1.5
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
        else:
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
        
        ax.set_aspect('equal', 'box')
        canvas.draw()

    def process_queue(self):
        """
        Processa todas as mensagens da fila de atualização, garantindo comunicação segura
        entre a thread de backend (receptor) e a thread da GUI. 
        Fundamental para integração em aplicações Tkinter multi-thread.
        """
        try:
            while not self.update_queue.empty():
                msg = self.update_queue.get_nowait()
                msg_type = msg.get('type')

                # Despacha cada tipo de mensagem para a função correspondente na interface.
                if msg_type == 'new_connection':
                    self.clear_all_for_new_connection(msg['address'])
                elif msg_type == 'connection_status':
                    self.update_status_var(self.connection_status_label, self.connection_status_var, msg)
                elif msg_type == 'decode_status':
                    self.update_status_var(self.decode_status_label, self.decode_status_var, msg)
                elif msg_type == 'hamming_status':
                    self.update_status_var(self.hamming_status_label, self.hamming_status_var, msg)
                elif msg_type == 'received_configs':
                    self.update_received_configs(msg['data'])
                elif msg_type == 'detection_result':
                    self.update_detection_display(msg['data'])
                elif msg_type == 'final_message':
                    self.update_received_message(msg['message'])
                elif msg_type == 'plot':
                    self.dispatch_plot(msg['tab'], msg['data'])
        finally:
            # Agenda a próxima verificação da fila; mantém o loop de atualização da GUI.
            self.master.after(100, self.process_queue)

    def update_detection_display(self, data):
        """
        Atualiza campos da GUI relativos ao resultado da detecção de erros (Camada de Enlace).
        Fornece feedback visual (cor/descrição) do método de detecção e detalhes (ex: CRC).
        """
        method = data.get('method')
        status = data.get('status')
        color = "green" if "OK" in status else "red" if "INVÁLIDO" in status else "black"
        self.detection_details_var.set("")

        if method == "Nenhuma":
            self.detection_method_var.set("Detecção de Erro:")
            self.detection_status_var.set("N/A (desativada)")
            self.detection_status_label.config(foreground="black")
        elif method == "Paridade Par":
            self.detection_method_var.set("Status Paridade:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
        elif method == "CRC-32":
            self.detection_method_var.set("Status CRC-32:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
            calc = data.get('calc')
            recv = data.get('recv')
            # Exibe valores binários do CRC calculado e recebido.
            details_text = f"Calculado: 0b{calc:032b}\nRecebido:  0b{recv:032b}"
            self.detection_details_var.set(details_text)
        elif method == "Checksum 16-bit":  # Checksum
            self.detection_method_var.set("Status Checksum:")
            self.detection_status_var.set(status)
            self.detection_status_label.config(foreground=color)
            calc = data.get('calc')
            recv = data.get('recv')
            # Exibe valores hexadecimais do checksum (mais legível)
            details_text = f"Calculado: 0x{calc:04X} ({calc:016b})\nRecebido:  0x{recv:04X} ({recv:016b})"
            self.detection_details_var.set(details_text)    

    def clear_all_for_new_connection(self, address):
        """
        Reinicializa todos os campos e gráficos da GUI para novo ciclo de transmissão.
        Fundamental para manter o isolamento entre execuções/simulações.
        """
        self.connection_status_var.set(f"Conexão de {address}")
        self.connection_status_label.config(foreground='green')
        for var in [self.decode_status_var, self.detection_status_var, self.hamming_status_var,
                    self.received_enquadramento_var, self.received_mod_digital_var,
                    self.received_mod_portadora_var, self.received_detecao_erro_var,
                    self.received_correcao_erro_var, self.received_bit_rate_var,
                    self.received_freq_var, self.received_amplitude_var,
                    self.received_sampling_rate_var, self.received_error_rate_var]:
            var.set("...")
        self.detection_method_var.set("Detecção:")
        self.detection_details_var.set("")

        self.received_message_text.config(state="normal")
        self.received_message_text.delete(1.0, tk.END)
        self.received_message_text.config(state="disabled")

        # Limpa todos os gráficos para a nova rodada.
        for ax, canvas, title in [
            (self.ax_pre, self.canvas_pre, "Sinal RX"),
            (self.ax_post, self.canvas_post, "Bits RX"),
            (self.ax_const_rx, self.canvas_const_rx, "Constelação 16-QAM (RX)")
        ]:
            self.clear_plot_ax(ax, canvas, title)

    def create_status_row(self, parent, row, text, var):
        """
        Cria uma linha composta por um rótulo estático e um dinâmico (StringVar) para exibir status variados.
        Padrão usado para conexão, decodificação e correção de erro.
        """
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=2, pady=1)
        label = ttk.Label(parent, textvariable=var)
        label.grid(row=row, column=1, sticky="w", padx=2, pady=1)
        return label

    def start_listening_thread(self):
        """
        Inicializa a thread de backend responsável por rodar o receptor.
        Mantém a GUI responsiva enquanto o servidor aguarda novas transmissões.
        """
        thread = threading.Thread(target=receptor.run_receiver, args=(self.gui_update_callback,))
        thread.daemon = True
        thread.start()

    def gui_update_callback(self, msg):
        """
        Callback thread-safe para envio de mensagens da thread backend à thread principal (GUI).
        Integração essencial em aplicações multi-thread Tkinter.
        """
        self.update_queue.put(msg)

    def update_status_var(self, label, var, msg):
        """
        Atualiza rótulo de status e sua cor visual conforme mensagem recebida.
        Útil para feedback de eventos como conexão, decodificação e correção de erro.
        """
        var.set(msg['message'])
        label.config(foreground=msg['color'])

    def dispatch_plot(self, tab, data):
        """
        Redireciona o comando de plotagem para a função apropriada, conforme aba ativa.
        Facilita modularização dos tipos de gráficos exibidos na GUI.
        """
        if tab == 'pre_demod':
            self.plot_pre_demod(data)
        elif tab == 'post_demod':
            self.plot_post_demod(data)
        elif tab == 'constellation_rx':
            self.plot_constellation_rx(data)

    def update_received_configs(self, data):
        """
        Atualiza variáveis de configuração da GUI com as informações do transmissor (metadados do experimento).
        Reflete parâmetros reais das camadas Física e Enlace.
        """
        self.received_enquadramento_var.set(data.get("enquadramento_type"))
        self.received_mod_digital_var.set(data.get("mod_digital_type"))
        self.received_mod_portadora_var.set(data.get("mod_portadora_type"))
        self.received_detecao_erro_var.set(data.get("detecao_erro_type"))
        self.received_correcao_erro_var.set(data.get("correcao_erro_type"))
        self.received_bit_rate_var.set(f"{data.get('bit_rate')} bps")
        self.received_freq_var.set(f"{data.get('freq_base')} Hz")
        self.received_amplitude_var.set(f"{data.get('amplitude')} V")
        self.received_sampling_rate_var.set(f"{data.get('sampling_rate')} sps")
        self.received_error_rate_var.set(f"{data.get('taxa_erros'):.3f}")

    def update_received_message(self, message):
        """
        Atualiza
        """
        self.received_message_text.config(state="normal") # Habilita temporariamente a área de texto para edição.
        self.received_message_text.delete(1.0, tk.END) # Limpa qualquer conteúdo existente na área de texto.
        self.received_message_text.insert(tk.END, message) # Insere a nova mensagem decodificada.
        self.received_message_text.config(state="disabled") # Desabilita a área de texto novamente para evitar edição pelo usuário.

if __name__ == '__main__':
    root = tk.Tk() # Cria a janela principal do Tkinter.
    app = ReceptorGUI(root) # Instancia a aplicação GUI do Receptor.
    root.mainloop() # Inicia o loop de eventos do Tkinter, mantendo a GUI em execução e responsiva.