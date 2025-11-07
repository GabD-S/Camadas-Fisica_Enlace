# Simulador/transmissor.py

import socket
import sys
import numpy as np
import time
import logging

# Permite importar módulos de outras pastas do projeto, essenciais para acesso a funcionalidades de cada camada.
sys.path.append('../')

from Utilidades import utils
from CamadaEnlace.deteccao_erros import ErrorDetector
from CamadaEnlace.correcao_erros import ErrorCorrector
from CamadaEnlace.enquadramento import Framer
from CamadaFisica.modulacoes_digitais import DigitalEncoder
from CamadaFisica.modulacoes_portadora import CarrierModulator

# Configurações de rede para simulação local.
HOST = '127.0.0.1'
PORT = 65432

# Logger para rastreamento de execução e diagnóstico.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_log(data_str, max_len=64):
    """
    Trunca strings longas no meio para facilitar visualização em logs.
    Útil para logar grandes sequências de bits de forma legível.
    """
    if len(data_str) > max_len:
        return f"{data_str[:(max_len-3)//2]}...{data_str[-(max_len-3)//2:]}"
    return data_str

def run_transmitter(params):
    """
    Fluxo principal do transmissor: aplica as etapas das camadas do modelo OSI (enlace e física),
    monta a mensagem, gera o sinal, realiza o enquadramento, modula e envia o sinal via TCP.
    Atualiza a interface gráfica em cada etapa para acompanhamento do processo.

    Args:
        params (dict): Parâmetros de configuração (mensagem, tipos de modulação, enquadramento etc),
                       including the 'gui_callback' function.
    """
    # Retrieve the update_callback from params
    update_callback = params.get('gui_callback')
    if not update_callback:
        logger.error("GUI callback function not provided in params. Cannot update GUI.")
        return

    try:
        # --- Extração e definição dos parâmetros básicos da transmissão ---
        config = {
            "message": params.get("message"),
            "bits_raw_input": params.get("bits_raw_input"),
            "enquadramento_type": params.get("enquadramento_type"),
            "mod_digital_type": params.get("mod_digital_type"),
            "mod_portadora_type": params.get("mod_portadora_type"),
            "detecao_erro_type": params.get("detecao_erro_type"),
            "correcao_erro_type": params.get("correcao_erro_type"),
            "taxa_erros": params.get("taxa_erros", 0.0),
            "bit_rate": 1000, # Taxa de bits padrão (Camada Física).
            "freq_base": 5000, # Frequência base da portadora.
            "amplitude": 1.0   # Amplitude do sinal (V).
        }
        config["sampling_rate"] = config["bit_rate"] * 20  # Oversampling para representação realista do sinal.
        samples_per_bit = config["sampling_rate"] // config["bit_rate"]

        # Instanciação dos objetos das camadas.
        error_detector = ErrorDetector()
        error_corrector = ErrorCorrector()
        framer = Framer()
        digital_encoder = DigitalEncoder()
        modulator = CarrierModulator(config["bit_rate"], config["freq_base"], config["amplitude"], config["sampling_rate"])

        update_callback({'type': 'status', 'message': "--- INÍCIO DA TRANSMISSÃO ---", 'color': 'black'})
        logger.info("--- INÍCIO DA TRANSMISSÃO ---")

        # --- Camadas Superiores: Conversão para bits (Camada Aplicação/Apresentação) ---
        if config.get('bits_raw_input') is not None:
            bits = config['bits_raw_input']
            config['original_message_len_bits'] = len(bits)
            logger.info(f"1. (App) Mensagem original (binário puro): {format_log(bits)}")
            update_callback({'type': 'log', 'message': f"1. (App) Mensagem original (binário puro): {len(bits)} bits"})
        else:
            bits = utils.text_to_binary(config['message'])
            config['original_message_len_bits'] = len(bits)
            logger.info(f"1. (App) Mensagem original em bits (ASCII): {format_log(bits)}")
            update_callback({'type': 'log', 'message': f"1. (App) Mensagem original (ASCII): {len(bits)} bits"})

        # --- Camada de Enlace: Detecção de erros (CRC-32, Paridade) ---
        detecao_selecionada = config["detecao_erro_type"]
        payload_com_detecao = bits
        if detecao_selecionada == "CRC-32":
            # Adiciona CRC-32 ao final dos dados.
            crc = error_detector.generate_crc(bits)
            payload_com_detecao = bits + crc
            logger.info(f"2. (Enlace) Adicionado CRC-32. Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionado CRC-32. Total: {len(payload_com_detecao)} bits."})
        elif detecao_selecionada == "Paridade Par":
            # Aplica esquema 7+1 bits, adicionando bits de paridade a cada 7 bits.
            padding_needed = (7 - len(bits) % 7) % 7
            bits_alinhados = bits + '0' * padding_needed 
            bytes_com_paridade = [error_detector.add_even_parity(bits_alinhados[i:i+7]) for i in range(0, len(bits_alinhados), 7)]
            payload_com_detecao = "".join(bytes_com_paridade)
            logger.info(f"2. (Enlace) Adicionada Paridade Par (esquema 7+1). Payload agora com {len(payload_com_detecao)} bits.")
            update_callback({'type': 'log', 'message': f"2. (Enlace) Adicionada Paridade Par. Total: {len(payload_com_detecao)} bits."})

        # --- Camada de Enlace: Correção de erros (Hamming) ---
        correcao_selecionada = config["correcao_erro_type"]
        if correcao_selecionada == "Hamming":
            bits_para_enlace = error_corrector.encode_hamming(payload_com_detecao)
            logger.info(f"3. (Enlace) Aplicado Hamming. Payload agora com {len(bits_para_enlace)} bits.")
            update_callback({'type': 'log', 'message': f"3. (Enlace) Aplicado Hamming. Total: {len(bits_para_enlace)} bits."})
        else:
            bits_para_enlace = payload_com_detecao

        # Define o payload antes do enquadramento (que é o que vem depois de CRC/Hamming)
        payload_before_framing = bits_para_enlace 
        #  Print no terminal antes do enquadramento ---
        logger.info(f"DEBUG: Enquadramento - Dados ANTES: {format_log(payload_before_framing)} (len={len(payload_before_framing)})")
        # ------------------------------------------------------

        # Camada de Enlace: Enquadramento (Byte/Bit Stuffing ou Contagem de Caracteres) ---
        enquadramento_selecionado = config["enquadramento_type"]
        frame_final_apos_enquadramento = "" # Initialize variable

        if enquadramento_selecionado == "Contagem de caracteres":
            frame_final_apos_enquadramento = framer.frame_char_count(bits_para_enlace)
        elif enquadramento_selecionado == "Byte Stuffing (Flags)":
            frame_final_apos_enquadramento = framer.frame_byte_stuffing(bits_para_enlace)
        else: # Assumed "Bit Stuffing (Flags)"
            frame_final_apos_enquadramento = framer.frame_bit_stuffing(bits_para_enlace)
        
        logger.info(f"4. (Enlace) Enquadramento '{enquadramento_selecionado}' aplicado. Frame agora com {len(frame_final_apos_enquadramento)} bits.")
        update_callback({'type': 'log', 'message': f"4. (Enlace) Enquadramento aplicado. Frame: {len(frame_final_apos_enquadramento)} bits."})

        # --- NOVO: Print no terminal DEPOIS do enquadramento ---
        logger.info(f"DEBUG: Enquadramento - Dados DEPOIS: {format_log(frame_final_apos_enquadramento)} (len={len(frame_final_apos_enquadramento)})")
        # -------------------------------------------------------

        # Envia os dados do quadro para a GUI para TODOS os tipos de enquadramento
        update_callback({
            'type': 'frame_display',
            'data': {
                'payload_before_stuffing': payload_before_framing, # Usando a chave antiga para compatibilidade com a GUI
                'frame_after_stuffing': frame_final_apos_enquadramento # Usando a chave antiga para compatibilidade com a GUI
            }
        })

        # --- Camada Física: Padding para 8-QAM ---
        mod_portadora = config["mod_portadora_type"]
        frame_for_physical_layer = frame_final_apos_enquadramento # Use the framed data for physical layer
        if mod_portadora == "8-QAM":
            padding_needed = len(frame_for_physical_layer) % 3
            if padding_needed != 0:
                qam_pad = 3 - padding_needed
                frame_for_physical_layer += '0' * qam_pad
                logger.info(f"(Pós-Enquadramento) Adicionado {qam_pad} bits de padding para alinhar o frame final com 8-QAM.")
            else:
                qam_pad = 0
            config["qam_pad"] = qam_pad
        else:
            config["qam_pad"] = 0
        config['original_payload_len'] = len(frame_for_physical_layer) # This now includes framing and QAM padding

        # --- Camada Física: Codificação Digital (Codificação de Linha) ---
        digital_signal_plot = digital_encoder.encode(frame_for_physical_layer, config["mod_digital_type"], samples_per_bit)
        logger.info("5. (Física) Codificação de linha gerada para visualização.")
        update_callback({'type': 'log', 'message': f"5. (Física) Codificação de linha aplicada: {config['mod_digital_type']}."})

        update_callback({'type': 'plot_digital', 'data': {
            't': np.arange(len(digital_signal_plot)) / config["sampling_rate"],
            'signal': digital_signal_plot,
            'config': config
        }})
        
        # --- Camada Física: Modulação por Portadora ---
        logger.info(f"6. (Física) Preparando para modular com {mod_portadora}.")
        if mod_portadora == "ASK":
            # ASK: bit 1 vira pulso, bit 0 vira ausência de pulso (amplitude).
            signal_source = np.array([1.0 if b == '1' else 0.0 for b in frame_for_physical_layer])
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)
        elif mod_portadora == "FSK":
            # FSK: bit 1 vira onda de uma frequência, bit 0 de outra.
            signal_source = np.array([1.0 if b == '1' else -1.0 for b in frame_for_physical_layer])
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)
        elif mod_portadora == "Nenhum":
            signal_source_for_analog = digital_signal_plot
            t_analog = np.arange(len(signal_source_for_analog)) / config["sampling_rate"]
            analog_signal = signal_source_for_analog
            qam_points = []
        else:  # 8-QAM ou outros
            signal_source = frame_for_physical_layer
            t_analog, analog_signal, *qam_points = modulator.modulate(signal_source, mod_portadora)

        update_callback({'type': 'plot_analog', 'data': {'t': t_analog, 'signal': analog_signal, 'config': config}})
        if qam_points:
            update_callback({'type': 'plot_constellation', 'data': {'points': qam_points[0]}})
        
        # --- Transmissão via Socket (Camada Física: Meio) ---
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Metadados enviados antes do sinal para configurar o receptor.
            final_metadata_str = (
                f"{config['message']}|"
                f"{config['enquadramento_type']}|"
                f"{config['mod_digital_type']}|"
                f"{config['mod_portadora_type']}|"
                f"{config['detecao_erro_type']}|"
                f"{config['correcao_erro_type']}|"
                f"{config['taxa_erros']}|"
                f"{config['bit_rate']}|"
                f"{config['freq_base']}|"
                f"{config['amplitude']}|"
                f"{config['sampling_rate']}|"
                f"{config['original_payload_len']}|"
                f"{config['qam_pad']}|"
                f"{config['original_message_len_bits']}"
            )
            s.sendall(final_metadata_str.encode('utf-8'))
            time.sleep(0.1) # Garante ordem de recebimento (primeiro metadados, depois o sinal).

            logger.info(f"DEBUG: Transmissor - Tamanho do analog_signal antes de enviar: {len(analog_signal)} amostras")
            logger.info(f"DEBUG: Transmissor - Total de bytes a enviar: {len(analog_signal.astype(np.float32).tobytes())} bytes")

            # Envia sinal modulado para o receptor, convertido para float32 em bytes.
            s.sendall(analog_signal.astype(np.float32).tobytes())
            logger.info("7. (Física) Sinal transmitido via socket.")
            update_callback({'type': 'status', 'message': 'Transmissão concluída!', 'color': 'green'})

    except Exception as e:
        # Captura falhas críticas e atualiza interface.
        logger.error(f"Erro crítico no transmissor: {e}", exc_info=True)
        update_callback({'type': 'status', 'message': f"Erro crítico: {e}", 'color': 'red'})