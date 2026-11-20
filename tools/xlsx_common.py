"""Shared formats and helpers for the workbook builders (xlsxwriter)."""


def formats(wb):
    F = {}

    def fmt(name, **kw):
        base = {"font_name": "Calibri", "font_size": 10, "valign": "vcenter"}
        base.update(kw)
        F[name] = wb.add_format(base)

    fmt("title", bold=True, font_size=16, font_color="#1F4E78")
    fmt("sub", italic=True, font_color="#595959")
    fmt("sec", bold=True, bg_color="#1F4E78", font_color="white")
    fmt("hdr", bold=True, bg_color="#D9E1F2", border=1, text_wrap=True)
    fmt("txt", text_wrap=True)
    fmt("txtb", text_wrap=True, border=1, border_color="#BFBFBF")
    fmt("bold", bold=True)
    fmt("in", bg_color="#DDEBF7", border=1, border_color="#5B9BD5", locked=False, num_format="General")
    fmt("intxt", bg_color="#DDEBF7", border=1, border_color="#5B9BD5", locked=False)
    fmt("calc", bg_color="#F2F2F2", border=1, border_color="#BFBFBF", num_format="#,##0.000")
    fmt("calc0", bg_color="#F2F2F2", border=1, border_color="#BFBFBF", num_format="#,##0")
    fmt("calcg", bg_color="#F2F2F2", border=1, border_color="#BFBFBF", num_format="General")
    fmt("res", bg_color="#FFF2CC", border=1, border_color="#BF9000", num_format="0.00", bold=True, align="center")
    fmt("res0", bg_color="#FFF2CC", border=1, border_color="#BF9000", num_format="#,##0", align="center")
    fmt("rest", bg_color="#FFF2CC", border=1, border_color="#BF9000", bold=True, align="center", text_wrap=True)
    fmt("big", bg_color="#FFF2CC", border=2, border_color="#BF9000", bold=True, font_size=13, align="center",
        num_format="0.00", text_wrap=True)
    fmt("big0", bg_color="#FFF2CC", border=2, border_color="#BF9000", bold=True, font_size=13, align="center",
        num_format="#,##0")
    fmt("small", font_size=9, font_color="#595959", text_wrap=True)
    fmt("pass", bg_color="#C6EFCE", font_color="#006100", bold=True)
    fmt("fail", bg_color="#FFC7CE", font_color="#9C0006", bold=True)
    fmt("na", bg_color="#EDEDED", font_color="#7F7F7F")
    fmt("ne", bg_color="#FCE4D6", font_color="#833C0B", bold=True)
    return F


def status_cf(ws, rng, F):
    for value, f in [("FAIL", "fail"), ("CHECK", "fail"), ("INPUT", "fail"), ("NEGATIVE", "fail"),
                     ("PASS", "pass"), ("OK", "pass"), ("ALL OK", "pass"), ("POSITIVE", "pass"),
                     ("N/A", "na"), ("INFO", "na"), ("NOT EVAL", "ne")]:
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": value, "format": F[f]})


def rf_fail_cf(ws, rng, first_cell, F):
    ws.conditional_format(rng, {"type": "formula", "criteria": f"=AND(ISNUMBER({first_cell}),{first_cell}<1)",
                                "format": F["fail"]})


def readme(ws, lines, F):
    ws.set_column("A:A", 2)
    ws.set_column("B:B", 120)
    for i, (k, t) in enumerate(lines):
        ws.write(i, 1, t, F[k])
        if k == "txt":
            ws.set_row(i, 30)
