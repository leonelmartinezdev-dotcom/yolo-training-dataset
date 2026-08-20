const BOX_COLORS = [
  "#e06c75", "#98c379", "#61afef", "#e5c07b", "#c678dd",
  "#56b6c2", "#d19a66", "#be5046", "#528bff", "#98c379",
];

const HANDLE_SCREEN_PX = 8;
const MIN_BOX_IMAGE_PX = 4;

class BoxCanvas {
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext("2d");

    this.image = null;
    this.imgW = 0;
    this.imgH = 0;

    this.boxes = [];
    this.selectedIndex = -1;

    this.zoom = 1;
    this.offsetX = 0;
    this.offsetY = 0;

    this.lastUsedClass = 0;

    this.onBoxesChanged = () => {};
    this.onSelectionChanged = () => {};

    this._drag = null; // {mode: 'draw'|'move'|'resize'|'pan', ...}
    this._spaceHeld = false;

    this._bindEvents();
  }

  setClassNames(names) {
    this.classNames = names;
  }

  loadImage(url, boxes) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.image = img;
        this.imgW = img.naturalWidth;
        this.imgH = img.naturalHeight;
        this.boxes = boxes.map((b) => ({ ...b }));
        this.selectedIndex = -1;
        this._resizeCanvasToContainer();
        this._fitToView();
        this._redraw();
        this.onSelectionChanged(-1);
        resolve();
      };
      img.onerror = reject;
      img.src = url;
    });
  }

  getBoxes() {
    return this.boxes.map((b) => ({ ...b }));
  }

  deleteSelected() {
    if (this.selectedIndex < 0) return;
    this.boxes.splice(this.selectedIndex, 1);
    this.selectedIndex = -1;
    this._redraw();
    this.onBoxesChanged();
    this.onSelectionChanged(-1);
  }

  selectIndex(i) {
    this.selectedIndex = i;
    this._redraw();
    this.onSelectionChanged(i);
  }

  setClassOfSelected(classId) {
    if (this.selectedIndex < 0) return;
    this.boxes[this.selectedIndex].class_id = classId;
    this.lastUsedClass = classId;
    this._redraw();
    this.onBoxesChanged();
  }

  cycleClassOfSelected(delta) {
    if (this.selectedIndex < 0 || !this.classNames || !this.classNames.length) return;
    const n = this.classNames.length;
    const box = this.boxes[this.selectedIndex];
    box.class_id = ((box.class_id + delta) % n + n) % n;
    this.lastUsedClass = box.class_id;
    this._redraw();
    this.onBoxesChanged();
  }

  deselect() {
    if (this._drag && this._drag.mode === "draw") {
      this._drag = null;
    }
    this.selectedIndex = -1;
    this._redraw();
    this.onSelectionChanged(-1);
  }

  resizeCanvas() {
    if (!this.image) return;
    this._resizeCanvasToContainer();
    this._redraw();
  }

  _resizeCanvasToContainer() {
    const wrap = this.canvas.parentElement;
    this.canvas.width = wrap.clientWidth;
    this.canvas.height = wrap.clientHeight;
  }

  _fitToView() {
    const baseScale = Math.min(this.canvas.width / this.imgW, this.canvas.height / this.imgH);
    this.zoom = 1;
    this._baseScale = baseScale;
    this.offsetX = (this.canvas.width - this.imgW * baseScale) / 2;
    this.offsetY = (this.canvas.height - this.imgH * baseScale) / 2;
  }

  _effectiveScale() {
    return this._baseScale * this.zoom;
  }

  _screenToImage(sx, sy) {
    const s = this._effectiveScale();
    return { x: (sx - this.offsetX) / s, y: (sy - this.offsetY) / s };
  }

  _imageToScreen(ix, iy) {
    const s = this._effectiveScale();
    return { x: ix * s + this.offsetX, y: iy * s + this.offsetY };
  }

  _boxToImagePx(box) {
    const left = (box.x_center - box.width / 2) * this.imgW;
    const top = (box.y_center - box.height / 2) * this.imgH;
    return { left, top, w: box.width * this.imgW, h: box.height * this.imgH };
  }

  _redraw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.image) return;

    const s = this._effectiveScale();
    ctx.drawImage(this.image, this.offsetX, this.offsetY, this.imgW * s, this.imgH * s);

    this.boxes.forEach((box, i) => {
      const { left, top, w, h } = this._boxToImagePx(box);
      const p1 = this._imageToScreen(left, top);
      const p2 = this._imageToScreen(left + w, top + h);
      const color = BOX_COLORS[box.class_id % BOX_COLORS.length];
      const selected = i === this.selectedIndex;

      ctx.strokeStyle = color;
      ctx.lineWidth = selected ? 3 : 2;
      ctx.strokeRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);

      const label = this.classNames && this.classNames[box.class_id] ? this.classNames[box.class_id] : String(box.class_id);
      ctx.font = "12px sans-serif";
      const textW = ctx.measureText(label).width + 6;
      ctx.fillStyle = color;
      ctx.fillRect(p1.x, p1.y - 16, textW, 16);
      ctx.fillStyle = "#111";
      ctx.fillText(label, p1.x + 3, p1.y - 4);

      if (selected) {
        ctx.fillStyle = color;
        const handles = this._handlePositions(p1, p2);
        Object.values(handles).forEach((h) => {
          ctx.fillRect(h.x - 4, h.y - 4, 8, 8);
        });
      }
    });

    if (this._drag && this._drag.mode === "draw") {
      const { startImg, curImg } = this._drag;
      const p1 = this._imageToScreen(Math.min(startImg.x, curImg.x), Math.min(startImg.y, curImg.y));
      const p2 = this._imageToScreen(Math.max(startImg.x, curImg.x), Math.max(startImg.y, curImg.y));
      ctx.strokeStyle = "#fff";
      ctx.setLineDash([4, 3]);
      ctx.strokeRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
      ctx.setLineDash([]);
    }
  }

  _handlePositions(p1, p2) {
    const midX = (p1.x + p2.x) / 2;
    const midY = (p1.y + p2.y) / 2;
    return {
      nw: { x: p1.x, y: p1.y }, n: { x: midX, y: p1.y }, ne: { x: p2.x, y: p1.y },
      w: { x: p1.x, y: midY }, e: { x: p2.x, y: midY },
      sw: { x: p1.x, y: p2.y }, s: { x: midX, y: p2.y }, se: { x: p2.x, y: p2.y },
    };
  }

  _hitHandle(sx, sy) {
    if (this.selectedIndex < 0) return null;
    const box = this.boxes[this.selectedIndex];
    const { left, top, w, h } = this._boxToImagePx(box);
    const p1 = this._imageToScreen(left, top);
    const p2 = this._imageToScreen(left + w, top + h);
    const handles = this._handlePositions(p1, p2);
    for (const [name, pos] of Object.entries(handles)) {
      if (Math.abs(sx - pos.x) <= HANDLE_SCREEN_PX && Math.abs(sy - pos.y) <= HANDLE_SCREEN_PX) {
        return name;
      }
    }
    return null;
  }

  _hitTestBox(ix, iy) {
    let bestIndex = -1;
    let bestArea = Infinity;
    this.boxes.forEach((box, i) => {
      const { left, top, w, h } = this._boxToImagePx(box);
      if (ix >= left && ix <= left + w && iy >= top && iy <= top + h) {
        const area = w * h;
        if (area < bestArea) {
          bestArea = area;
          bestIndex = i;
        }
      }
    });
    return bestIndex;
  }

  _clampImagePoint(p) {
    return { x: Math.min(Math.max(p.x, 0), this.imgW), y: Math.min(Math.max(p.y, 0), this.imgH) };
  }

  _bindEvents() {
    const canvas = this.canvas;

    window.addEventListener("keydown", (e) => {
      if (e.code === "Space") this._spaceHeld = true;
    });
    window.addEventListener("keyup", (e) => {
      if (e.code === "Space") this._spaceHeld = false;
    });

    canvas.addEventListener("wheel", (e) => {
      if (!this.image) return;
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      const before = this._screenToImage(sx, sy);

      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      this.zoom = Math.min(Math.max(this.zoom * factor, 0.2), 15);

      const after = this._screenToImage(sx, sy);
      const s = this._effectiveScale();
      this.offsetX += (after.x - before.x) * s;
      this.offsetY += (after.y - before.y) * s;

      this._redraw();
    }, { passive: false });

    canvas.addEventListener("mousedown", (e) => {
      if (!this.image) return;
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      if (this._spaceHeld || e.button === 1) {
        this._drag = { mode: "pan", startSx: sx, startSy: sy, startOffsetX: this.offsetX, startOffsetY: this.offsetY };
        return;
      }

      const handle = this._hitHandle(sx, sy);
      if (handle) {
        this._drag = { mode: "resize", handle, box: { ...this.boxes[this.selectedIndex] } };
        return;
      }

      const imgPt = this._clampImagePoint(this._screenToImage(sx, sy));
      const hit = this._hitTestBox(imgPt.x, imgPt.y);

      if (hit >= 0) {
        this.selectIndex(hit);
        const box = this.boxes[hit];
        const { left, top } = this._boxToImagePx(box);
        this._drag = { mode: "move", grabOffset: { x: imgPt.x - left, y: imgPt.y - top } };
      } else {
        this.selectIndex(-1);
        this._drag = { mode: "draw", startImg: imgPt, curImg: imgPt };
      }
    });

    canvas.addEventListener("mousemove", (e) => {
      if (!this.image || !this._drag) return;
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      if (this._drag.mode === "pan") {
        this.offsetX = this._drag.startOffsetX + (sx - this._drag.startSx);
        this.offsetY = this._drag.startOffsetY + (sy - this._drag.startSy);
        this._redraw();
        return;
      }

      const imgPt = this._clampImagePoint(this._screenToImage(sx, sy));

      if (this._drag.mode === "draw") {
        this._drag.curImg = imgPt;
        this._redraw();
      } else if (this._drag.mode === "move") {
        const box = this.boxes[this.selectedIndex];
        const w = box.width * this.imgW;
        const h = box.height * this.imgH;
        let left = imgPt.x - this._drag.grabOffset.x;
        let top = imgPt.y - this._drag.grabOffset.y;
        left = Math.min(Math.max(left, 0), this.imgW - w);
        top = Math.min(Math.max(top, 0), this.imgH - h);
        box.x_center = (left + w / 2) / this.imgW;
        box.y_center = (top + h / 2) / this.imgH;
        this._redraw();
      } else if (this._drag.mode === "resize") {
        this._applyResize(imgPt);
        this._redraw();
      }
    });

    window.addEventListener("mouseup", () => {
      if (!this._drag) return;

      if (this._drag.mode === "draw") {
        const { startImg, curImg } = this._drag;
        const left = Math.min(startImg.x, curImg.x);
        const top = Math.min(startImg.y, curImg.y);
        const w = Math.abs(curImg.x - startImg.x);
        const h = Math.abs(curImg.y - startImg.y);
        if (w >= MIN_BOX_IMAGE_PX && h >= MIN_BOX_IMAGE_PX) {
          const box = {
            class_id: this.lastUsedClass,
            x_center: (left + w / 2) / this.imgW,
            y_center: (top + h / 2) / this.imgH,
            width: w / this.imgW,
            height: h / this.imgH,
          };
          this.boxes.push(box);
          this.selectedIndex = this.boxes.length - 1;
          this.onBoxesChanged();
          this.onSelectionChanged(this.selectedIndex);
        }
      } else if (this._drag.mode === "move" || this._drag.mode === "resize") {
        this.onBoxesChanged();
      }

      this._drag = null;
      this._redraw();
    });
  }

  _applyResize(imgPt) {
    const box = this.boxes[this.selectedIndex];
    const orig = this._drag.box;
    let left = (orig.x_center - orig.width / 2) * this.imgW;
    let top = (orig.y_center - orig.height / 2) * this.imgH;
    let right = left + orig.width * this.imgW;
    let bottom = top + orig.height * this.imgH;

    const handle = this._drag.handle;
    if (handle.includes("n")) top = Math.min(imgPt.y, bottom - MIN_BOX_IMAGE_PX);
    if (handle.includes("s")) bottom = Math.max(imgPt.y, top + MIN_BOX_IMAGE_PX);
    if (handle.includes("w")) left = Math.min(imgPt.x, right - MIN_BOX_IMAGE_PX);
    if (handle.includes("e")) right = Math.max(imgPt.x, left + MIN_BOX_IMAGE_PX);

    left = Math.max(left, 0);
    top = Math.max(top, 0);
    right = Math.min(right, this.imgW);
    bottom = Math.min(bottom, this.imgH);

    box.x_center = (left + right) / 2 / this.imgW;
    box.y_center = (top + bottom) / 2 / this.imgH;
    box.width = (right - left) / this.imgW;
    box.height = (bottom - top) / this.imgH;
  }
}
