class ErrorCorrector:
    """Implementa o Código de Hamming(7,4) para correção de erro de 1 bit por bloco.
    Atua na Camada de Enlace, adicionando bits de paridade para garantir integridade dos dados.
    """

    def encode_hamming(self, data_bits):
        """
        Codifica os dados usando Hamming(7,4).
        Para cada 4 bits de dados, adiciona 3 bits de paridade formando blocos de 7 bits.
        """
        encoded_string = ""

        for i in range(0, len(data_bits), 4):
            chunk = data_bits[i:i+4].ljust(4, '0')  # Preenche blocos incompletos com zeros à direita
            d = [int(b) for b in chunk]

            # Calcula bits de paridade conforme esquema Hamming(7,4)
            p1 = (d[0] + d[1] + d[3]) % 2  # Paridade dos bits 1, 3, 5, 7
            p2 = (d[0] + d[2] + d[3]) % 2  # Paridade dos bits 2, 3, 6, 7
            p3 = (d[1] + d[2] + d[3]) % 2  # Paridade dos bits 4, 5, 6, 7

            # Bloco codificado: p1 p2 d1 p3 d2 d3 d4
            encoded_chunk = f"{p1}{p2}{d[0]}{p3}{d[1]}{d[2]}{d[3]}"
            encoded_string += encoded_chunk

        return encoded_string

    def decode_hamming(self, received_bits):
        """
        Decodifica blocos Hamming(7,4), detectando e corrigindo até 1 erro de bit por bloco.

        Retorna:
            decoded_string: dados originais sem bits de paridade.
            corrected_full_frame: sequência recebida após correções aplicadas.
            report: quantidade de erros detectados e corrigidos.
        """
        decoded_string = ""
        corrected_full_frame = ""
        erros_corrigidos = 0

        for i in range(0, len(received_bits), 7):
            chunk = received_bits[i:i+7]
            if len(chunk) < 7:
                continue  # Descarta bloco incompleto

            bits = [int(b) for b in chunk]
            p1, p2, d1, p3, d2, d3, d4 = bits

            # Calcula bits de síndrome (c1, c2, c3) para identificar erros
            c1 = (p1 + d1 + d2 + d4) % 2  # Síndrome relacionada à posição 1
            c2 = (p2 + d1 + d3 + d4) % 2  # Síndrome relacionada à posição 2
            c3 = (p3 + d2 + d3 + d4) % 2  # Síndrome relacionada à posição 4

            # Determina posição do erro no bloco (0 se não houver erro)
            error_pos = c3 * 4 + c2 * 2 + c1

            chunk_list = list(chunk)
            if error_pos != 0:
                erros_corrigidos += 1
                # Corrige o bit invertendo seu valor (posições indexadas em 1)
                chunk_list[error_pos - 1] = '1' if chunk_list[error_pos - 1] == '0' else '0'

            corrected_chunk_str = "".join(chunk_list)
            corrected_full_frame += corrected_chunk_str

            # Extrai bits de dados (posições 3, 5, 6, 7)
            decoded_string += corrected_chunk_str[2] + corrected_chunk_str[4:]

        # Relatório de erros corrigidos
        report = (f"{erros_corrigidos} erro(s) de bit único corrigido(s)."
                  if erros_corrigidos > 0 else
                  "Nenhum erro de bit único detectado.")

        return decoded_string, corrected_full_frame, report