"""
Общие утилиты для формирования HTML-вложений в Allure-отчётах backend тестов.
"""

HTML_CSS = """
<style>
html{height:100%;min-height:100vh;background:#fff}
body{
    min-height:calc(100vh - 32px);
    font-family:Arial,sans-serif;
    font-size:13px;
    margin:16px;
    color:#222;
    box-sizing:border-box;
}
h2{margin:0 0 12px;font-size:15px;color:#2c3e50}
table{border-collapse:collapse;width:auto;margin-bottom:20px}
th{background:#d6e4f0;color:#2c3e50;padding:4px 12px;text-align:left;white-space:nowrap;font-size:12px}
th.r{text-align:right}
td{padding:3px 12px;border-bottom:1px solid #e0e0e0;vertical-align:top}
td.r{text-align:right;white-space:nowrap}
tr:nth-child(even){background:#f7f7f7}
tr:hover{background:#eef4fb}
.red{color:#c0392b;font-weight:bold}
.green{color:#27ae60}
.gray{color:#888}
.collapsible{margin:10px 0 18px;border:1px solid #d9e2ec;border-radius:6px;overflow:hidden}
.collapsible summary{cursor:pointer;list-style:none;padding:10px 14px;background:#f4f7fb;color:#2c3e50;font-weight:bold}
.collapsible summary::-webkit-details-marker{display:none}
.collapsible summary:hover{background:#eaf1f8}
.collapsible-body{padding:12px 14px 4px}
.club-block{margin-bottom:24px;border:1px solid #ddd;border-radius:4px;overflow:hidden}
.club-head{background:#34495e;color:#fff;padding:8px 14px;font-weight:bold}
.club-sub{color:#ccc;font-size:12px;font-weight:normal}
.plan-block{margin:10px 14px}
.plan-head{font-weight:bold;margin-bottom:4px;color:#2c3e50}
.entry-table td{font-size:12px;padding:3px 8px;font-family:monospace}
</style>
"""


def html_table(headers, rows, right_cols=()):
    """HTML-таблица с заголовком. right_cols — индексы колонок с выравниванием вправо."""
    ths = "".join(
        f'<th class="r">{h}</th>' if i in right_cols else f"<th>{h}</th>"
        for i, h in enumerate(headers)
    )
    trs = []
    for row in rows:
        tds = "".join(
            f'<td class="r">{cell}</td>' if i in right_cols else f"<td>{cell}</td>"
            for i, cell in enumerate(row)
        )
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def html_kv(pairs):
    """HTML-таблица ключ-значение."""
    rows = "".join(
        f'<tr><td><b>{k}</b></td><td class="r">{v}</td></tr>'
        for k, v in pairs
    )
    return f"<table>{rows}</table>"
