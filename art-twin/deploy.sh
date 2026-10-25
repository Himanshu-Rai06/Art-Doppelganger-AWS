#!/bin/bash
# Run in AWS CloudShell from the repo folder: bash deploy.sh
set -e; cd "$(dirname "$0")"
FN=art-twin; ROLE=art-twin-role
ACC=$(aws sts get-caller-identity --query Account --output text)
Z=https://github.com/opencv/opencv_zoo/raw/main/models
[ -f yunet.onnx ] || curl -sL -o yunet.onnx $Z/face_detection_yunet/face_detection_yunet_2023mar.onnx
[ -f sface.onnx ] || curl -sL -o sface.onnx $Z/face_recognition_sface/face_recognition_sface_2021dec.onnx
[ $(stat -c %s sface.onnx) -gt 1000000 ] || { echo "model download failed, check internet and delete the .onnx files"; exit 1; }
[ -f embeddings.npy ] || { echo "embeddings.npy missing, run build_embeddings.py first"; exit 1; }
rm -rf build function.zip && mkdir build
pip install -q --target build --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp "opencv-python-headless==4.10.0.84" "numpy<2"
find build -name tests -type d -prune -exec rm -rf {} + ; find build -name __pycache__ -type d -prune -exec rm -rf {} + ; find build -name "*.pyi" -delete; rm -rf build/numpy/f2py build/numpy/distutils build/bin
find lambda -maxdepth 1 -type f -exec cp {} build/ \;
cp yunet.onnx sface.onnx embeddings.npy meta.json build/
(cd build && zip -qr ../function.zip .)
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  sleep 12
fi
B=art-twin-$ACC-tmp
aws s3 mb s3://$B >/dev/null 2>&1 || true; aws s3 cp function.zip s3://$B/function.zip
if aws lambda get-function --function-name $FN >/dev/null 2>&1; then
  aws lambda update-function-code --function-name $FN --s3-bucket $B --s3-key function.zip >/dev/null
else
  aws lambda create-function --function-name $FN --runtime python3.12 --handler handler.lambda_handler \
    --role arn:aws:iam::$ACC:role/$ROLE --code S3Bucket=$B,S3Key=function.zip --memory-size 1024 --timeout 30 >/dev/null
  aws lambda wait function-active-v2 --function-name $FN
  aws lambda create-function-url-config --function-name $FN --auth-type NONE >/dev/null
  aws lambda add-permission --function-name $FN --statement-id url1 --action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE >/dev/null
  aws lambda add-permission --function-name $FN --statement-id url2 --action lambda:InvokeFunction --principal '*' --invoked-via-function-url >/dev/null 2>&1 || true
fi
aws s3 rb s3://$B --force >/dev/null
aws lambda put-function-concurrency --function-name $FN --reserved-concurrent-executions 5 >/dev/null 2>&1 || echo "(concurrency cap not set, fine for a class demo)"
echo; echo "LIVE AT:"; aws lambda get-function-url-config --function-name $FN --query FunctionUrl --output text
