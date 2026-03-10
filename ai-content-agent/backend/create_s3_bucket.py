"""
Create S3 Bucket for Media Storage

This script creates the S3 bucket needed for storing campaign assets.
"""

import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def create_s3_bucket():
    """Create S3 bucket with public access for Instagram"""
    
    bucket_name = os.getenv('S3_BUCKET_NAME', 'ai-content-agent-assets')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"🪣 Creating S3 bucket: {bucket_name}")
    print(f"📍 Region: {region}\n")
    
    s3_client = boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    try:
        # Create bucket
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print(f"✅ Bucket created: {bucket_name}\n")
        
        # Disable Block Public Access
        print("🔓 Configuring public access...")
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        print("✅ Public access enabled\n")
        
        # Add bucket policy for public read
        print("📜 Adding bucket policy...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        import json
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✅ Bucket policy added\n")
        
        # Add CORS configuration
        print("🌐 Adding CORS configuration...")
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': []
                }
            ]
        }
        
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print("✅ CORS configured\n")
        
        print("="*60)
        print("🎉 S3 Bucket Setup Complete!")
        print("="*60)
        print(f"\nBucket Name: {bucket_name}")
        print(f"Region: {region}")
        print(f"Public Access: Enabled")
        print(f"CORS: Configured")
        print("\n✅ Ready to upload media files!")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'BucketAlreadyOwnedByYou':
            print(f"✅ Bucket already exists: {bucket_name}")
            print("   Updating configuration...\n")
            
            # Update configurations
            try:
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )
                print("✅ Public access enabled")
                
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicReadGetObject",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
                
                import json
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                print("✅ Bucket policy updated")
                
                print("\n✅ Bucket is ready!")
                return True
                
            except Exception as update_error:
                print(f"⚠️  Error updating configuration: {update_error}")
                return True  # Bucket exists, so return True
                
        elif error_code == 'BucketAlreadyExists':
            print(f"❌ Bucket name already taken by another AWS account")
            print(f"   Try a different bucket name in .env file")
            return False
        else:
            print(f"❌ Error creating bucket: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("S3 Bucket Creation")
    print("="*60 + "\n")
    
    success = create_s3_bucket()
    
    if success:
        print("\n✅ You can now upload campaign assets!")
    else:
        print("\n❌ Bucket creation failed. Check errors above.")
    
    exit(0 if success else 1)
