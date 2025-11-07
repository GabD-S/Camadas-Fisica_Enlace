import numpy as np

class DigitalEncoder:
    """Implementa esquemas de codificação de linha (modulação em banda base).
    Atua na Camada Física, convertendo bits digitais em sinais elétricos específicos para transmissão.
    """

    def encode(self, bits, encoding_type, samples_per_bit=10):
        """
        Interface para selecionar e aplicar um método específico de codificação de linha.

        Parâmetros:
        - bits: sequência binária a ser codificada.
        - encoding_type: tipo de codificação (NRZ-Polar, Manchester, Bipolar).
        - samples_per_bit: quantidade de amostras por bit (define resolução temporal do sinal).
        """
        if encoding_type == "NRZ-Polar":
            return self.nrz_polar(bits, samples_per_bit)
        elif encoding_type == "Manchester":
            return self.manchester(bits, samples_per_bit)
        elif encoding_type == "Bipolar":
            return self.bipolar_ami(bits, samples_per_bit)
        else:
            raise ValueError(f"Tipo de codificação desconhecido: {encoding_type}")

    def nrz_polar(self, bits, samples_per_bit=10):
        """
        Implementa codificação NRZ-Polar (Non-Return to Zero Polar):
        - Bit '1': nível positivo constante (+1)
        - Bit '0': nível negativo constante (-1)

        O nível do sinal permanece constante durante toda duração do bit, gerando um sinal simples, porém sem autossincronização.
        """
        signal = []
        for bit in bits:
            val = 1.0 if int(bit) == 1 else -1.0
            signal.extend([val] * samples_per_bit)
        return np.array(signal)

    def manchester(self, bits, samples_per_bit=10):
        """
        Implementa codificação Manchester:
        Cada bit é dividido em duas metades:
        - Bit '0': primeira metade positiva (+1), segunda metade negativa (-1)
        - Bit '1': primeira metade negativa (-1), segunda metade positiva (+1)

        A mudança de polaridade no meio do bit garante melhor sincronização temporal entre transmissor e receptor.
        """
        half_spb = samples_per_bit // 2
        signal = []
        for bit in bits:
            if int(bit) == 0:
                signal.extend([1.0] * half_spb)
                signal.extend([-1.0] * half_spb)
            else:
                signal.extend([-1.0] * half_spb)
                signal.extend([1.0] * half_spb)
        return np.array(signal)

    def bipolar_ami(self, bits, samples_per_bit=10):
        """
        Implementa codificação Bipolar AMI (Alternate Mark Inversion):
        - Bit '0': nível zero (ausência de pulso)
        - Bit '1': alterna a polaridade do nível (+1 e -1) a cada ocorrência

        Utiliza polaridade alternada nos pulsos para representar bits '1', permitindo detecção de erros por violação de polaridade.
        """
        signal = []
        last_pulse_level = -1.0  # Inicializa para que o primeiro pulso seja positivo
        for bit in bits:
            if int(bit) == 0:
                signal.extend([0.0] * samples_per_bit)
            else:
                last_pulse_level *= -1.0
                signal.extend([last_pulse_level] * samples_per_bit)
        return np.array(signal)
