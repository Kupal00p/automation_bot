"""
MySQL to PostgreSQL Migration Script
Automatically updates service files to use PostgreSQL syntax
"""
import os
import re

def migrate_file(filepath):
    """Migrate a single file from MySQL to PostgreSQL syntax"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace cursor(dictionary=True) with cursor(cursor_factory=RealDictCursor)
    content = content.replace(
        'cursor(dictionary=True)',
        'cursor(cursor_factory=RealDictCursor)'
    )
    
    # Replace conn.close() with db_pool.putconn(conn)
    # But be careful not to replace it in finally blocks that already have it
    content = re.sub(
        r'(\s+)conn\.close\(\)(?!\s*#\s*Already using putconn)',
        r'\1db_pool.putconn(conn)  # Already using putconn',
        content
    )
    
    # Replace NOW() with CURRENT_TIMESTAMP
    content = content.replace('NOW()', 'CURRENT_TIMESTAMP')
    
    # Replace cursor.close() followed by conn.close() with cursor.close() followed by db_pool.putconn(conn)
    content = re.sub(
        r'cursor\.close\(\)\s+conn\.close\(\)',
        'cursor.close()\n        db_pool.putconn(conn)',
        content
    )
    
    # Add RealDictCursor import if cursor_factory is used
    if 'cursor_factory=RealDictCursor' in content and 'from psycopg2.extras import RealDictCursor' not in content:
        # Find the imports section and add the import
        content = re.sub(
            r'(from services\.db_service import.*)',
            r'\1\nfrom psycopg2.extras import RealDictCursor',
            content,
            count=1
        )
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Migrated: {filepath}")
        return True
    else:
        print(f"⏭️  Skipped (no changes): {filepath}")
        return False

def main():
    """Migrate all service files"""
    services_dir = os.path.join(os.path.dirname(__file__), 'services')
    
    files_to_migrate = [
        'admin_service.py',
        'order_service.py',
        'order_processor.py',
        'order_validator.py',
        'product_service.py',
        'verification_service.py',
        'notification_service.py'
    ]
    
    migrated_count = 0
    for filename in files_to_migrate:
        filepath = os.path.join(services_dir, filename)
        if os.path.exists(filepath):
            if migrate_file(filepath):
                migrated_count += 1
    
    print(f"\n🎉 Migration complete! {migrated_count} files updated.")

if __name__ == '__main__':
    main()
