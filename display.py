# display.py
import os

def get_terminal_width(default=180):
    """Deteksi lebar terminal, fallback ke default jika gagal."""
    try:
        return os.get_terminal_size().columns
    except:
        return default

def print_header(title: str, width: int = None, char: str = "─"):
    """Cetak header dengan judul di tengah, menyesuaikan lebar terminal."""
    if width is None:
        width = get_terminal_width()
    title_len = len(title)
    line_len = (width - title_len - 2) // 2
    line = char * line_len
    if (width - title_len) % 2 == 0:
        print(f"{line} {title} {line}")
    else:
        print(f"{line} {title} {line}{char}")

def print_panel(title: str, content_lines: list, width: int = None):
    """
    Cetak panel dengan border Unicode.
    Lebar menyesuaikan terminal jika width=None.
    """
    if width is None:
        width = get_terminal_width()
    content_width = width - 4

    # Border atas dengan judul
    title_part = f"┌─ {title} "
    remaining = width - len(title_part) - 1
    if remaining < 0:
        title_part = title_part[:width-2] + "┐"
        print(title_part)
    else:
        print(title_part + "─" * remaining + "┐")

    # Konten
    for line in content_lines:
        print(f"│ {line:<{content_width}} │")

    # Border bawah
    print("└" + "─" * (width - 2) + "┘")

def print_table(headers: list, rows: list, column_widths: list = None):
    """Cetak tabel dengan border Unicode."""
    if not rows:
        return

    num_cols = len(headers)
    if column_widths is None:
        column_widths = []
        for i in range(num_cols):
            max_len = len(str(headers[i]))
            for row in rows:
                if i < len(row):
                    max_len = max(max_len, len(str(row[i])))
            column_widths.append(max_len + 2)  # padding

    def border_line(left, mid, right, sep):
        line = left
        for i, w in enumerate(column_widths):
            line += sep * (w + 2)
            if i < num_cols - 1:
                line += mid
        line += right
        return line

    print(border_line("┌", "┬", "┐", "─"))
    header_cells = [f" {h:<{column_widths[i]}} " for i, h in enumerate(headers)]
    print("│" + "│".join(header_cells) + "│")
    print(border_line("├", "┼", "┤", "─"))
    for row in rows:
        cells = [f" {str(val):<{column_widths[i]}} " for i, val in enumerate(row)]
        print("│" + "│".join(cells) + "│")
    print(border_line("└", "┴", "┘", "─"))

def print_info(label: str, value: str, indent: int = 3):
    """Cetak pasangan label–nilai dengan indentasi."""
    print(" " * indent + f"{label}: {value}")

def print_separator(char: str = "─", width: int = None):
    """Cetak garis pemisah."""
    if width is None:
        width = get_terminal_width()
    print(char * width)