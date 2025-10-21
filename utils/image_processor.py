"""
Image Processing Utility
Handles image compression, validation, and optimization
"""
import os
import logging
from PIL import Image
from pathlib import Path
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Enterprise-level image processing and validation"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, config=None):
        """
        Initialize image processor
        
        Args:
            config: Dictionary with compression settings
        """
        self.config = config or {
            'compression_quality': 85,
            'max_width': 2048,
            'max_height': 2048,
            'thumbnail_size': (300, 300)
        }
    
    def validate_image(self, file_path):
        """
        Validate image file
        
        Args:
            file_path: Path to image file
            
        Returns:
            dict: Validation result with status and details
        """
        result = {
            'valid': False,
            'error': None,
            'width': None,
            'height': None,
            'size_bytes': None,
            'format': None
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['error'] = 'File does not exist'
                return result
            
            # Check file size
            file_size = os.path.getsize(file_path)
            result['size_bytes'] = file_size
            
            if file_size > self.MAX_FILE_SIZE:
                result['error'] = f'File size ({file_size/1024/1024:.2f}MB) exceeds maximum ({self.MAX_FILE_SIZE/1024/1024}MB)'
                return result
            
            # Check file extension
            ext = Path(file_path).suffix.lower().lstrip('.')
            if ext not in self.ALLOWED_EXTENSIONS:
                result['error'] = f'Invalid file extension: {ext}'
                return result
            
            # Open and validate image
            try:
                with Image.open(file_path) as img:
                    result['width'] = img.width
                    result['height'] = img.height
                    result['format'] = img.format
                    
                    # Verify image integrity
                    img.verify()
                    
                result['valid'] = True
                return result
                
            except Exception as img_error:
                result['error'] = f'Invalid or corrupted image: {str(img_error)}'
                return result
        
        except Exception as e:
            result['error'] = f'Validation error: {str(e)}'
            return result
    
    def compress_image(self, input_path, output_path, quality=None):
        """
        Compress and optimize image
        
        Args:
            input_path: Source image path
            output_path: Destination path
            quality: Compression quality (1-100)
            
        Returns:
            dict: Compression result with stats
        """
        result = {
            'success': False,
            'original_size': 0,
            'compressed_size': 0,
            'reduction_percent': 0,
            'error': None
        }
        
        try:
            quality = quality or self.config['compression_quality']
            original_size = os.path.getsize(input_path)
            result['original_size'] = original_size
            
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    if Path(output_path).suffix.lower() in ['.jpg', '.jpeg']:
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                
                # Resize if too large
                max_width = self.config['max_width']
                max_height = self.config['max_height']
                
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to {img.width}x{img.height}")
                
                # Save with compression
                save_kwargs = {
                    'quality': quality,
                    'optimize': True
                }
                
                if img.format == 'PNG':
                    save_kwargs = {'optimize': True, 'compress_level': 9}
                
                img.save(output_path, **save_kwargs)
            
            compressed_size = os.path.getsize(output_path)
            result['compressed_size'] = compressed_size
            result['reduction_percent'] = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
            result['success'] = True
            
            logger.info(f"Compressed {Path(input_path).name}: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({result['reduction_percent']:.1f}% reduction)")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error compressing image {input_path}: {e}")
        
        return result
    
    def create_thumbnail(self, input_path, output_path, size=None):
        """
        Create thumbnail from image
        
        Args:
            input_path: Source image
            output_path: Thumbnail destination
            size: Tuple of (width, height)
            
        Returns:
            bool: Success status
        """
        try:
            size = size or self.config['thumbnail_size']
            
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(output_path, quality=self.config['compression_quality'], optimize=True)
            
            logger.info(f"Created thumbnail: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False
    
    def detect_image_type(self, filename):
        """
        Detect image type from filename pattern
        
        Args:
            filename: Image filename
            
        Returns:
            str: 'main', 'gallery', or 'thumbnail'
        """
        filename_lower = filename.lower()
        
        # Main image patterns
        if any(pattern in filename_lower for pattern in ['main', 'primary', 'hero', 'cover', '_1.', '-1.']):
            return 'main'
        
        # Thumbnail patterns
        if any(pattern in filename_lower for pattern in ['thumb', 'thumbnail', 'small', 'preview']):
            return 'thumbnail'
        
        # Default to gallery
        return 'gallery'
    
    def generate_unique_filename(self, original_filename, prefix=''):
        """
        Generate unique filename with hash
        
        Args:
            original_filename: Original file name
            prefix: Optional prefix
            
        Returns:
            str: Unique filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = Path(original_filename).suffix
        base = Path(original_filename).stem
        
        # Create hash from original filename + timestamp
        hash_input = f"{base}_{timestamp}".encode('utf-8')
        hash_suffix = hashlib.md5(hash_input).hexdigest()[:8]
        
        if prefix:
            return f"{prefix}_{base}_{hash_suffix}{ext}"
        
        return f"{base}_{hash_suffix}{ext}"
    
    def batch_process_images(self, image_files, output_dir, compress=True):
        """
        Process multiple images in batch
        
        Args:
            image_files: List of image file paths
            output_dir: Output directory
            compress: Whether to compress images
            
        Returns:
            list: Results for each image
        """
        results = []
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, img_path in enumerate(image_files):
            try:
                # Validate
                validation = self.validate_image(img_path)
                
                if not validation['valid']:
                    results.append({
                        'filename': Path(img_path).name,
                        'success': False,
                        'error': validation['error']
                    })
                    continue
                
                # Generate output path
                unique_filename = self.generate_unique_filename(Path(img_path).name)
                output_path = os.path.join(output_dir, unique_filename)
                
                # Compress if enabled
                if compress:
                    compression_result = self.compress_image(img_path, output_path)
                    
                    results.append({
                        'filename': Path(img_path).name,
                        'stored_filename': unique_filename,
                        'success': compression_result['success'],
                        'original_size': compression_result['original_size'],
                        'compressed_size': compression_result['compressed_size'],
                        'width': validation['width'],
                        'height': validation['height'],
                        'image_type': self.detect_image_type(Path(img_path).name),
                        'error': compression_result.get('error')
                    })
                else:
                    # Just copy without compression
                    import shutil
                    shutil.copy2(img_path, output_path)
                    
                    results.append({
                        'filename': Path(img_path).name,
                        'stored_filename': unique_filename,
                        'success': True,
                        'original_size': validation['size_bytes'],
                        'width': validation['width'],
                        'height': validation['height'],
                        'image_type': self.detect_image_type(Path(img_path).name)
                    })
                
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
                results.append({
                    'filename': Path(img_path).name,
                    'success': False,
                    'error': str(e)
                })
        
        return results
