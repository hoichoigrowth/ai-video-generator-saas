"""
MinIO initialization script
Creates buckets and sets up storage structure
"""

import asyncio
import logging
import json
from minio import Minio
from minio.error import S3Error
from config.settings import settings

logger = logging.getLogger(__name__)

class MinIOInitializer:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name

    def create_buckets(self):
        """Create all required buckets"""
        buckets = [
            {
                'name': self.bucket_name,
                'description': 'Main bucket for AI video generator files'
            },
            {
                'name': f"{self.bucket_name}-backups",
                'description': 'Backup bucket for critical files'
            }
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket['name']):
                    self.client.make_bucket(bucket['name'])
                    logger.info(f"Created bucket: {bucket['name']} - {bucket['description']}")
                else:
                    logger.info(f"Bucket already exists: {bucket['name']}")
            except S3Error as e:
                logger.error(f"Failed to create bucket {bucket['name']}: {e}")
                raise

    def create_folder_structure(self):
        """Create the folder structure in the main bucket"""
        folders = [
            'projects/',
            'projects/templates/',
            'exports/',
            'temp/',
            'backups/'
        ]
        
        # Create empty objects to represent folders
        for folder in folders:
            try:
                # Check if folder marker already exists
                objects = list(self.client.list_objects(self.bucket_name, prefix=folder, max_keys=1))
                if not objects:
                    # Create an empty file to represent the folder
                    self.client.put_object(
                        self.bucket_name,
                        folder + '.keep',
                        data=b'',
                        length=0,
                        content_type='application/octet-stream'
                    )
                    logger.info(f"Created folder: {folder}")
                else:
                    logger.info(f"Folder already exists: {folder}")
            except S3Error as e:
                logger.error(f"Failed to create folder {folder}: {e}")
                raise

    def set_bucket_policies(self):
        """Set bucket policies for proper access"""
        # Public read policy for images and videos (optional)
        public_read_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/projects/*/scenes/*"
                },
                {
                    "Effect": "Allow", 
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/projects/*/characters/*"
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject", 
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/projects/*/videos/*"
                }
            ]
        }
        
        try:
            # Only set policy if we want public access (optional)
            if settings.environment == "development":
                self.client.set_bucket_policy(
                    self.bucket_name,
                    json.dumps(public_read_policy)
                )
                logger.info("Set bucket policy for public read access to media files")
            else:
                logger.info("Skipping public bucket policy in production")
        except S3Error as e:
            # Policy setting might fail in some MinIO configurations, but that's okay
            logger.warning(f"Could not set bucket policy (this may be normal): {e}")

    def create_sample_files(self):
        """Create sample files for testing"""
        sample_files = [
            {
                'path': 'projects/templates/sample_script.txt',
                'content': '''# Sample AI Video Script

## Scene 1: Introduction
A young entrepreneur walks into a bustling coffee shop, laptop in hand, ready to change the world with their innovative idea.

## Scene 2: The Pitch
Standing before a room of investors, they present their vision with passion and conviction.

## Scene 3: Success
Months later, their product launches to widespread acclaim, transforming lives across the globe.
''',
                'content_type': 'text/plain'
            },
            {
                'path': 'projects/templates/README.md',
                'content': '''# AI Video Generator Templates

This folder contains template files for the AI Video Generator:

- `sample_script.txt` - Example script format
- `character_template.json` - Character design template
- `production_template.json` - Production plan template

## Usage

1. Upload your script in the supported format
2. The AI will generate a screenplay
3. Shot division will be created automatically
4. Characters will be extracted and designs generated
5. Scenes will be rendered using Midjourney
6. Final video will be generated using Kling AI

## File Formats Supported

- `.txt` - Plain text scripts
- `.md` - Markdown formatted scripts  
- `.rtf` - Rich text format
- `.doc/.docx` - Microsoft Word documents

All files are stored securely in MinIO object storage.
''',
                'content_type': 'text/markdown'
            }
        ]
        
        for file_info in sample_files:
            try:
                # Check if file already exists
                try:
                    self.client.stat_object(self.bucket_name, file_info['path'])
                    logger.info(f"Sample file already exists: {file_info['path']}")
                    continue
                except S3Error:
                    pass  # File doesn't exist, create it
                
                # Create the sample file
                content_bytes = file_info['content'].encode('utf-8')
                self.client.put_object(
                    self.bucket_name,
                    file_info['path'],
                    data=content_bytes,
                    length=len(content_bytes),
                    content_type=file_info['content_type']
                )
                logger.info(f"Created sample file: {file_info['path']}")
                
            except S3Error as e:
                logger.error(f"Failed to create sample file {file_info['path']}: {e}")

    def verify_setup(self):
        """Verify MinIO setup is working correctly"""
        try:
            # Test bucket access
            if not self.client.bucket_exists(self.bucket_name):
                raise Exception(f"Main bucket {self.bucket_name} does not exist")
            
            # Test file operations
            test_content = b"MinIO test file"
            test_path = "temp/setup_test.txt"
            
            # Upload test file
            self.client.put_object(
                self.bucket_name,
                test_path,
                data=test_content,
                length=len(test_content),
                content_type='text/plain'
            )
            
            # Download test file
            response = self.client.get_object(self.bucket_name, test_path)
            downloaded_content = response.read()
            
            if downloaded_content != test_content:
                raise Exception("File upload/download verification failed")
            
            # Clean up test file
            self.client.remove_object(self.bucket_name, test_path)
            
            # List objects to verify structure
            objects = list(self.client.list_objects(self.bucket_name, recursive=True))
            logger.info(f"MinIO verification successful: {len(objects)} objects found")
            
            # Display folder structure
            folders = set()
            for obj in objects:
                parts = obj.object_name.split('/')
                if len(parts) > 1:
                    folders.add(parts[0] + '/')
            
            logger.info(f"Folder structure: {sorted(folders)}")
            
        except Exception as e:
            logger.error(f"MinIO verification failed: {e}")
            raise

def main():
    """Main initialization function"""
    logger.info("Starting MinIO initialization...")
    
    try:
        initializer = MinIOInitializer()
        
        # Step 1: Create buckets
        logger.info("Creating buckets...")
        initializer.create_buckets()
        
        # Step 2: Create folder structure
        logger.info("Creating folder structure...")
        initializer.create_folder_structure()
        
        # Step 3: Set bucket policies
        logger.info("Setting bucket policies...")
        initializer.set_bucket_policies()
        
        # Step 4: Create sample files
        logger.info("Creating sample files...")
        initializer.create_sample_files()
        
        # Step 5: Verify setup
        logger.info("Verifying setup...")
        initializer.verify_setup()
        
        logger.info("MinIO initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"MinIO initialization failed: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the initialization
    main()