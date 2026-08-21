"""Fusiona etiquetas manuales con detecciones del modelo base COCO.

Sin esto, cualquier objeto COCO visible pero no etiquetado (autos, personas)
cuenta como fondo y el fine-tuning le enseña al modelo a NO detectarlo, que es
exactamente como se pierden las clases preentrenadas.

Lee las etiquetas manuales de --labels y escribe el resultado fusionado en
--out, sin tocar el original. El export de la app usa --out por default
(backend/config.py: EXPORT_LABELS_DIR), asi que alcanza con correr esto antes
de exportar cada vez que agregues o edites etiquetas.
"""

import argparse
from pathlib import Path


def iou(a, b):
    """IoU entre dos cajas xyxy en pixeles."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def to_xyxy(cx, cy, w, h, iw, ih):
    return [(cx - w / 2) * iw, (cy - h / 2) * ih, (cx + w / 2) * iw, (cy + h / 2) * ih]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="yolo11s.pt", help="Modelo base que aporta las pseudo-etiquetas")
    p.add_argument("--images", default="workspace/images")
    p.add_argument("--labels", default="workspace/labels", help="Etiquetas manuales (solo lectura)")
    p.add_argument("--out", default="workspace/labels_auto", help="Destino de las etiquetas fusionadas")
    p.add_argument("--classes", default="workspace/classes.txt")
    p.add_argument("--conf", type=float, default=0.25, help="Umbral de confianza para pseudo-etiquetar")
    p.add_argument("--iou", type=float, default=0.5, help="IoU sobre el cual una pseudo-caja se descarta por solaparse con una manual")
    p.add_argument("--device", default=None)
    p.add_argument(
        "--manual-classes",
        default="motorcycle",
        help="Clases donde SOLO se confia en las etiquetas manuales (coma-separadas). "
             "Son las que estas corrigiendo: el modelo base se equivoca en ellas.",
    )
    p.add_argument("--include-unlabeled", action="store_true",
                   help="Incluir imagenes sin etiqueta manual (riesgoso: sus motos sin marcar pasan a ser fondo)")
    args = p.parse_args()

    classes = [l.strip() for l in Path(args.classes).read_text().splitlines() if l.strip()]
    name_to_idx = {n: i for i, n in enumerate(classes)}
    manual_only = {n.strip() for n in args.manual_classes.split(",") if n.strip()}
    unknown = manual_only - set(name_to_idx)
    if unknown:
        raise SystemExit(f"--manual-classes desconocidas en {args.classes}: {sorted(unknown)}")
    manual_idx = {name_to_idx[n] for n in manual_only}

    from ultralytics import YOLO

    model = YOLO(args.model)
    if list(model.names.values()) != classes[: len(model.names)]:
        print("AVISO: los nombres del modelo no coinciden con el prefijo de classes.txt; "
              "los indices pseudo-etiquetados podrian no alinearse.")

    images_dir, labels_dir, out_dir = Path(args.images), Path(args.labels), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    added, kept, skipped_files, dropped_overlap, dropped_manual_cls = {}, 0, [], 0, 0
    written = 0

    for img in sorted(images_dir.iterdir()):
        if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        lbl = labels_dir / f"{img.stem}.txt"
        if not lbl.exists() and not args.include_unlabeled:
            skipped_files.append(img.name)
            continue

        manual = []
        if lbl.exists():
            for line in lbl.read_text().splitlines():
                if line.strip():
                    parts = line.split()
                    manual.append((int(parts[0]), *(float(x) for x in parts[1:5])))
        kept += len(manual)

        res = model.predict(str(img), conf=args.conf, device=args.device, verbose=False)[0]
        ih, iw = res.orig_shape
        manual_xyxy = [to_xyxy(*m[1:], iw, ih) for m in manual]

        merged = [f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}" for c, cx, cy, w, h in manual]
        for cls_t, box in zip(res.boxes.cls, res.boxes.xywhn):
            cls_i = int(cls_t)
            if cls_i in manual_idx:      # esta clase la corrige el humano
                dropped_manual_cls += 1
                continue
            cx, cy, w, h = (float(v) for v in box)
            cand = to_xyxy(cx, cy, w, h, iw, ih)
            if any(iou(cand, m) > args.iou for m in manual_xyxy):
                dropped_overlap += 1
                continue
            merged.append(f"{cls_i} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            added[classes[cls_i]] = added.get(classes[cls_i], 0) + 1

        (out_dir / f"{img.stem}.txt").write_text("\n".join(merged) + "\n")
        written += 1

    print(f"\nEscritos {written} archivos en {out_dir}/")
    print(f"  cajas manuales preservadas : {kept}")
    print(f"  pseudo-cajas agregadas     : {sum(added.values())}")
    for n, c in sorted(added.items(), key=lambda kv: -kv[1]):
        print(f"      {n:16s} {c}")
    print(f"  descartadas (clase manual) : {dropped_manual_cls}")
    print(f"  descartadas (solape > {args.iou}) : {dropped_overlap}")
    if skipped_files:
        print(f"\n  {len(skipped_files)} imagenes SIN etiqueta manual, omitidas:")
        for n in skipped_files:
            print(f"      {n}")
        print("  Etiquetalas en la app (o usa --include-unlabeled bajo tu responsabilidad).")
    print("\nYa podes exportar desde la app: usa este directorio por default.")


if __name__ == "__main__":
    main()
