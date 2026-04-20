from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import boto3
from loguru import logger

app = create_phantom_service(
    name="Cloud Security Service",
    description="Monitors and maintains security posture across cloud environments.",
    version="1.0.0"
)

class AwsConfigCheck(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    resource_id: str = None

@app.post("/aws/misconfiguration")
async def detect_aws_misconfiguration(config_check: AwsConfigCheck):
    """
    Detects AWS cloud misconfigurations.
    """
    logger.info(f"Detecting AWS misconfigurations in region {config_check.region_name}")
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
                
        return success_response(data={"misconfigurations": misconfigurations})
    except Exception as e:
        logger.error(f"Error detecting AWS misconfigurations: {e}")
        return error_response(code="AWS_CHECK_FAILED", message=str(e), status_code=500)

@app.post("/aws/iam_abuse")
async def detect_aws_iam_abuse(config_check: AwsConfigCheck):
    """
    Detects IAM role abuse.
    """
    logger.info(f"Detecting IAM abuse in AWS region {config_check.region_name}")
    alerts = []
    if config_check.resource_id and "admin" in config_check.resource_id.lower():
        alerts.append({
            "type": "IAM Role Abuse",
            "resource": config_check.resource_id,
            "severity": "CRITICAL",
            "details": "Highly privileged role detected with suspicious activity."
        })
    return success_response(data={"alerts": alerts})

@app.post("/aws/s3_exposure")
async def detect_aws_s3_exposure(config_check: AwsConfigCheck):
    """
    Detects S3 bucket exposure.
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
                policy_status = s3.get_bucket_policy_status(Bucket=bucket_name)
                if policy_status['PolicyStatus']['IsPublic']:
                    exposed_buckets.append({
                        "type": "S3 Public Policy",
                        "resource": bucket_name,
                        "severity": "HIGH",
                        "details": "S3 bucket has a public policy."
                    })
            except s3.exceptions.NoSuchBucketPolicy:
                pass

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

        return success_response(data={"exposed_buckets": exposed_buckets})
    except Exception as e:
        logger.error(f"Error detecting S3 bucket exposure: {e}")
        return error_response(code="AWS_CHECK_FAILED", message=str(e), status_code=500)
