#!/bin/bash
# Deletes everything deploy.sh created
aws lambda delete-function --function-name art-twin
aws iam detach-role-policy --role-name art-twin-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name art-twin-role
echo "Deleted."
