class ErrorDetector:
    """
    Implementa métodos de detecção de erros na Camada de Enlace.
    Inclui Paridade Par (detecta 1 bit de erro) e CRC-32 (detecta erros em rajada).
    """

    def __init__(self):
        # Polinômio CRC-32 padrão IEEE 802.3 (Ethernet), sem o bit mais significativo implícito (x^32)
        self.CRC32_POLY = 0x104C11DB7

    def add_even_parity(self, bit_chunk):
        """
        Aplica paridade par adicionando 1 bit ao final, garantindo quantidade par de bits '1'.
        Detecta erro simples (1 bit) na recepção.
        """
        return bit_chunk + ('1' if bit_chunk.count('1') % 2 != 0 else '0')

    def check_even_parity(self, chunk_with_parity):
        """
        Verifica se a paridade par está correta.
        Retorna True se não houver erro ou False caso detecte erro simples.
        """
        return chunk_with_parity.count('1') % 2 == 0

    def _crc_division_engine(self, data_bits_str, poly_bits_str):
        """
        Realiza divisão polinomial binária (modulo-2) utilizando XOR.
        Coração do cálculo/verificação do CRC.
        """
        poly = list(map(int, poly_bits_str))
        data = list(map(int, data_bits_str))
        n = len(poly)

        # Percorre bits dos dados aplicando XOR com o polinômio quando encontrar bit '1'
        for i in range(len(data) - n + 1):
            if data[i] == 1:
                for j in range(n):
                    data[i + j] ^= poly[j]

        # Retorna o resto da divisão (CRC) em formato binário
        remainder = "".join(map(str, data[-(n - 1):]))
        return remainder

    def generate_crc(self, data_bits):
        """
        Gera CRC-32 dos dados binários informados (para transmissão).
        """
        poly_bits = bin(self.CRC32_POLY)[2:]  # Polinômio em binário
        num_poly_bits = len(poly_bits)

        # Adiciona zeros no final para cálculo CRC (padding)
        padded_data = data_bits + '0' * (num_poly_bits - 1)

        # Calcula resto da divisão polinomial (CRC)
        remainder = self._crc_division_engine(padded_data, poly_bits)

        # Retorna CRC ajustado para o tamanho correto
        return remainder.zfill(num_poly_bits - 1)

    def check_crc(self, frame_with_crc):
        """
        Verifica integridade do quadro recebido utilizando CRC-32.
        Retorna 0 se não houver erro; valor diferente indica erro.
        """
        poly_bits = bin(self.CRC32_POLY)[2:]
        remainder_str = self._crc_division_engine(frame_with_crc, poly_bits)
        return int(remainder_str, 2)
