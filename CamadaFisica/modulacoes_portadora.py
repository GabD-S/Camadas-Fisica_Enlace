# CamadaFisica/modulacoes_portadora.py

import numpy as np
import math

class CarrierModulator:
    """
    Implementa diferentes esquemas de modulação por portadora (ASK, FSK, 8-QAM).
    Atua na Camada Física, convertendo sinais digitais em formas de onda analógicas
    apropriadas para transmissão através de um canal de comunicação.
    """

    def __init__(self, bit_rate, carrier_freq, amplitude, sampling_rate):
        """
        Inicializa os parâmetros fundamentais para a modulação e demodulação da portadora.

        Args:
            bit_rate (int): Taxa de bits (bits por segundo - bps).
            carrier_freq (int): Frequência da onda portadora (Hertz - Hz).
            amplitude (float): Amplitude máxima do sinal modulado (Volts).
            sampling_rate (int): Taxa de amostragem do sinal (amostras por segundo - Hz).
        """
        self.bit_rate = bit_rate
        self.carrier_freq = carrier_freq
        self.amplitude = amplitude
        self.sampling_rate = sampling_rate
        # Calcula o número de amostras por bit para reconstrução precisa da forma de onda.
        self.samples_per_bit = int(sampling_rate / bit_rate)

        # Mapeamento da constelação 8-QAM: associa cada símbolo de 3 bits a um ponto complexo (I, Q).
        # Estes pontos definem as combinações de amplitude e fase.
        self.QAM8_MAP = {
            '000': complex(1, 0),
            '001': complex(0, 1),
            '010': complex(-1, 0),
            '011': complex(0, -1),
            '100': complex(1/np.sqrt(2), 1/np.sqrt(2)),
            '101': complex(1/np.sqrt(2), -1/np.sqrt(2)),
            '110': complex(-1/np.sqrt(2), 1/np.sqrt(2)),
            '111': complex(-1/np.sqrt(2), -1/np.sqrt(2)),
        }
        # Cria um mapeamento reverso para facilitar a busca do símbolo de bits durante a demodulação.
        self.INV_QAM8_MAP = {v: k for k, v in self.QAM8_MAP.items()}

    def modulate(self, signal_source, modulation_type):
        """
        Método de despacho para selecionar e aplicar o tipo de modulação por portadora desejado.
        
        Args:
            signal_source: O sinal de entrada para a modulação (array NumPy para ASK/FSK, string de bits para 8-QAM).
            modulation_type (str): O nome do esquema de modulação a ser aplicado (ex: "ASK", "FSK", "8-QAM", "Nenhum").
            
        Returns:
            tuple: Uma tupla contendo o eixo de tempo (t), o sinal analógico modulado, e uma lista de pontos da constelação (vazia para ASK/FSK).
        
        Raises:
            ValueError: Se o tipo de modulação especificado for desconhecido.
        """
        if modulation_type == "ASK":
            return self.modulate_ask(signal_source)
        elif modulation_type == "FSK":
            return self.modulate_fsk(signal_source)
        elif modulation_type == "8-QAM":
            return self.modulate_8qam(signal_source)
        elif modulation_type == "Nenhum": # NOVO: Caso a modulação por portadora seja "Nenhum"
            # Se não há modulação de portadora, o sinal "analógico" é o próprio sinal digital em banda base.
            # O `signal_source` aqui já deve ser uma forma de onda digital (array NumPy de +1.0/-1.0).
            num_samples = len(signal_source)
            t = np.arange(num_samples) / self.sampling_rate # Eixo de tempo para o sinal digital.
            return t, signal_source, [] # Retorna o sinal digital como se fosse o analógico, sem pontos QAM.
        else:
            raise ValueError(f"Tipo de modulação desconhecido: {modulation_type}")

    def modulate_ask(self, digital_signal):
        """
        Aplica a modulação ASK (Amplitude Shift Keying).
        Neste esquema, a amplitude da onda portadora é variada de acordo com o valor do bit:
        Bit '1' → onda com amplitude máxima (self.amplitude); Bit '0' → sinal nulo (amplitude zero).
        
        Args:
            digital_signal (np.array): O sinal digital em banda base (array de 0.0s e 1.0s).
            
        Returns:
            tuple: Eixo de tempo (t), o sinal ASK modulado, e uma lista vazia de pontos de constelação.
        """
        num_bits = len(digital_signal)
        # Cria um eixo de tempo contínuo para o sinal analógico, baseado na taxa de amostragem.
        t = np.linspace(0, num_bits / self.bit_rate, num_bits * self.samples_per_bit, endpoint=False)

        # Repete os níveis do sinal digital para corresponder ao número de amostras por bit e escala pela amplitude.
        amplitude_signal = np.repeat(digital_signal * self.amplitude, self.samples_per_bit)
        carrier = np.sin(2 * np.pi * self.carrier_freq * t) # Gera a onda portadora senoidal.
        modulated = amplitude_signal * carrier  # Modula a amplitude da portadora com o sinal digital.
        return t, modulated, []  # ASK não possui diagrama de constelação convencional.

    def modulate_fsk(self, digital_signal):
        """
        Aplica a modulação FSK (Frequency Shift Keying).
        Neste esquema, a frequência da onda portadora é alternada para representar os bits:
        Bit '1' → uma frequência (f1); Bit '0' → outra frequência (f0).
        
        Args:
            digital_signal (np.array): O sinal digital em banda base (array de -1.0s e 1.0s).
            
        Returns:
            tuple: Eixo de tempo (t), o sinal FSK modulado, e uma lista vazia de pontos de constelação.
        """
        num_bits = len(digital_signal)
        # Cria um eixo de tempo contínuo para o sinal analógico.
        t = np.linspace(0, num_bits / self.bit_rate, num_bits * self.samples_per_bit, endpoint=False)

        f_dev = self.bit_rate  # Define o desvio de frequência para as duas frequências FSK.
        f1 = self.carrier_freq + f_dev # Frequência para representar o bit '1'.
        f0 = self.carrier_freq - f_dev # Frequência para representar o bit '0'.

        modulated = np.zeros_like(t) # Inicializa o array do sinal modulado com zeros.
        for i, level in enumerate(digital_signal): # Itera sobre cada bit do sinal digital.
            start_sample = i * self.samples_per_bit # Amostra de início para o período do bit atual.
            end_sample = (i + 1) * self.samples_per_bit # Amostra de fim para o período do bit atual.
            freq_to_use = f1 if level == 1 else f0 # Seleciona a frequência com base no valor do bit.
            # Gera o segmento de onda senoidal para o bit atual e o adiciona ao sinal modulado.
            modulated[start_sample:end_sample] = self.amplitude * np.sin(2 * np.pi * freq_to_use * t[start_sample:end_sample])
        return t, modulated, []  # FSK também não possui diagrama de constelação convencional.

    def modulate_8qam(self, bits):
        """
        Aplica a modulação 8-QAM (Quadrature Amplitude Modulation).
        Este esquema modula simultaneamente a amplitude e a fase da portadora.
        Cada grupo de 3 bits é mapeado para um ponto específico (I, Q) na constelação.
        
        Args:
            bits (str): A string de bits a ser modulada.
            
        Returns:
            tuple: Eixo de tempo (t), o sinal 8-QAM modulado, e a lista de pontos da constelação gerados.
        """
        # Adiciona bits de padding se o comprimento total não for um múltiplo de 3 (para formar símbolos completos).
        if len(bits) % 3 != 0:
            bits += '0' * (3 - len(bits) % 3)

        # Divide a string de bits em símbolos de 3 bits.
        symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]
        # Mapeia cada símbolo de 3 bits para seu ponto complexo (I, Q) na constelação.
        qam_points = [self.QAM8_MAP.get(s, complex(0, 0)) for s in symbols]

        # Calcula o número de amostras por símbolo (3 bits por símbolo * amostras por bit).
        samples_per_symbol = self.samples_per_bit * 3
        # Cria o eixo de tempo para o sinal modulado, abrangendo todos os símbolos.
        t = np.linspace(0, len(symbols) * 3 / self.bit_rate, len(symbols) * samples_per_symbol, endpoint=False)
        modulated = np.zeros(len(t)) # Inicializa o array do sinal modulado.

        for i, point in enumerate(qam_points): # Itera sobre cada ponto (símbolo) da constelação.
            start_sample = i * samples_per_symbol # Amostra de início para o símbolo atual.
            end_sample = (i + 1) * samples_per_symbol # Amostra de fim para o símbolo atual.
            # Calcula as componentes em fase (I) e em quadratura (Q) escaladas pela amplitude.
            i_comp = point.real * self.amplitude
            q_comp = point.imag * self.amplitude

            # Gera as portadoras ortogonais (cosseno para I, seno para Q) para o segmento de tempo atual.
            cos_carrier = np.cos(2 * np.pi * self.carrier_freq * t[start_sample:end_sample])
            sin_carrier = np.sin(2 * np.pi * self.carrier_freq * t[start_sample:end_sample])
            # Combina as componentes I e Q com suas portadoras para formar o sinal 8-QAM.
            modulated[start_sample:end_sample] = i_comp * cos_carrier - q_comp * sin_carrier
        return t, modulated, qam_points # Retorna o sinal, o eixo de tempo e os pontos da constelação.

    def demodulate(self, received_signal, modulation_type, config, digital_encoder_instance):
        """
        Método de despacho para selecionar e aplicar o tipo de demodulação correspondente à modulação original.
        
        Args:
            received_signal (np.array): O sinal recebido do canal (com ruído, se aplicável).
            modulation_type (str): O tipo de modulação de portadora que foi originalmente usada (ex: "ASK", "FSK", "8-QAM", "Nenhum").
            config (dict): Dicionário de configurações da transmissão, necessário para parâmetros de demodulação.
            digital_encoder_instance (DigitalEncoder): Uma instância do DigitalEncoder para reconstruir a forma de onda digital.
            
        Returns:
            tuple: Uma tupla contendo a string de bits demodulados, o sinal digital reconstruído (forma de onda), e o eixo de tempo para este sinal.
            
        Raises:
            ValueError: Se o tipo de demodulação especificado for desconhecido.
        """
        if modulation_type == "ASK":
            return self._demodulate_ask(received_signal, config, digital_encoder_instance)
        elif modulation_type == "FSK":
            return self._demodulate_fsk(received_signal, config, digital_encoder_instance)
        elif modulation_type == "8-QAM":
            # Demodula 8-QAM e retorna os bits, o sinal digital reconstruído e, **os pontos da constelação ruidosa**.
            return self._demodulate_8qam(received_signal, config, digital_encoder_instance)
        elif modulation_type == "Nenhum": # Caso a modulação por portadora seja "Nenhum"
            # Se não houve modulação de portadora, o sinal recebido já é o sinal digital em banda base.
            # O objetivo aqui é reamostrar e converter esse sinal digital de volta para a string de bits.
            samples_per_bit = int(config["sampling_rate"] / config["bit_rate"])
            num_bits = len(received_signal) // samples_per_bit
            
            bits_str = ""
            for i in range(num_bits):
                # Amostra o sinal no meio de cada período de bit para determinar o valor do bit.
                sample_index = i * samples_per_bit + samples_per_bit // 2
                if sample_index < len(received_signal): # Garante que o índice esteja dentro dos limites.
                    val = received_signal[sample_index]
                    bits_str += '1' if val > 0 else '0' # Determina o bit (1 para positivo, 0 para negativo/zero).
                else: # Em caso de sinal truncado, assume '0' para bits faltantes.
                    bits_str += '0' 
            
            # Reconstrói a forma de onda digital (codificação de linha) usando o DigitalEncoder
            # com os bits recuperados e o tipo de modulação digital original.
            digital_signal_rx = digital_encoder_instance.encode(bits_str, config['mod_digital_type'], samples_per_bit)
            t_digital = np.arange(len(digital_signal_rx)) / config["sampling_rate"] # Eixo de tempo para a forma de onda reconstruída.
            # NOVO: Retorna uma lista vazia para os pontos de constelação ruidosa, pois não há constelação para "Nenhum".
            return bits_str, digital_signal_rx, t_digital, [] 
        else:
            raise ValueError(f"Tipo de demodulação desconhecido: {modulation_type}")

    def _demodulate_ask(self, received_signal, config, digital_encoder_instance):
        """
        Realiza a demodulação coerente de ASK.
        O sinal recebido é correlacionado com uma portadora local para determinar
        a amplitude e, consequentemente, o bit transmitido (comparação com limiar).
        
        Args:
            received_signal (np.array): O sinal modulado ASK recebido.
            config (dict): Configurações da transmissão.
            digital_encoder_instance (DigitalEncoder): Instância para reconstruir o sinal digital.
            
        Returns:
            tuple: String de bits demodulados, forma de onda digital reconstruída e seu eixo de tempo.
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq_base = config['freq_base']
        mod_digital_type = config.get('mod_digital_type', 'NRZ-Polar')

        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received_signal) // samples_per_bit
        t_bit_period = np.linspace(0, 1 / bit_rate, samples_per_bit, endpoint=False) # Eixo de tempo para um período de bit.
        local_carrier = np.sin(2 * np.pi * freq_base * t_bit_period) # Portadora local para correlação.

        # Limiar de decisão para ASK: metade da energia do sinal de um '1' (assumindo OOK).
        threshold = self.amplitude * np.sum(local_carrier * local_carrier) / 2.0 

        bits = "" # String para armazenar os bits demodulados.
        for i in range(num_bits): # Processa o sinal segmento por segmento, um para cada bit.
            segment = received_signal[i * samples_per_bit : (i + 1) * samples_per_bit]
            correlation = np.sum(segment * local_carrier) # Calcula a correlação do segmento com a portadora local.
            bits += '1' if correlation > threshold else '0' # Decide o bit com base no limiar.

        # Reconstrói a forma de onda digital (codificação de linha) usando os bits recuperados.
        digital_signal_rx = digital_encoder_instance.encode(bits, mod_digital_type, samples_per_bit)
        t_digital = np.arange(len(digital_signal_rx)) / sampling_rate # Eixo de tempo para a forma de onda reconstruída.
        # NOVO: Retorna uma lista vazia para os pontos de constelação ruidosa, pois ASK não tem constelação.
        return bits, digital_signal_rx, t_digital, [] 

    def _demodulate_fsk(self, received_signal, config, digital_encoder_instance):
        """
        Realiza a demodulação coerente de FSK.
        O sinal recebido é correlacionado com duas portadoras locais (para '0' e '1').
        O bit é determinado pela portadora com maior correlação.
        
        Args:
            received_signal (np.array): O sinal modulado FSK recebido.
            config (dict): Configurações da transmissão.
            digital_encoder_instance (DigitalEncoder): Instância para reconstruir o sinal digital.
            
        Returns:
            tuple: String de bits demodulados, forma de onda digital reconstruída e seu eixo de tempo.
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq_base = config['freq_base']
        mod_digital_type = config.get('mod_digital_type', 'NRZ-Polar')

        samples_per_bit = int(sampling_rate / bit_rate)
        num_bits = len(received_signal) // samples_per_bit
        t_bit_period = np.linspace(0, 1 / bit_rate, samples_per_bit, endpoint=False) # Eixo de tempo para um período de bit.

        f_dev = bit_rate # Desvio de frequência utilizado para as portadoras FSK.
        f1 = freq_base + f_dev # Frequência para o bit '1'.
        f0 = freq_base - f_dev # Frequência para o bit '0'.
        local_carrier_1 = np.sin(2 * np.pi * f1 * t_bit_period) # Portadora local para '1'.
        local_carrier_0 = np.sin(2 * np.pi * f0 * t_bit_period) # Portadora local para '0'.

        bits = "" # String para armazenar os bits demodulados.
        for i in range(num_bits): # Processa o sinal segmento por segmento.
            segment = received_signal[i * samples_per_bit : (i + 1) * samples_per_bit]
            correlation_1 = np.sum(segment * local_carrier_1) # Correlação com portadora '1'.
            correlation_0 = np.sum(segment * local_carrier_0) # Correlação com portadora '0'.
            bits += '1' if correlation_1 > correlation_0 else '0' # Decide o bit com base na maior correlação.

        # Reconstrói a forma de onda digital (codificação de linha) usando os bits recuperados.
        digital_signal_rx = digital_encoder_instance.encode(bits, mod_digital_type, samples_per_bit)
        t_digital = np.arange(len(digital_signal_rx)) / sampling_rate # Eixo de tempo para a forma de onda reconstruída.
        # NOVO: Retorna uma lista vazia para os pontos de constelação ruidosa, pois FSK não tem constelação.
        return bits, digital_signal_rx, t_digital, [] 

    def _demodulate_8qam(self, received_signal, config, digital_encoder_instance):
        """
        Realiza a demodulação coerente de 8-QAM.
        O sinal recebido é projetado nas portadoras I e Q, e o ponto resultante é
        comparado com os pontos da constelação original para determinar o símbolo.
        
        Args:
            received_signal (np.array): O sinal modulado 8-QAM recebido.
            config (dict): Configurações da transmissão.
            digital_encoder_instance (DigitalEncoder): Instância para reconstruir o sinal digital.
            
        Returns:
            tuple: String de bits demodulados, forma de onda digital reconstruída, seu eixo de tempo,
                   e a lista de pontos de constelação recebidos (com ruído).
        """
        bit_rate = config['bit_rate']
        sampling_rate = config['sampling_rate']
        freq_base = config['freq_base']
        samples_per_symbol = int(sampling_rate / bit_rate) * 3 # Amostras por símbolo (3 bits/símbolo).
        num_symbols = len(received_signal) // samples_per_symbol # Número total de símbolos no sinal.

        bits = "" # String para armazenar os bits demodulados.
        received_qam_points = [] # NOVO: Lista para armazenar os pontos da constelação com ruído.

        for i in range(num_symbols): # Processa o sinal símbolo por símbolo.
            start_sample = i * samples_per_symbol
            end_sample = (i + 1) * samples_per_symbol
            segment = received_signal[start_sample:end_sample]
            if len(segment) < samples_per_symbol: # Verifica se o segmento está completo.
                break # Sai do loop se o último segmento estiver incompleto.

            t_segment = np.linspace(i * 3 / bit_rate, (i + 1) * 3 / bit_rate, samples_per_symbol, endpoint=False) # Eixo de tempo para o segmento.
            # Portadoras locais ortogonais para projeção I e Q.
            local_cos_carrier = np.cos(2 * np.pi * freq_base * t_segment)
            local_sin_carrier = np.sin(2 * np.pi * freq_base * t_segment)

            # Projeção do sinal recebido nas componentes I e Q.
            i_component = np.sum(segment * local_cos_carrier)
            q_component = np.sum(segment * -local_sin_carrier) # Note o sinal negativo para a componente Q.
            
            # Normalização das componentes I e Q pela energia da portadora (assumindo portadoras de amplitude 1).
            normalization_factor = self.amplitude * np.sum(local_cos_carrier**2) # Energia da portadora.
            received_point = complex(i_component / normalization_factor, q_component / normalization_factor) if normalization_factor > 1e-9 else 0j
            received_qam_points.append(received_point) # NOVO: Adiciona o ponto recebido (com ruído) à lista.
            
            # Encontra o ponto da constelação mais próximo do ponto recebido (detecção por distância mínima).
            closest_constellation_point = min(self.QAM8_MAP.values(), key=lambda c_point: abs(received_point - c_point))
            bits += self.INV_QAM8_MAP[closest_constellation_point] # Converte o ponto da constelação de volta para bits.

        # Garante que o tamanho final da string de bits não exceda o comprimento original esperado do payload.
        expected_len = config.get('original_payload_len', len(bits))
        bits = bits[:expected_len]

        mod_digital_type = config.get('mod_digital_type', 'NRZ-Polar')
        # Reconstrói a forma de onda digital (codificação de linha) usando os bits recuperados.
        digital_signal_rx = digital_encoder_instance.encode(bits, mod_digital_type, self.samples_per_bit)
        t_digital = np.arange(len(digital_signal_rx)) / sampling_rate # Eixo de tempo para a forma de onda reconstruída.
        
        # ALTERAÇÃO: Agora retorna a lista de pontos de constelação ruidosa também.
        return bits, digital_signal_rx, t_digital, received_qam_points