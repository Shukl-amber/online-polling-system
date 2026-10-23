#!/usr/bin/env python3
"""Script to build the frontend, upload to S3, and invalidate CloudFront cache.

Workflow:
1. Runs 'npm run build' inside frontend/
2. Resolves S3 bucket and CloudFront distribution ID from SSM or flags
3. Uploads dist/ files with exact Content-Type headers
4. Issues a CloudFront invalidation for '/*'

Usage:
    python scripts/publish_frontend.py [--region ap-south-1] [--skip-build]
"""

from __future__ import annotations

import argparse
import mimetypes
import subprocess
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def get_ssm_parameter(ssm_client: boto3.client, name: str) -> str | None:
    """Fetch a parameter from SSM Parameter Store."""
    try:
        response = ssm_client.get_parameter(Name=name, WithDecryption=False)
        return response["Parameter"]["Value"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ParameterNotFound":
            return None
        raise


def run_build(frontend_dir: Path) -> None:
    """Run npm run build in frontend directory."""
    print("Building production bundle with npm run build...")
    # On Windows npm is npm.cmd
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run([npm_cmd, "run", "build"], cwd=frontend_dir, check=False)
    if result.returncode != 0:
        print("Frontend build failed", file=sys.stderr)
        sys.exit(1)
    print("Frontend build succeeded.")


def upload_dist_to_s3(s3_client: boto3.client, bucket_name: str, dist_dir: Path) -> int:
    """Upload all files from dist_dir to S3 with correct content types."""
    print(f"Uploading files to s3://{bucket_name}...")
    count = 0
    for file_path in dist_dir.rglob("*"):
        if file_path.is_file():
            key = file_path.relative_to(dist_dir).as_posix()
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                if file_path.suffix == ".woff2":
                    content_type = "font/woff2"
                elif file_path.suffix == ".woff":
                    content_type = "font/woff"
                else:
                    content_type = "application/octet-stream"

            extra_args = {"ContentType": content_type}
            # Cache immutable assets for 1 year, html for 0
            if key.startswith("assets/"):
                extra_args["CacheControl"] = "public, max-age=31536000, immutable"
            else:
                extra_args["CacheControl"] = "public, max-age=0, must-revalidate"

            s3_client.upload_file(
                Filename=str(file_path),
                Bucket=bucket_name,
                Key=key,
                ExtraArgs=extra_args,
            )
            count += 1
    print(f"Uploaded {count} files to S3.")
    return count


def invalidate_cloudfront(cf_client: boto3.client, distribution_id: str) -> str:
    """Create a CloudFront invalidation for /*."""
    print(f"Creating CloudFront invalidation for distribution {distribution_id}...")
    caller_reference = f"publish-{int(time.time())}"
    res = cf_client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {
                "Quantity": 1,
                "Items": ["/*"],
            },
            "CallerReference": caller_reference,
        },
    )
    invalidation_id = res["Invalidation"]["Id"]
    print(f"Invalidation created: {invalidation_id}")
    return invalidation_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish frontend to S3 and invalidate CloudFront")
    parser.add_argument(
        "--region",
        default="ap-south-1",
        help="AWS region (default: ap-south-1)",
    )
    parser.add_argument(
        "--bucket",
        help="Target S3 bucket name (defaults to SSM parameter)",
    )
    parser.add_argument(
        "--distribution-id",
        help="CloudFront distribution ID (defaults to SSM parameter)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip npm run build step",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    frontend_dir = repo_root / "frontend"
    dist_dir = frontend_dir / "dist"

    if not args.skip_build:
        run_build(frontend_dir)

    if not dist_dir.exists():
        print(f"Error: {dist_dir} does not exist. Run build first.", file=sys.stderr)
        sys.exit(1)

    region = args.region
    ssm = boto3.client("ssm", region_name=region)
    s3 = boto3.client("s3", region_name=region)
    cf = boto3.client("cloudfront")

    def get_fallback(*names: str) -> str | None:
        for n in names:
            val = get_ssm_parameter(ssm, n)
            if val:
                return val
        return None

    bucket_name = args.bucket or get_fallback(
        "/polling_system/frontend_bucket_name",
        "/polling_system/hosting/bucket_name",
    )
    distribution_id = args.distribution_id or get_fallback(
        "/polling_system/distribution_id",
        "/polling_system/hosting/distribution_id",
    )

    if not bucket_name:
        print("Error: Target S3 bucket not found in SSM or arguments.", file=sys.stderr)
        sys.exit(1)

    upload_dist_to_s3(s3, bucket_name, dist_dir)

    if distribution_id:
        invalidate_cloudfront(cf, distribution_id)
    else:
        print("Warning: CloudFront distribution ID not provided, skipping invalidation.")

    print("Publish complete.")


if __name__ == "__main__":
    main()
