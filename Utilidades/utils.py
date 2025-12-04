import numpy as np
import matplotlib.pyplot as plt

def text_to_binary(text):
    """
    Converte uma string de texto para uma sequência contínua de bits (ASCII 8 bits por caractere).
    Função típica das camadas supeiores preparando o dado para transmissão binária.

    Args:
        text (str): Texto de entrada.

    Returns:
        str: String de bits concatenados (ex: "0100100001100101...").
    """
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_str):
    """
    Converte uma string de bits contínua em texto ASCII, considerando grupos de 8 bits por caractere.
    Fundamental para reconstruir o dado nas camadas supeiores após a recepção.

    Args:
        binary_str (str): String de bits concatenados.

    Returns:
        str: Texto decodificado dos bytes válidos.
    """
    # Garante que só bytes completos (8 bits) sejam convertidos.
    padding = len(binary_str) % 8
    if padding != 0:
        binary_str = binary_str[:len(binary_str) - padding]

    # Divide em blocos de 8 bits e converte para caracteres ASCII.
    chars = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    return ''.join(chr(int(char, 2)) for char in chars if int(char, 2) != 0)

def plot_signal(time_or_x, signal, title, xlabel="Tempo (s)", ylabel="Amplitude (V)", is_digital=False):
    """
    Plota um sinal (digital ou analógico) para análise de transmissão/recepção.
    Usado em contextos da Camada Física (banda base e passa-faixa) e para depuração.

    Args:
        time_or_x (array-like): Eixo X (tempo ou índice de amostra).
        signal (array-like): Valores do sinal a serem plotados.
        title (str): Título do gráfico.
        xlabel (str, opcional): Rótulo do eixo X.
        ylabel (str, opcional): Rótulo do eixo Y.
        is_digital (bool, opcional): True para sinais digitais (usa degraus), False para analógicos (linha contínua).
    """
    plt.figure(figsize=(15, 4))
    if is_digital:
        # Sinais digitais: degraus (NRZ, Manchester etc.)
        plt.step(time_or_x, signal, where='post')
    else:
        # Sinais analógicos: linha contínua (modulação por portadora).
        plt.plot(time_or_x, signal)

    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True)

    # Ajuste dinâmico do eixo Y para melhor visualização, com margem.
    min_val = np.min(signal)
    max_val = np.max(signal)
    plt.ylim(min_val - abs(min_val)*0.2 - 0.2, max_val + abs(max_val)*0.2 + 0.2)

    plt.tight_layout()
    plt.show()

def plot_constellation(qam_points, title="Diagrama de Constelação 8-QAM"):
    """
    Plota o diagrama de constelação (I-Q) para modulações QAM (Camada Física),
    ilustrando os símbolos modulados no plano Em Fase (I) vs. Quadratura (Q).

    Args:
        qam_points (list/array): Lista de números complexos (cada um é um símbolo I/Q).
        title (str, opcional): Título do gráfico.
    """
    # Extração das componentes I (real) e Q (imaginária) de cada ponto.
    i_components = [p.real for p in qam_points]
    q_components = [p.imag for p in qam_points]

    plt.figure(figsize=(6, 6))
    plt.scatter(i_components, q_components, c='blue', marker='o')

    plt.title(title, fontsize=14)
    plt.xlabel("Componente em Fase (I)", fontsize=12)
    plt.ylabel("Componente em Quadratura (Q)", fontsize=12)
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.axis('equal')  # Escala igual em ambos os eixos

    # Anotação dos símbolos para identificação visual (e.g., S0, S1...)
    for i, point in enumerate(qam_points):
        plt.annotate(f'S{i}', (point.real + 0.05, point.imag + 0.05))

    plt.tight_layout()
    plt.show()

def plot_qam16_constellation(qam_points, title="Diagrama de Constelação 16-QAM"):
    """
    Plota o diagrama de constelação para 16-QAM.
    """
    i_components = [p.real for p in qam_points]
    q_components = [p.imag for p in qam_points]
    
    plt.figure(figsize=(8, 8))
    plt.scatter(i_components, q_components, c='blue', marker='o', alpha=0.6)
    
    # Adiciona pontos de referência da constelação ideal
    qam16_ref = [
        -3+3j, -1+3j, 1+3j, 3+3j,
        -3+1j, -1+1j, 1+1j, 3+1j,
        -3-1j, -1-1j, 1-1j, 3-1j,
        -3-3j, -1-3j, 1-3j, 3-3j
    ]
    real_ref = [p.real for p in qam16_ref]
    imag_ref = [p.imag for p in qam16_ref]
    plt.scatter(real_ref, imag_ref, color='red', s=50, alpha=0.3, marker='x')
    
    plt.title(title, fontsize=14)
    plt.xlabel("Componente em Fase (I)", fontsize=12)
    plt.ylabel("Componente em Quadratura (Q)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.axis('equal')
    
    # Adiciona grade mais densa para 16-QAM
    for i in [-3, -1, 1, 3]:
        plt.axhline(i, color='gray', linewidth=0.2, linestyle='--')
        plt.axvline(i, color='gray', linewidth=0.2, linestyle='--')
    
    plt.tight_layout()
    plt.show()

def format_checksum_info(checksum_binary, data_bits=None):
    """
    Formata informações do checksum para exibição.
    
    Args:
        checksum_binary (str): String binária do checksum
        data_bits (str, opcional): Dados originais para cálculo
        
    Returns:
        str: String formatada com informações do checksum
    """
    if len(checksum_binary) not in [8, 16, 32]:
        return f"Checksum inválido: {checksum_binary} ({len(checksum_binary)} bits)"
    
    checksum_int = int(checksum_binary, 2)
    hex_width = len(checksum_binary) // 4
    
    info = f"Checksum: {checksum_binary}\n"
    info += f"  Decimal: {checksum_int}\n"
    info += f"  Hexadecimal: 0x{checksum_int:0{hex_width}X}\n"
    
    if data_bits:
        # Calcula checksum dos dados para verificação
        from CamadaEnlace.deteccao_erros import ErrorDetector
        detector = ErrorDetector()
        calculated = detector.calculate_checksum(data_bits, len(checksum_binary))
        info += f"  Verificação: {'OK' if checksum_binary == calculated else 'INVÁLIDO'}\n"
    
    return info

def demonstrate_checksum_example():
    """
    Demonstra um exemplo completo de checksum.
    """
    example_data = "010000010100001001000011"  # "ABC" em ASCII: 01000001 01000010 01000011
    
    print("📊 Exemplo de Checksum")
    print("=" * 60)
    print(f"Dados: '{example_data}'")
    print(f"       (ASCII: 'A' 'B' 'C')")
    
    from CamadaEnlace.deteccao_erros import ErrorDetector
    detector = ErrorDetector()
    
    checksum_8 = detector.calculate_checksum(example_data, 8)
    checksum_16 = detector.calculate_checksum(example_data, 16)
    
    print(f"\nChecksum 8-bit:  {checksum_8} (0x{int(checksum_8, 2):02X})")
    print(f"Checksum 16-bit: {checksum_16} (0x{int(checksum_16, 2):04X})")
    
    # Testar com erro
    corrupted = list(example_data + checksum_16)
    corrupted[5] = '1' if corrupted[5] == '0' else '0'  # Inverte um bit
    corrupted_str = ''.join(corrupted)
    
    is_valid = detector.verify_checksum(corrupted_str, 16)
    print(f"\nApós inverter bit 5: {'❌ Erro detectado!' if not is_valid else '✅ Não detectado (ERRO!)'}")    