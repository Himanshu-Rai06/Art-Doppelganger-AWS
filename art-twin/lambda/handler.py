import base64, json, os
import cv2, numpy as np

D = os.path.dirname(os.path.abspath(__file__))
det = cv2.FaceDetectorYN.create(f"{D}/yunet.onnx", "", (320, 320), 0.7)
rec = cv2.FaceRecognizerSF.create(f"{D}/sface.onnx", "")
E = np.load(f"{D}/embeddings.npy")
with open(f"{D}/meta.json", encoding="utf-8") as f:
    M = json.load(f)
with open(f"{D}/index.html", encoding="utf-8") as f:
    PAGE = f.read()


def reply(code, body, ctype="application/json"):
    return {"statusCode": code, "headers": {"Content-Type": ctype, "Cache-Control": "no-store", "Access-Control-Allow-Origin": "*"}, "body": body}


def err(code, msg):
    return reply(code, json.dumps({"error": msg}))


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "GET":
        return reply(200, PAGE, "text/html; charset=utf-8")
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw)
        payload = json.loads(raw)
        img = cv2.imdecode(np.frombuffer(base64.b64decode(payload["image"].split(",")[-1]), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return err(400, "Could not read that photo. Try another one.")


        h, w = img.shape[:2]
        det.setInputSize((w, h))
        _, faces = det.detect(img)
        if faces is None:
            return err(200, "No face found. Try a clear, front-facing photo with good light.")
        face = max(faces, key=lambda f: f[2] * f[3])
        feat = rec.feature(rec.alignCrop(img, face)).flatten()
        feat = feat / np.linalg.norm(feat)
        sims = E @ feat
        top = np.argsort(sims)[::-1][:3]
        return reply(200, json.dumps({"matches": [dict(M[i], similarity=round(float(sims[i]) * 100, 1)) for i in top]}))
    except Exception:
        return err(400, "Could not read that photo. Try another one.")
