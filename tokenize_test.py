import inspect
import time
from extraction import annotate

source_lines, startline = inspect.getsourcelines(inspect)

tic = time.perf_counter()
annotated_lines, l2n, n2l, header_lines = annotate(source_lines, max_line=2000)
took = time.perf_counter() - tic


for ln, chunked_line in sorted(annotated_lines.items()):
    print(ln, '  ', end='')
    print(source_lines[ln-1])
    for chunk in chunked_line:
        # print(chunk[0].__repr__(), end='')
        print('\t', chunk)

    print('\n\n')


recon_lines = []
for ln, linelist in sorted(annotated_lines.items()):
    recon_lines.append(''.join([tup[0] for tup in linelist]))

recon_source = ''.join(recon_lines)
source = ''.join(source_lines)

assert source == recon_source

print('work took', 1000*took)
# print(name2locs)