import os
import subprocess
from pathlib import Path

def generate_migration(message):
    """Generate a new migration with alembic
    
    Args:
        message (str): Migration message
    """
    subprocess.run(['alembic', 'revision', '--autogenerate', '-m', message])
    print(f"Migration with message '{message}' generated.")

def upgrade_db():
    """Apply all migrations to the database"""
    subprocess.run(['alembic', 'upgrade', 'head'])
    print("Database upgraded successfully.")

def downgrade_db(revision=''):
    """Downgrade database to previous revision or specific revision
    
    Args:
        revision (str): Revision to downgrade to (default: -1)
    """
    if not revision:
        revision = '-1'
    subprocess.run(['alembic', 'downgrade', revision])
    print(f"Database downgraded to revision {revision}.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration helper')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate migration
    gen_parser = subparsers.add_parser('generate', help='Generate a new migration')
    gen_parser.add_argument('message', help='Migration message')
    
    # Upgrade database
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade database to latest revision')
    
    # Downgrade database
    downgrade_parser = subparsers.add_parser('downgrade', help='Downgrade database')
    downgrade_parser.add_argument('--revision', help='Revision to downgrade to', default='')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_migration(args.message)
    elif args.command == 'upgrade':
        upgrade_db()
    elif args.command == 'downgrade':
        downgrade_db(args.revision)
    else:
        parser.print_help() 