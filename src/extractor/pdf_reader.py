import pymupdf
from typing import List, Tuple, Generator, Optional


def extract_page_blocks(page: pymupdf.Page) -> List[Tuple[float, float, float, float, str]]:
    """Extrai os blocos de texto de uma página de forma geometricamente consciente de 2 colunas.
    Evita o entrelaçamento horizontal entre colunas paralelas.
    Retorna uma lista de tuplas (x0, y0, x1, y1, texto_limpo).
    """
    width = page.rect.width
    height = page.rect.height
    mid_x = width / 2.0

    raw_blocks = page.get_text("blocks")
    valid_blocks = []

    for b in raw_blocks:
        x0, y0, x1, y1, text, _, b_type = b
        if b_type != 0:  # Ignora imagens ou vetores
            continue

        clean_text = text.strip()
        if not clean_text:
            continue

        # Ignorar número de página no rodapé e cabeçalhos de navegação
        if (y0 > height - 48 or y1 < 28):
            if clean_text.isdigit() or len(clean_text) <= 3 or "|" in clean_text or "LIVRO" in clean_text.upper():
                continue

        valid_blocks.append((x0, y0, x1, y1, clean_text))

    # Separação por zonas da página
    top_full = []
    left_col = []
    right_col = []
    bottom_full = []

    for b in valid_blocks:
        x0, y0, x1, y1, _ = b
        is_full_width = (x0 < mid_x - 30 and x1 > mid_x + 30)

        if is_full_width:
            if y0 < height * 0.35:
                top_full.append(b)
            else:
                bottom_full.append(b)
        elif x0 < mid_x:
            left_col.append(b)
        else:
            right_col.append(b)

    # Ordenação vertical dentro de cada zona
    top_full.sort(key=lambda item: item[1])
    left_col.sort(key=lambda item: item[1])
    right_col.sort(key=lambda item: item[1])
    bottom_full.sort(key=lambda item: item[1])

    return top_full + left_col + right_col + bottom_full


def iter_pdf_blocks(pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> Generator[Tuple[int, int, str, Tuple[float, float, float, float]], None, None]:
    """Itera sobre todas as páginas do PDF devolvendo blocos limpos ordenados.
    Produz: (numero_pagina, indice_bloco, texto_bloco, (x0, y0, x1, y1))
    """
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    last_page = min(end_page, total_pages) if end_page is not None else total_pages

    for page_idx in range(start_page, last_page):
        page = doc[page_idx]
        blocks = extract_page_blocks(page)
        for b_idx, (x0, y0, x1, y1, text) in enumerate(blocks):
            yield (page_idx + 1, b_idx, text, (x0, y0, x1, y1))
