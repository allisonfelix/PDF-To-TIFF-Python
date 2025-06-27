# 🖨️ PDF-to-TIFF Pipeline Automator – Python + GhostScript + ImageMagick

Este projeto em **Python** automatiza a conversão de arquivos PDF em imagens TIFF com resolução e perfis de cor configuráveis. É voltado para gráficas que precisam agilizar a preparação de arquivos para impressão, substituindo processos manuais em ferramentas como Photoshop.

---

## 🧩 Contexto

Complementa e se integra ao pipeline existente desenvolvido em **PowerShell**, também disponível neste repositório, responsável por orquestrar o tratamento e movimentação de arquivos gráficos.

---

## ✅ O que este script faz

- Varrimento automático de múltiplas pastas e subpastas;
- Validação de PDFs via `pdfinfo` para garantir integridade antes da conversão;
- Cálculo dinâmico de resolução (DPI) com base no tamanho físico do PDF;
- Conversão de textos em curvas via `mutool`;
- Exportação para TIFF com GhostScript e tratamento final com ImageMagick;
- Registro de fontes ausentes em log;
- Filtros personalizados (por exemplo, ignorar PDFs com proporção extrema).

---

## ⚙️ Requisitos

Instale as ferramentas abaixo e adicione seus executáveis ao PATH **ou** aponte seus caminhos diretamente no script:

- [GhostScript](https://www.ghostscript.com/)
- [ImageMagick](https://imagemagick.org/)
- [MuPDF (mutool)](https://mupdf.com/)
- [Poppler for Windows (pdfinfo)](https://blog.alivate.com.au/poppler-windows/)

---

## 📁 Estrutura esperada

```
PDF-to-TIFF-Pipeline-Python/
├── converter-pdf.py               # Script principal em Python
├── README.md
├── PerfisICC/
│   ├── sRGB_ICC_v4_Appearance.icc
│   └── USWebCoatedSWOP.icc
└── C:/Pedidos/...             # Pastas monitoradas com os PDFs
```

---

## 🔧 Como usar

1. Edite o script `converter-pdf.py` e defina:
   - Caminho dos executáveis (`GHOSTSCRIPT`, `IMAGEMAGICK`, `MUTOOL`, `PDFINFO`);
   - Caminho dos perfis ICC (`ICC_INPUT_RGB`, `ICC_OUTPUT_CMYK`);
   - Lista de pastas em `PASTAS_RAIZES`.

2. Execute com:

```bash
python converter-pdf.py
```

O script ficará em execução contínua, monitorando as pastas e processando novos PDFs.

---

## 🔄 Integração com PowerShell

Este script pode ser chamado a partir de outro pipeline em PowerShell, por exemplo:

```powershell
Start-Process -FilePath "python.exe" -ArgumentList "converter-pdf.py"
```

Permite integração híbrida entre o tratamento de arquivos com `robocopy`, geração de logs em CSV e dashboards, ou execução sequencial após o preflight automatizado.

---

## 📌 Observações

- O script ignora arquivos já convertidos para evitar retrabalho;
- PDFs inválidos ou com fontes ausentes são registrados em arquivos `.txt` na pasta do arquivo;
- Proporções maiores que 10:1 são ignoradas automaticamente;
- PDFs com “camisa” no nome (em subpastas de "Sign - Sublimação") são exportados com 100 DPI automaticamente.

---

## 🤝 Créditos

Desenvolvido por [Allison dos Santos Felix](https://linkedin.com/in/allison-dos-santos-felix-743814a2), com foco em automações gráficas e fluxos híbridos de produção.

---

## 📄 Licença

Uso interno. Para fins educacionais e demonstrativos.
