import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ajustável conforme nível desejado (DEBUG, INFO, etc.)

class Framer:
    """Gerencia técnicas de enquadramento na Camada de Enlace:
    - Contagem de caracteres
    - Byte stuffing
    - Bit stuffing
    """

    FLAG_BIT_PATTERN = "01111110"  # Delimitador de quadro padrão HDLC (bit stuffing)
    FLAG_BYTE = 0x7E               # FLAG em formato de byte (126 decimal)
    ESC_BYTE = 0x7D                # Byte de escape (125 decimal)

    def frame_char_count(self, payload_bits):
        """Enquadra dados inserindo cabeçalho com a quantidade de bytes do payload.
        Método simples, porém vulnerável: um erro no cabeçalho pode comprometer toda a recepção."""
        logger.debug(f"frame_char_count: entrada payload_bits len={len(payload_bits)}")
        if len(payload_bits) % 8 != 0:
            padding = 8 - (len(payload_bits) % 8)
            payload_bits += '0' * padding  # Alinhamento para múltiplo de 8 bits
            logger.debug(f"frame_char_count: padding de {padding} bits adicionado")

        num_bytes = len(payload_bits) // 8
        if num_bytes > 255:
            logger.error("frame_char_count: Payload excede máximo de 255 bytes")
            raise ValueError("Payload excede o tamanho máximo de 255 bytes.")

        header = format(num_bytes, '08b')
        frame = header + payload_bits
        logger.debug(f"frame_char_count: saída frame len={len(frame)}")
        return frame

    def deframe_char_count(self, frame_bits):
        """Extrai payload usando o cabeçalho de contagem de caracteres.
        Depende da integridade do cabeçalho para determinar corretamente o payload."""
        logger.debug(f"deframe_char_count: entrada frame_bits len={len(frame_bits)}")
        header_bits = frame_bits[:8]
        payload_len_in_bytes = int(header_bits, 2)
        payload_len_in_bits = payload_len_in_bytes * 8

        payload = frame_bits[8 : 8 + payload_len_in_bits]
        remaining_frame = frame_bits[8 + payload_len_in_bits:]
        logger.debug(f"deframe_char_count: payload len={len(payload)}, restante len={len(remaining_frame)}")
        return payload, remaining_frame

    def frame_byte_stuffing(self, payload_bits):
        """Aplica byte stuffing, técnica que evita confusão entre dados e caracteres especiais (FLAG e ESC).
        Insere byte de escape (ESC) antes de caracteres especiais no payload."""
        logger.debug(f"frame_byte_stuffing: entrada payload_bits len={len(payload_bits)}")
        padding_needed = len(payload_bits) % 8
        if padding_needed != 0:
            num_zeros_to_add = 8 - padding_needed
            payload_bits += '0' * num_zeros_to_add  # Completa último byte
            logger.debug(f"frame_byte_stuffing: {num_zeros_to_add} bits adicionados para alinhamento")

        payload_bytes = [int(payload_bits[i:i+8], 2) for i in range(0, len(payload_bits), 8)]
        logger.debug(f"frame_byte_stuffing: convertido em {len(payload_bytes)} bytes")

        stuffed_payload = []
        for byte in payload_bytes:
            if byte in (self.FLAG_BYTE, self.ESC_BYTE):
                stuffed_payload.append(self.ESC_BYTE)  # Insere escape antes do byte especial
                logger.debug(f"frame_byte_stuffing: byte {byte:#04x} escapado")
            stuffed_payload.append(byte)

        final_frame_bytes = [self.FLAG_BYTE] + stuffed_payload + [self.FLAG_BYTE]
        frame_bits = "".join(format(byte, '08b') for byte in final_frame_bytes)
        logger.debug(f"frame_byte_stuffing: saída frame_bits len={len(frame_bits)}")
        return frame_bits

    def deframe_byte_stuffing(self, frame_bits):
        """Remove enquadramento de byte stuffing.
        Verifica presença das FLAGs inicial e final, remove caracteres ESC usados para diferenciar dados reais de caracteres especiais."""
        logger.debug(f"deframe_byte_stuffing: entrada frame_bits len={len(frame_bits)}")

        if len(frame_bits) % 8 != 0:
            logger.error("deframe_byte_stuffing: comprimento do quadro inválido")
            return None, "Erro: comprimento inválido (não múltiplo de 8)."
        if not (frame_bits.startswith(self.FLAG_BIT_PATTERN) and frame_bits.endswith(self.FLAG_BIT_PATTERN)):
            logger.error("deframe_byte_stuffing: flags ausentes ou inválidas")
            return None, "Erro: flags ausentes ou inválidas."

        frame_bytes = [int(frame_bits[i:i+8], 2) for i in range(0, len(frame_bits), 8)]
        payload_with_stuffing = frame_bytes[1:-1]
        destuffed_payload = []
        is_escaped = False

        for i, byte in enumerate(payload_with_stuffing):
            if is_escaped:
                destuffed_payload.append(byte)
                is_escaped = False
                logger.debug(f"deframe_byte_stuffing: byte escapado {byte:#04x} no índice {i}")
            elif byte == self.ESC_BYTE:
                is_escaped = True
                logger.debug(f"deframe_byte_stuffing: ESC encontrado no índice {i}")
            else:
                destuffed_payload.append(byte)

        if is_escaped:
            logger.error("deframe_byte_stuffing: ESC no final do quadro")
            return None, "Erro: ESC no final do quadro."

        payload_destuffed_bits = "".join(format(byte, '08b') for byte in destuffed_payload)
        logger.debug(f"deframe_byte_stuffing: payload destuffed len={len(payload_destuffed_bits)} bits")
        return payload_destuffed_bits, "OK"

    def frame_bit_stuffing(self, payload_bits):
        """Aplica bit stuffing: técnica utilizada em protocolos HDLC/PPP para evitar que o padrão delimitador (FLAG) apareça no payload.
        Insere um '0' após sequência de cinco bits '1' consecutivos."""
        stuffed_payload = payload_bits.replace('11111', '111110')
        return self.FLAG_BIT_PATTERN + stuffed_payload + self.FLAG_BIT_PATTERN

    def deframe_bit_stuffing(self, frame_bits):
        """Remove bit stuffing retirando o '0' inserido após cinco bits '1' consecutivos.
        Verifica presença correta das FLAGS delimitadoras."""
        if not (frame_bits.startswith(self.FLAG_BIT_PATTERN) and frame_bits.endswith(self.FLAG_BIT_PATTERN)):
            logger.error("deframe_bit_stuffing: flags não encontradas")
            return None, "Erro: Flags não encontradas."

        stuffed_payload = frame_bits[len(self.FLAG_BIT_PATTERN):-len(self.FLAG_BIT_PATTERN)]
        destuffed_payload = stuffed_payload.replace('111110', '11111')
        return destuffed_payload, "OK"
