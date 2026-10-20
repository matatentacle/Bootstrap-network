import sys, csv, os, re, openpyxl
src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
wb = openpyxl.load_workbook(src, data_only=True)
for ws in wb.worksheets:
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', ws.title).strip('_')
    rows = []
    for row in ws.iter_rows(values_only=True):
        vals = ['' if c is None else str(c).replace('\n', ' / ').strip() for c in row]
        while vals and vals[-1] == '': vals.pop()
        rows.append(vals)
    while rows and not rows[-1]: rows.pop()
    with open(f'{outdir}/{safe}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerows(rows)
    with open(f'{outdir}/{safe}.txt', 'w') as f:
        for i, vals in enumerate(rows, 1):
            if vals: f.write(f'{i:>4} | ' + ' | '.join(vals) + '\n')
    print(safe, len(rows))
