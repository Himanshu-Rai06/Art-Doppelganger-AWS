# Run: nohup python3 build_embeddings.py 400 > build.log 2>&1 &
# Needs yunet.onnx and sface.onnx in this folder. Watch progress with: tail -f build.log
import cv2, json, sys, time, urllib.parse, urllib.request, numpy as np
SEARCH_API = "https://collectionapi.metmuseum.org/public/collection/v1.1"
OBJECT_API = "https://collectionapi.metmuseum.org/public/collection/v1"
HDR = {"User-Agent": "Mozilla/5.0 (art-twin class project)"}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
QUERIES = ["portrait", "portrait of a man", "portrait of a woman", "lady", "gentleman",
           "young man", "young woman", "self-portrait", "boy", "girl", "head", "bust"]
DEPTS = [11, 1]  # European Paintings, American Wing

def get(u, tries=4):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=30).read()
        except Exception:
            time.sleep(1.5 * (k + 1))
    raise RuntimeError("failed " + u)

det = cv2.FaceDetectorYN.create("yunet.onnx", "", (320, 320), 0.7)
rec = cv2.FaceRecognizerSF.create("sface.onnx", "")
ids = []
for d in DEPTS:
    for q in QUERIES:
        try:
            r = json.loads(get(f"{SEARCH_API}/search?hasImages=true&isPublicDomain=true&departmentId={d}&q={urllib.parse.quote(q)}"))
            ids += r.get("objectIDs") or []
        except Exception as e:
            print("search skip", d, q)
ids = list(dict.fromkeys(ids))
print(len(ids), "candidates", flush=True)
vecs, meta = [], []
for n, i in enumerate(ids):
    if len(meta) >= N: break
    try:
        o = json.loads(get(f"{OBJECT_API}/objects/{i}"))
        if not o.get("isPublicDomain") or not o.get("primaryImageSmall"): continue
        if "Painting" not in (o.get("classification") or "Painting"): continue
        img = cv2.imdecode(np.frombuffer(get(o["primaryImageSmall"]), np.uint8), cv2.IMREAD_COLOR)
        h, w = img.shape[:2]; det.setInputSize((w, h)); _, faces = det.detect(img)
        if faces is None: continue
        f = max(faces, key=lambda f: f[2] * f[3])
        if f[2] < 40: continue
        v = rec.feature(rec.alignCrop(img, f)).flatten(); v /= np.linalg.norm(v)
        vecs.append(v)
        meta.append({"title": o["title"], "artist": o["artistDisplayName"], "date": o["objectDate"],
                     "image": o["primaryImageSmall"], "url": o["objectURL"]})
        if len(meta) % 25 == 0: print(len(meta), "kept,", n + 1, "checked", flush=True)
    except Exception as e:
        print("skip", i, type(e).__name__, flush=True)
    time.sleep(0.1)
np.save("embeddings.npy", np.array(vecs, dtype=np.float32)); json.dump(meta, open("meta.json", "w"))
print("done:", len(meta), "paintings")
