#!/usr/bin/env python
import subprocess
from datetime import datetime
from pathlib import Path

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = Path('backups')
backup_dir.mkdir(exist_ok=True)

# PostgreSQL дамп
subprocess.run(
    f'pg_dump -U hh -h localhost -d homeharmony_new | gzip > {backup_dir}/backup_{timestamp}.sql.gz',
    shell=True, check=True
)
print(f'✅ {backup_dir}/backup_{timestamp}.sql.gz')

# Django дамп
subprocess.run([
    'python', 'manage.py', 'dumpdata', 'kitchen',
    '--indent', '2', '--output', str(backup_dir / f'dump_kitchen_{timestamp}.json')
], check=True)
print(f'✅ {backup_dir}/dump_kitchen_{timestamp}.json')