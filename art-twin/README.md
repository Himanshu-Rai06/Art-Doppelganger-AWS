# Art Twin
Upload a selfie, find the Met Museum portrait that looks most like you. Serverless: one AWS Lambda function serves the page and does the face matching. Idle cost is zero and photos are never stored.

## One-time prep (do before class)
1. AWS Console, open **CloudShell** (icon in the top bar). [SCREENSHOT 1: CloudShell open]
2. `git clone <your-repo-url> && cd art-twin`
3. Download the two models and build the painting database (about 15 min, run once):
   ```
   Z=https://github.com/opencv/opencv_zoo/raw/main/models
   curl -sL -o yunet.onnx $Z/face_detection_yunet/face_detection_yunet_2023mar.onnx
   curl -sL -o sface.onnx $Z/face_recognition_sface/face_recognition_sface_2021dec.onnx
   pip install --user opencv-python-headless==4.10.0.84 "numpy<2"
   python3 build_embeddings.py 600
   ```
   [SCREENSHOT 2: output ending in "done: N paintings"]
4. Download `embeddings.npy` and `meta.json` (CloudShell, Actions > Download file), put them in the repo on your computer and push. Or run `git add embeddings.npy meta.json && git commit -m data && git push` from CloudShell if you set up git login.

## Deploy (3 to 4 minutes, also the class-day rebuild)
```
git clone <your-repo-url> && cd art-twin   # skip if already there
bash deploy.sh
```
It prints `LIVE AT: https://....lambda-url.<region>.on.aws/`. Open it on your phone.
[SCREENSHOT 3: terminal showing LIVE AT url]
[SCREENSHOT 4: Lambda console, art-twin function, Function URL visible]
[SCREENSHOT 5: the web page with your own result]

## Class day
Open the URL, show it as a QR code (any free QR generator) on the projector. Optional: Lambda console > Monitor tab shows requests live. [SCREENSHOT 6: Monitor graph after the class has used it]

## After
`bash teardown.sh` deletes everything.
