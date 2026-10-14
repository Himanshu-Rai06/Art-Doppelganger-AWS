# Run once: python3 build_embeddings.py 600   (needs yunet.onnx and sface.onnx in this folder)
import cv2, json, sys, time, urllib.request, numpy as np
API = "https://collectionapi.metmuseum.org/public/collection/v1"
HDR = {"User-Agent": "art-twin-class-project"}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=30).read()
det = cv2.FaceDetectorYN.create("yunet.onnx", "", (320, 320), 0.7)
rec = cv2.FaceRecognizerSF.create("sface.onnx", "")
ids = json.loads(get(f"{API}/search?hasImages=true&isPublicDomain=true&departmentId=11&q=portrait"))["objectIDs"]
print(len(ids), "candidates")
vecs, meta = [], []
for n, i in enumerate(ids):
    if len(meta) >= N: break
    try:
        o = json.loads(get(f"{API}/objects/{i}"))
        if not o.get("isPublicDomain") or not o.get("primaryImageSmall") or "Painting" not in o.get("classification", "Painting"): continue
        img = cv2.imdecode(np.frombuffer(get(o["primaryImageSmall"]), np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]; det.setInputSize((w, h)); _, faces = det.detect(img)
        if faces is None: continue
        f = max(faces, key=lambda f: f[2] * f[3])
        if f[2] < 40: continue
        v = rec.feature(rec.alignCrop(img, f)).flatten(); v /= np.linalg.norm(v)
        vecs.append(v); meta.append({"title": o["title"], "artist": o["artistDisplayName"], "date": o["objectDate"], "image": o["primaryImageSmall"], "url": o["objectURL"]})
        if len(meta) % 25 == 0: print(len(meta), "faces kept,", n + 1, "checked")
    except Exception as e:
        print("skip", i, type(e).__name__)
    time.sleep(0.05)
np.save("embeddings.npy", np.array(vecs, dtype=np.float32)); json.dump(meta, open("meta.json", "w"))
print("done:", len(meta), "paintings")
