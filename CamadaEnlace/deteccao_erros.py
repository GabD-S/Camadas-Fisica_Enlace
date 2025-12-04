class ErrorDetector:
    """
    Implementa métodos de detecção de erros na Camada de Enlace.
    Inclui Paridade Par (detecta 1 bit de erro), checksum e CRC-32 (detecta erros em rajada).
    """

    def __init__(self):
        # Polinômio CRC-32 padrão IEEE 802.3 (Ethernet), sem o bit mais significativo implícito (x^32)
        self.CRC32_POLY = 0x104C11DB7
        self.CHECKSUM_SIZE = 16  # Vamos usar checksum de 16 bits

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
    
    def calculate_checksum(self, data_bits, checksum_bits=16):
        """
        Calcula o checksum de 16 bits para dados binários.
        Algoritmo: Soma os valores de 16-bit e faz complemento de 1.
        
        Args:
            data_bits (str): String de bits dos dados
            checksum_bits (int): Tamanho do checksum (8, 16, 32 bits)
            
        Returns:
            str: String de bits do checksum
        """
        # Garante que o número de bits seja múltiplo de checksum_bits
        if len(data_bits) % checksum_bits != 0:
            # Adiciona zeros à direita para completar
            padding = checksum_bits - (len(data_bits) % checksum_bits)
            data_bits = data_bits + '0' * padding
        
        # Divide os dados em palavras de checksum_bits bits
        num_words = len(data_bits) // checksum_bits
        total = 0
        
        for i in range(num_words):
            start = i * checksum_bits
            end = start + checksum_bits
            word = data_bits[start:end]
            # Converte para inteiro
            total += int(word, 2)
        
        # Adiciona o carry (se houver) de volta ao total
        max_value = (1 << checksum_bits) - 1  # Valor máximo para checksum_bits bits
        
        while total > max_value:
            # Extrai o carry e soma de volta
            carry = total >> checksum_bits
            total = (total & max_value) + carry
        
        # Calcula o complemento de 1
        checksum_value = (~total) & max_value
        
        # Converte para string binária com padding
        checksum_str = format(checksum_value, f'0{checksum_bits}b')
        
        return checksum_str

    def add_checksum(self, data_bits, checksum_bits=16):
        """
        Adiciona checksum aos dados.
        
        Args:
            data_bits (str): Dados originais em bits
            checksum_bits (int): Tamanho do checksum
            
        Returns:
            str: Dados + checksum
        """
        checksum = self.calculate_checksum(data_bits, checksum_bits)
        return data_bits + checksum

    def verify_checksum(self, data_with_checksum, checksum_bits=16):
        """
        Verifica a integridade dos dados usando checksum.
        
        Args:
            data_with_checksum (str): Dados com checksum anexado
            checksum_bits (int): Tamanho do checksum
            
        Returns:
            bool: True se o checksum for válido, False caso contrário
        """
        # Separa dados e checksum
        data_bits = data_with_checksum[:-checksum_bits]
        received_checksum = data_with_checksum[-checksum_bits:]
        
        # Calcula checksum dos dados recebidos
        calculated_checksum = self.calculate_checksum(data_bits, checksum_bits)
        
        # Verifica se são iguais
        # No checksum, a soma de todos os dados + checksum deve ser zero
        # (em complemento de 1)
        max_value = (1 << checksum_bits) - 1
        
        # Soma todos os blocos (dados + checksum recebido)
        all_bits = data_with_checksum
        num_words = len(all_bits) // checksum_bits
        total = 0
        
        for i in range(num_words):
            start = i * checksum_bits
            end = start + checksum_bits
            word = all_bits[start:end]
            total += int(word, 2)
        
        # Adiciona o carry de volta
        while total > max_value:
            carry = total >> checksum_bits
            total = (total & max_value) + carry
        
        # A soma total deve ser zero (em complemento de 1)
        return total == 0

    def verify_checksum_simple(self, data_with_checksum, checksum_bits=16):
        """
        Método simplificado de verificação: apenas compara checksums.
        Mais direto para debug.
        
        Args:
            data_with_checksum (str): Dados com checksum anexado
            checksum_bits (int): Tamanho do checksum
            
        Returns:
            tuple: (bool, str, str) - (válido, checksum_calculado, checksum_recebido)
        """
        data_bits = data_with_checksum[:-checksum_bits]
        received_checksum = data_with_checksum[-checksum_bits:]
        
        calculated_checksum = self.calculate_checksum(data_bits, checksum_bits)
        
        is_valid = (calculated_checksum == received_checksum)
        
        return is_valid, calculated_checksum, received_checksum
