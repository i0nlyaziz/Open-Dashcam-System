# Model Weights

`yolo26n.pt` and `yolo26n-depth.pt` are the stock pretrained YOLO26 models used by this project — no custom training was done. They aren't committed directly to this repo (see `.gitignore`); instead, they're attached to this repo's Releases so anyone cloning it gets the exact same model files without relying on Ultralytics' automatic download at runtime.

## Download

- **yolo26n.pt** — [Download from Releases](https://github.com/i0nlyaziz/Open-Dashcam-System/releases/download/v1.0/yolo26n.pt)
- **yolo26n-depth.pt** — [Download from Releases](https://github.com/i0nlyaziz/Open-Dashcam-System/releases/download/v1.0/yolo26n-depth.pt)

## Using the weights

1. Download both files from the links above and place them in this `weights/` folder.
2. `main.py` loads them directly by filename — no export step is required.
3. To use different or custom-trained models instead (e.g. a model that identifies vehicle brand), replace either file and point `main.py` at your own weights — see the Project Philosophy section in the main README for how this project is meant to be extended.