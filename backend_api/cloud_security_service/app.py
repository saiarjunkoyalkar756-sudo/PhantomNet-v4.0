# backend_api/cloud_security_service/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import boto3

logger = logging.getLogger(__name__)

app = FastAPI()

class AwsConfigCheck(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    resource_id: str = None # Optional, for specific resource checks

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Cloud Security Service is healthy"}

@app.post("/aws/misconfiguration")
async def detect_aws_misconfiguration(config_check: AwsConfigCheck):
    """
    Detects AWS cloud misconfigurations.
    This is a simplified example.
    """
    logger.info(f"Detecting AWS misconfigurations in region {config_check.region_name} for {config_check.resource_id or 'all resources'}")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=config_check.aws_access_key_id,
            aws_secret_access_key=config_check.aws_secret_access_key,
            region_name=config_check.region_name
        )
        response = s3.list_buckets()
        misconfigurations = []
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            # Simplified check: public access for any bucket
            try:
                acl = s3.get_bucket_acl(Bucket=bucket_name)
                for grant in acl['Grants']:
                    if 'URI' in grant['Grantee'] and 'AllUsers' in grant['Grantee']['URI']:
                        misconfigurations.append({
                            "type": "S3 Public Access",
                            "resource": bucket_name,
                            "severity": "HIGH",
                            "details": "S3 bucket is publicly accessible."
                        })
            except Exception as e:
                logger.warning(f"Could not get ACL for bucket {bucket_name}: {e}")
                
        return {"status": "success", "misconfigurations": misconfigurations}
    except Exception as e:
        logger.error(f"Error detecting AWS misconfigurations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AWS misconfiguration detection failed: {e}")

@app.post("/aws/iam_abuse")
async def detect_aws_iam_abuse(config_check: AwsConfigCheck):
    """
    Detects IAM role abuse.
    Placeholder for actual implementation.
    """
    logger.info(f"Detecting IAM abuse in AWS region {config_check.region_name}")
    # In a real scenario, this would involve analyzing CloudTrail logs,
    # IAM Access Analyzer findings, or custom policies.
    if "admin" in config_check.resource_id: # Example heuristic
        return {
            "status": "success",
            "alerts": [{
                "type": "IAM Role Abuse",
                "resource": config_check.resource_id,
                "severity": "CRITICAL",
                "details": "Highly privileged role detected with suspicious activity (placeholder)."
            }]
        }
    return {"status": "success", "alerts": []}

@app.post("/aws/s3_exposure")
async def detect_aws_s3_exposure(config_check: AwsConfigCheck):
    """
    Detects S3 bucket exposure.
    This can overlap with misconfiguration, but focuses specifically on public access.
    """
    logger.info(f"Detecting S3 bucket exposure in AWS region {config_check.region_name}")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=config_check.aws_access_key_id,
            aws_secret_access_key=config_check.aws_secret_access_key,
            region_name=config_check.region_name
        )
        response = s3.list_buckets()
        exposed_buckets = []
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                # Check Bucket Policy and ACL for public access
                policy_status = s3.get_bucket_policy_status(Bucket=bucket_name)
                if policy_status['PolicyStatus']['IsPublic']:
                    exposed_buckets.append({
                        "type": "S3 Public Policy",
                        "resource": bucket_name,
                        "severity": "HIGH",
                        "details": "S3 bucket has a public policy."
                    })
            except s3.exceptions.NoSuchBucketPolicy:
                pass # No bucket policy, not necessarily exposed

            try:
                acl = s3.get_bucket_acl(Bucket=bucket_name)
                for grant in acl['Grants']:
                    if 'URI' in grant['Grantee'] and 'AllUsers' in grant['Grantee']['URI']:
                        exposed_buckets.append({
                            "type": "S3 Public ACL",
                            "resource": bucket_name,
                            "severity": "HIGH",
                            "details": "S3 bucket has public ACL access."
                        })
            except Exception as e:
                logger.warning(f"Could not get ACL for bucket {bucket_name}: {e}")

        return {"status": "success", "exposed_buckets": exposed_buckets}
    except Exception as e:
        logger.error(f"Error detecting S3 bucket exposure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"S3 exposure detection failed: {e}")
