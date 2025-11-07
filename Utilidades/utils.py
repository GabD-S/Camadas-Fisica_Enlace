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
