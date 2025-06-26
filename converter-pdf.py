#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import math
import time
import shutil
from pathlib import Path

# CONFIGURAÇÕES
GHOSTSCRIPT = r"Pasta\De\Instalação\gs\gs10.05.1\bin\gswin64c.exe"
IMAGEMAGICK = r"Pasta\De\Instalação\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
MUTOOL = shutil.which("mutool") or r"C:\Tools\MuPDF-1.26.2\mutool.exe"

# Perfis ICC
ICC_INPUT_RGB = r"C:\caminho\para\arquivos\PerfisICC\sRGB_ICC_v4_Appearance.icc"
ICC_OUTPUT_CMYK = r"C:\caminho\para\arquivos\PerfisICC\USWebCoatedSWOP.icc"

# Pastas a varrer
PASTAS_RAIZES = [
    r"/caminho/para/arquivos/cartao_de_visita",
    r"/caminho/para/arquivos/folhetos",
    r"/caminho/para/arquivos/adesivos",
]

CHECK_INTERVAL = 10  # segundos

# Localização do pdfinfo
PDFINFO = shutil.which("pdfinfo")
fallback = r"C:\poppler-24.08.0\Library\bin\pdfinfo.exe"
if not PDFINFO and Path(fallback).exists():
    PDFINFO = fallback
    print(f"[INFO] Usando pdfinfo em: {PDFINFO}")
elif not PDFINFO:
    print("[WARN] 'pdfinfo' não encontrado. Checagem de PDF ficará desativada.")

# Validação de executáveis essenciais
for cmd, name in [(GHOSTSCRIPT, "Ghostscript"), (IMAGEMAGICK, "ImageMagick"), (MUTOOL, "Mutool")]:
    if not Path(cmd).exists():
        print(f"[WARN] {name} não encontrado em: {cmd}. Sem conversão para curvas.")


def log_pdf_invalido(caminho_pdf: Path):
    log_file = caminho_pdf.parent / 'log_pdfs_incorretos.txt'
    with log_file.open('a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {caminho_pdf.name}\n")


def get_pdf_pages(caminho_pdf: Path) -> int:
    if not PDFINFO:
        return 0
    try:
        out = subprocess.check_output([PDFINFO, str(caminho_pdf)], universal_newlines=True)
        for linha in out.splitlines():
            if linha.startswith("Pages:"):
                return int(linha.split()[1])
    except Exception:
        pass
    return 0


def get_pdf_dimensions_cm(caminho_pdf: Path) -> (float, float):
    if not PDFINFO:
        return 0.0, 0.0
    try:
        out = subprocess.check_output([PDFINFO, str(caminho_pdf)], universal_newlines=True)
    except Exception:
        return 0.0, 0.0
    for linha in out.splitlines():
        if linha.startswith("Page size:"):
            parts = linha.split()
            largura_pt, altura_pt = float(parts[2]), float(parts[4])
            fator = 2.54 / 72
            return largura_pt * fator, altura_pt * fator
    return 0.0, 0.0


def calcular_resolucao_cm_cm(largura_cm: float, altura_cm: float) -> int:
    area = largura_cm * altura_cm
    if area <= 0:
        return 300
    valor = 300 / math.log10(area)
    valor = round(valor)
    if area > 2500:
        limites = [150, 100, 50]
        melhor = min(limites, key=lambda L: abs(valor - L) - 5 if abs(valor - L) > 5 else abs(valor - L))
        return melhor
    return 300


def tem_tifs_convertidos(caminho_pdf: Path) -> bool:
    base = caminho_pdf.stem
    pasta = caminho_pdf.parent
    matches = list(pasta.glob(f"{base}-???.tif"))
    if matches:
        print(f"[DEBUG] Ignorando {caminho_pdf.name}: já existe {matches[0].name}")
    return bool(matches)


def converter_pdf_para_tif(caminho_pdf: Path):
    base = caminho_pdf.stem
    pasta = caminho_pdf.parent
    outlined_pdf = pasta / f"{base}_outlined.pdf"
    original_pdf = caminho_pdf

    # 1) Converter texto em curvas via mutool
    if Path(MUTOOL).exists():
        subprocess.run([MUTOOL, 'clean', '-gg', str(original_pdf), str(outlined_pdf)], check=True)
        source_pdf = outlined_pdf
        print(f"[INFO] Texto convertido em curvas: {outlined_pdf.name}")
    else:
        source_pdf = original_pdf

    # 2) Validar PDF
    if PDFINFO:
        valid = subprocess.run([PDFINFO, str(source_pdf)], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        if valid.returncode != 0:
            print(f"[WARN] PDF inválido: {source_pdf.name}")
            log_pdf_invalido(source_pdf)
            if outlined_pdf.exists(): outlined_pdf.unlink()
            return

    # 3) Dimensões e filtro de proporção 10:1
    largura_cm, altura_cm = get_pdf_dimensions_cm(source_pdf)
    if largura_cm > 0 and altura_cm > 0:
        ratio = max(largura_cm / altura_cm, altura_cm / largura_cm)
        if ratio > 10:
            print(f"[INFO] Ignorando {base}: proporção {ratio:.1f}:1 > 10:1")
            if outlined_pdf.exists(): outlined_pdf.unlink()
            return

    # 4) Verificar Impressao-Digital
    pages = get_pdf_pages(source_pdf)
    only_first = ('impressao-digital' in base.lower()) and pages > 16
    if only_first:
        print(f"[INFO] {base}: >16 páginas Impressao-Digital, exportando apenas página 1")

    # 5) Calcular DPI
    largura_cm, altura_cm = get_pdf_dimensions_cm(source_pdf)
    dpi = calcular_resolucao_cm_cm(largura_cm, altura_cm) if PDFINFO else 300
    if "Sign - Sublimação" in source_pdf.parts and "camisa" in base.lower():
        dpi = 100
        print(f"[INFO] Override DPI para 100 em {source_pdf.name}")
    else:
        print(f"[INFO] Convertendo {source_pdf.name}: {dpi} DPI")

    # 6) Ghostscript
    gs_args = [
        GHOSTSCRIPT,
        '-dBATCH', '-dNOPAUSE', '-dSAFER',
        '-sDEVICE=tiff32nc',
        '-dRenderIntent=1',
        '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4',
        f'-sDefaultRGBProfile={ICC_INPUT_RGB}',
        f'-sOutputICCProfile={ICC_OUTPUT_CMYK}',
        f'-r{dpi}'
    ]
    if only_first:
        gs_args += ['-dFirstPage=1', '-dLastPage=1']
    temp_tif = pasta / f"{base}_gs.tif"
    gs_args += [f'-sOutputFile={temp_tif}', str(source_pdf)]
    proc = subprocess.run(gs_args, stderr=subprocess.PIPE,
                           stdout=subprocess.DEVNULL, universal_newlines=True)

    # Captura de fontes faltando
    faltando = [l for l in proc.stderr.splitlines() if 'Loading font' in l or 'substitute' in l]
    if faltando:
        log_file = pasta / 'fontes-faltando.txt'
        with log_file.open('w', encoding='utf-8') as f:
            f.write('\n'.join(faltando))
        print(f"[WARN] Fontes faltando registradas em {log_file}")

    # 7) ImageMagick
    im_cmd = [
        IMAGEMAGICK,
        str(temp_tif),
        '-define', 'tiff:alpha=associated',
        '-compress', 'LZW',
        str(pasta / f"{base}-%03d.tif")
    ]
    subprocess.run(im_cmd, check=True)

    # 8) Limpeza
    temp_tif.unlink(missing_ok=True)
    if source_pdf != original_pdf and outlined_pdf.exists():
        outlined_pdf.unlink(missing_ok=True)


def varrer_e_converter():
    while True:
        for raiz in PASTAS_RAIZES:
            raiz_path = Path(raiz)
            print(f"[DEBUG] Varrendo: {raiz_path}")
            for caminho in raiz_path.rglob("*.pdf"):
                if caminho.parent == raiz_path:
                    continue
                if tem_tifs_convertidos(caminho):
                    continue
                try:
                    converter_pdf_para_tif(caminho)
                except Exception as e:
                    print(f"[ERRO] {caminho}: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    varrer_e_converter()
