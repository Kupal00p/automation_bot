"""
PostgreSQL to MySQL Reversion Script
Automatically reverts service files back to MySQL syntax
"""
import os
import re

def revert_file(filepath):
    """Revert a single file from PostgreSQL to MySQL syntax"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace cursor(cursor_factory=RealDictCursor) with cursor(dictionary=True)
    content = content.replace(
        'cursor(cursor_factory=RealDictCursor)',
        'cursor(dictionary=True)'
    )
    
    # Replace db_pool.putconn(conn) with conn.close()
    content = content.replace('db_pool.putconn(conn)', 'conn.close()')
    
    # Replace CURRENT_TIMESTAMP with NOW()
    content = re.sub(
        r'(\s+SET\s+\w+\s*=\s*)CURRENT_TIMESTAMP',
        r'\1NOW()',
        content,
        flags=re.IGNORECASE
    )
    
    # Remove RealDictCursor import if present
    content = re.sub(
        r'\nfrom psycopg2\.extras import RealDictCursor\n?',
        '\n',
        content
    )
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Reverted: {filepath}")
        return True
    else:
        print(f"⏭️  Skipped (no changes): {filepath}")
        return False

def main():
    """Revert all service files"""
    services_dir = os.path.join(os.path.dirname(__file__), 'services')
    
    files_to_revert = [
        'admin_service.py',
        'order_service.py',
        'order_processor.py',
        'order_validator.py',
        'product_service.py',
        'verification_service.py',
        'notification_service.py'
    ]
    
    reverted_count = 0
    for filename in files_to_revert:
        filepath = os.path.join(services_dir, filename)
        if os.path.exists(filepath):
            if revert_file(filepath):
                reverted_count += 1
    
    print(f"\n🎉 Reversion complete! {reverted_count} files reverted to MySQL.")

if __name__ == '__main__':
    main()
