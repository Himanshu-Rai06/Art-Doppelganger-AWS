import base64, json, os
import cv2, numpy as np

D = os.path.dirname(os.path.abspath(__file__))
det = cv2.FaceDetectorYN.create(f"{D}/yunet.onnx", "", (320, 320), 0.7)
rec = cv2.FaceRecognizerSF.create(f"{D}/sface.onnx", "")
E = np.load(f"{D}/embeddings.npy")
M = json.load(open(f"{D}/meta.json"))
PAGE = open(f"{D}/index.html", encoding="utf-8").read()


def reply(code, body, ctype="application/json"):
    return {"statusCode": code, "headers": {"Content-Type": ctype, "Cache-Control": "no-store"}, "body": body}


def lambda_handler(event, context):
    if event["requestContext"]["http"]["method"] == "GET":
        return reply(200, PAGE, "text/html; charset=utf-8")
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw)
        b64 = json.loads(raw)["image"].split(",")[-1]
        img = cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
        det.setInputSize((w, h))
        _, faces = det.detect(img)
        if faces is None:
            return reply(200, json.dumps({"error": "No face found. Try a clear, front-facing photo with good light."}))
        face = max(faces, key=lambda f: f[2] * f[3])
        feat = rec.feature(rec.alignCrop(img, face)).flatten()
        feat = feat / np.linalg.norm(feat)
        sims = E @ feat
        top = np.argsort(sims)[::-1][:3]
        out = [dict(M[i], similarity=round(float(sims[i]) * 100, 1)) for i in top]
        return reply(200, json.dumps({"matches": out}))
    except Exception:
        return reply(400, json.dumps({"error": "Could not read that photo. Try another one."}))
