# Hand Calculation Tools

Excel hand-calculation tools for structural joints. Each tool consists of:

* an **Excel workbook** (`excel/`). This is the tool engineers use. Every calculation is a live formula, and nothing is locked or hidden.
* a **technical and user manual** (`docs/`), as an editable Word file (native equations) and a PDF.
* an **independent Python implementation** (`handcalc/`) and **automated tests** (`tests/`). The tests recalculate the workbook with LibreOffice and compare it with the Python implementation and with published worked examples.

| Tool | Workbook | Manual | Status |
|---|---|---|---|
| Bolted joint, single fastener (BOLT / SCREW / STUD) | `excel/Bolted_Joint_Tool.xlsx` | `docs/Bolted_Joint_Tool.docx/.pdf` | v2.0 – done |
| Double-shear lug / clevis, HSB 26101-01 | `excel/HSB_Clevis_Tool.xlsx` | `docs/HSB_Clevis_Tool.docx/.pdf` | v7.0 – done |
| Lug / pin / clevis, AFSAM Section 9 | `excel/AFSAM_Lug_Tool.xlsx` | `docs/AFSAM_Lug_Tool.docx/.pdf` | v6.0 – done |

## Bolted Joint Tool v2.0 – changes from the previous two workbooks

The previous `Bolted_Joint_Tool.xlsx` and `Bolted_Joint_Single_Fastener_Tool_v1.xlsx` are replaced by a single workbook.

* **One tool for BOLT / SCREW / STUD.** You select the configuration from a drop-down list.
* **General joint stack.** Up to 8 layers can be entered, each split at mid-grip using the similar-triangles method. This fixes three problems in the old workbooks:
  * a wrong result when the top plate is thicker than half the grip,
  * the separate 2-plate and 4-plate engines,
  * washer-placement errors.
* **Thread stripping follows the method document.** RF = Fsu / (1.5·FF·(Fpre+Pf)/As), and the weaker mating material governs. The old tools applied 1.5 to the external load only, which overestimated the RF by up to about 1.5×.
* **Torque unit fixed.** Torque is now in N·m; the old workbook was labelled Nmm.
* **Fatigue uses the real Goodman criterion** (Shigley eq. 8-38). The old workbook ignored mean stress.
* **Preload scatter and embedment are optional inputs.** Maximum preload is used for the strength checks and minimum preload for separation and slip.
* **New tightening-torque window** (Tmin / Tmax).
* **Every failure mode is always listed** with PASS / FAIL / N/A / NOT EVALUATED and the inputs it needs.
* **Thread tables are linked to the inputs** and regenerated from the standard formulas. In the old workbook the "ISO coarse" and "UNC" sheets actually contained UNF data.

## Running the tests

```bash
pip install openpyxl xlsxwriter pytest matplotlib
python -m pytest            # needs LibreOffice (soffice) for the Excel tests
```

If you edit a formula in a workbook, run the tests to confirm that the reference examples still match.

## Rebuilding

```bash
python tools/figures_bolted_joint.py          # schematic figures -> docs/figures
python tools/figures_bolted_joint_theory.py   # theory figures (derivations, example plots)
python tools/build_bolted_joint.py            # workbook layout -> excel/
python tools/screenshots_bolted_joint.py      # workbook screenshots for the manual (needs LibreOffice)
python tools/figures_hsb_clevis.py            # HSB clevis figures
python tools/build_hsb_clevis.py              # HSB clevis workbook
python tools/screenshots_hsb_clevis.py        # HSB clevis screenshots
python tools/digitize/make_tables.py          # AFSAM chart digitization -> handcalc/afsam_charts.py + overlays
python tools/figures_afsam.py                 # AFSAM sketches
python tools/build_afsam_lug.py               # AFSAM workbook
python tools/screenshots_afsam.py             # AFSAM screenshots
./tools/build_docs.sh                  # manuals -> docs/*.docx, docs/*.pdf (needs pandoc, Node + Playwright)
```

Rebuilding the workbook overwrites manual edits. Either edit the workbook directly, or edit the build script and rebuild, but not both.
