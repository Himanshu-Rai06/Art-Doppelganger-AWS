# Manual setup on AWS

These are the steps used to build the project by hand. Console menus change, so treat the names as a guide.

## 1. Secure the account
1. Turn on MFA for the root user (IAM dashboard).
2. Create an IAM admin user for daily work and sign in as that user.
3. Billing > Budgets: create a small monthly budget with an email alert.

## 2. Launch the EC2 build machine
- Region: Asia Pacific (Mumbai), ap-south-1. Use one region for everything.
- AMI: Ubuntu Server. Type: t3.micro. Storage: 8 GB.
- Create a key pair (.pem) and keep it safe. It cannot be downloaded again.
- Security group: SSH (22) from My IP only. If SSH later times out, your IP probably changed, so update the rule.

## 3. Give the machine permission to deploy
IAM > Roles > Create role > AWS service > EC2, attach the permissions needed to create Lambda functions, IAM roles and S3 buckets (an admin policy is simplest for a throwaway project). Attach it to the instance (Actions > Security > Modify IAM role). Delete the role when finished.

## 4. Connect
```powershell
ssh -i "KeyEC2.pem" ubuntu@<public-ip>
```
On Linux or Mac run `chmod 400 KeyEC2.pem` first. On Windows PowerShell this is not needed.

## 5. Install tools
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv unzip zip curl git -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip && unzip -q awscliv2.zip && sudo ./aws/install
export AWS_DEFAULT_REGION=ap-south-1
python3 -m venv venv && source venv/bin/activate
pip install opencv-python-headless numpy
```
(AWS CloudShell would remove the need for the EC2 machine, but it can be unavailable while a new account is being verified.)

## 6. Models and dataset
```bash
git clone https://github.com/<your-username>/<your-repo>.git && cd <your-repo>
Z=https://github.com/opencv/opencv_zoo/raw/main/models
curl -sL -o yunet.onnx $Z/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -sL -o sface.onnx $Z/face_recognition_sface/face_recognition_sface_2021dec.onnx
python3 build_embeddings.py 400      # run with nohup if the connection may drop
```

## 7. Deploy
```bash
bash deploy.sh
```
Open the printed URL on a phone. Test with a clear, front-facing photo.

## 8. Shut everything down
1. `bash teardown.sh` (Lambda function and its role).
2. EC2: terminate the instance, release any Elastic IPs, delete unattached volumes.
3. IAM: delete the build machine's role and instance profile.
4. S3: confirm the temporary bucket is gone. CloudWatch: delete the function's log group.
5. Check Billing the next day. Public IPv4 addresses and forgotten instances are the usual surprise charges.

## Problems met and fixes
| Problem | Fix |
|---|---|
| CloudShell blocked (new account) | Used EC2 with an IAM role as the deploy machine |
| OpenCV import failed | Recreated the virtual environment and reinstalled |
| Python 3.12 not on the EC2 OS | Dataset built with the available Python; Lambda package built for 3.12 |
| Met API requests failing | Adjusted requests, skipped bad records, retries |
| Package near Lambda's 250 MB limit | Pinned OpenCV 4.10.0.84, numpy<2, removed test files |
| S3 `-q` option and existing bucket errors in deploy script | Removed the option, tolerate an existing bucket |
