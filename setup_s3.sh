#!/bin/bash
set -e
if [ -z "$AWS_ACCESS_KEY" ] || [ -z "$AWS_SECRET_KEY" ] || [ -z "$S3_BUCKET" ]; then
  echo "Please set AWS_ACCESS_KEY, AWS_SECRET_KEY and S3_BUCKET."
  exit 1
fi
aws configure set aws_access_key_id $AWS_ACCESS_KEY
aws configure set aws_secret_access_key $AWS_SECRET_KEY
aws configure set default.region ${S3_REGION:-us-east-1}
aws s3 mb s3://$S3_BUCKET --region ${S3_REGION:-us-east-1} || true
cat > /tmp/s3_policy.json <<POL
{
  "Version":"2012-10-17",
  "Statement":[{
    "Sid":"PublicReadGetObject",
    "Effect":"Allow",
    "Principal": "*",
    "Action":["s3:GetObject"],
    "Resource":["arn:aws:s3:::$S3_BUCKET/*"]
  }]
}
POL
aws s3api put-bucket-policy --bucket $S3_BUCKET --policy file:///tmp/s3_policy.json || true
echo "S3 setup done."
