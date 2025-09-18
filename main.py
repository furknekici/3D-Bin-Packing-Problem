import re
import copy
import random
import time
import json
from multiprocessing import Pool
import plotly.graph_objects as go

def load_instances(path):
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        container_line = next(l for l in lines if "Bin dimensions" in l)
        dims = re.findall(r'\d+', container_line)
        container = {"L": int(dims[0]), "W": int(dims[1]), "H": int(dims[2])}
        boxes = []
        for line in lines:
            if line.startswith("#") or line.startswith("-") or line.lower().startswith("id"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                q = int(parts[1])
                l, w, h = int(parts[2]), int(parts[3]), int(parts[4])
                for _ in range(q):
                    boxes.append({"id": len(boxes), "L": l, "W": w, "H": h})
        return container, boxes
# ------------------------------
# JSON instance yükleme
# ------------------------------
def load_all_instances(path, container_dims=(1200, 1200, 1500)):
    """
    JSON dosyasından tüm order'ları yükler.
    container_dims: (L, W, H) sabit konteyner boyutları
    """
    with open(path, "r") as f:
        data = json.load(f)

    instances = {}
    for order_id, order_content in data.items():
        boxes = []
        for _, item in order_content["item_sequence"].items():
            l = int(item["length/mm"])
            w = int(item["width/mm"])
            h = int(item["height/mm"])
            boxes.append({
                "id": len(boxes),
                "L": l,
                "W": w,
                "H": h
            })

        container = {"L": container_dims[0], "W": container_dims[1], "H": container_dims[2]}
        instances[order_id] = (container, boxes)

    return instances

# ------------------------------
# Çakışma kontrolü
# ------------------------------
def check_collision(b, placed):
    for other in placed:
        if (b["x"] < other["x"] + other["L"] and b["x"] + b["L"] > other["x"] and
            b["y"] < other["y"] + other["W"] and b["y"] + b["W"] > other["y"] and
            b["z"] < other["z"] + other["H"] and b["z"] + b["H"] > other["z"]):
            return True
    return False

# ------------------------------
# Destek alanı kontrolü
# ------------------------------
def get_supported_z(b, placed):
    max_z = 0
    for other in placed:
        x_overlap = min(b["x"]+b["L"], other["x"]+other["L"]) - max(b["x"], other["x"])
        y_overlap = min(b["y"]+b["W"], other["y"]+other["W"]) - max(b["y"], other["y"])
        if x_overlap > 0 and y_overlap > 0:
            support_area = x_overlap * y_overlap
            box_area = b["L"] * b["W"]
            if support_area / box_area >= 0.8:
                max_z = max(max_z, other["z"] + other["H"])
    return max_z

# ------------------------------
# Floating kutu kontrolü
# ------------------------------
def check_floating_boxes(placed):
    floating = []
    for b in placed:
        if b["z"] == 0:
            continue
        supported = False
        for other in placed:
            if other == b:
                continue
            x_overlap = min(b["x"]+b["L"], other["x"]+other["L"]) - max(b["x"], other["x"])
            y_overlap = min(b["y"]+b["W"], other["y"]+other["W"]) - max(b["y"], other["y"])
            if x_overlap > 0 and y_overlap > 0:
                support_area = x_overlap * y_overlap
                if support_area / (b["L"]*b["W"]) >= 0.8:
                    if abs(b["z"] - (other["z"] + other["H"])) < 1e-3:
                        supported = True
                        break
        if not supported:
            floating.append(b)
    return floating

# ------------------------------
# Tüm rotasyonları deneyen yerleştirme
# ------------------------------
def get_rotations(b):
    L,W,H = b["L"], b["W"], b["H"]
    return [
        (L,W,H), (L,H,W), (W,L,H), (W,H,L), (H,L,W), (H,W,L)
    ]

def place_boxes_sequence(container, boxes_seq):
    placed = []
    extreme_points = [{"x":0,"y":0,"z":0}]
    unplaced = []

    for b in boxes_seq:
        placed_flag = False
        for l,w,h in get_rotations(b):
            for p in extreme_points:
                if p["x"] + l <= container["L"] and p["y"] + w <= container["W"]:
                    b["x"], b["y"], b["L"], b["W"], b["H"] = p["x"], p["y"], l, w, h
                    b["z"] = get_supported_z(b, placed)
                    if b["z"] + b["H"] <= container["H"] and not check_collision(b, placed):
                        b_copy = copy.deepcopy(b)
                        b_copy["placed"] = True
                        placed.append(b_copy)
                        extreme_points.append({"x": p["x"]+l, "y": p["y"], "z": b_copy["z"]})
                        extreme_points.append({"x": p["x"], "y": p["y"]+w, "z": b_copy["z"]})
                        extreme_points.append({"x": p["x"], "y": p["y"], "z": b_copy["z"]+b_copy["H"]})
                        placed_flag = True
                        break
            if placed_flag:
                break
        if not placed_flag:
            unplaced.append(copy.deepcopy(b))

    used_volume = sum([b["L"]*b["W"]*b["H"] for b in placed])
    total_volume = container["L"]*container["W"]*container["H"]
    return placed, used_volume / total_volume, unplaced

# ------------------------------
# Global trial fonksiyonu
# ------------------------------
def trial(i, container, boxes):
    return place_boxes_sequence(container, random.sample(boxes, len(boxes)))

# ------------------------------
# 30 saniye limitli paralel deneme
# ------------------------------
def parallel_trials_time_limited(container, boxes, max_trials=1000, time_limit=30, batch_size=10):
    total_box_volume = sum(b["L"]*b["W"]*b["H"] for b in boxes)
    container_volume = container["L"]*container["W"]*container["H"]
    require_full = total_box_volume <= container_volume  # tüm kutular sığabilir mi?

    best = None
    trials_done = 0
    start = time.time()

    with Pool() as pool:
        while trials_done < max_trials:
            remaining = min(batch_size, max_trials - trials_done)
            args = [(i, container, boxes) for i in range(remaining)]
            results = pool.starmap(trial, args)

            for res in results:
                placed, fitness, unplaced = res
                if not best or len(unplaced) < len(best[2]):
                    best = res

            trials_done += remaining

            if require_full and len(best[2]) == 0:
                print(f"✅ Tüm kutular {trials_done}. denemede yerleştirildi!")
                break

            if time.time() - start > time_limit:
                print(f"⏱ Süre limiti ({time_limit} sn) aşıldı, en iyi sonuç döndürülüyor...")
                break

    end = time.time()
    print(f"Toplam süre: {end-start:.2f} saniye, yapılan deneme: {trials_done}")
    return best

# ------------------------------
# Plotly 3D Görselleştirme
# ------------------------------
def plot_boxes(container, boxes):
    fig = go.Figure()

    for b in boxes:
        x, y, z = b["x"], b["y"], b["z"]
        dx, dy, dz = b["L"], b["W"], b["H"]

        # Renkli kutu (daha canlı ve az şeffaf)
        fig.add_trace(go.Mesh3d(
            x=[x, x+dx, x+dx, x, x, x+dx, x+dx, x],
            y=[y, y, y+dy, y+dy, y, y, y+dy, y+dy],
            z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
            i=[0, 0, 0, 4, 4, 4, 2, 1, 5, 6, 7, 6],
            j=[1, 2, 3, 5, 6, 7, 6, 5, 4, 7, 6, 2],
            k=[2, 3, 0, 6, 7, 4, 1, 0, 1, 3, 2, 1],
            color=f"rgb({(b['id']*50)%255}, {(b['id']*80)%255}, {(b['id']*120)%255})",
            opacity=0.7,
            name=f"Kutu {b['id']}",
            hovertext=f"ID: {b['id']}<br>LWH: {b['L']}x{b['W']}x{b['H']}<br>Koordinat: ({x},{y},{z})",
            hoverinfo="text"
        ))

        # Daha net kenarlar için çizgileri Mesh3d ile değil, Scatter3d ile
        edges = [
            # Alt taban
            ([x, x+dx], [y, y], [z, z]),
            ([x+dx, x+dx], [y, y+dy], [z, z]),
            ([x+dx, x], [y+dy, y+dy], [z, z]),
            ([x, x], [y+dy, y], [z, z]),
            # Üst taban
            ([x, x+dx], [y, y], [z+dz, z+dz]),
            ([x+dx, x+dx], [y, y+dy], [z+dz, z+dz]),
            ([x+dx, x], [y+dy, y+dy], [z+dz, z+dz]),
            ([x, x], [y+dy, y], [z+dz, z+dz]),
            # Dikey kenarlar
            ([x, x], [y, y], [z, z+dz]),
            ([x+dx, x+dx], [y, y], [z, z+dz]),
            ([x+dx, x+dx], [y+dy, y+dy], [z, z+dz]),
            ([x, x], [y+dy, y+dy], [z, z+dz])
        ]
        for ex, ey, ez in edges:
            fig.add_trace(go.Scatter3d(
                x=ex, y=ey, z=ez,
                mode='lines',
                line=dict(color='black', width=4),
                showlegend=False
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X', nticks=10, range=[0, container["L"]], backgroundcolor="rgb(230, 230,230)"),
            yaxis=dict(title='Y', nticks=10, range=[0, container["W"]], backgroundcolor="rgb(230, 230,230)"),
            zaxis=dict(title='Z', nticks=10, range=[0, container["H"]], backgroundcolor="rgb(230, 230,230)"),
            aspectmode='data'
        ),
        width=1000,
        height=800,
        margin=dict(r=20, l=10, b=10, t=10),
        showlegend=True
    )
    fig.show()





# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    choice = input("Veriyi dosyadan mı yoksa elle mi gireceksiniz? (dosya/elle): ").strip().lower()

    if choice == "dosya":
        file_type = input("Dosya tipi nedir? (txt/json): ").strip().lower()
        path = input("Dosya yolu: ").strip()
        if file_type == "txt":
            container, boxes = load_instances(path)
        elif file_type == "json":
            instances = load_all_instances(path)
            # JSON'da birden fazla order olabilir, ilkini alıyoruz
            order_id, (container, boxes) = next(iter(instances.items()))
        else:
            print("Geçersiz dosya tipi.")
            exit()
    elif choice == "elle":
        # Konteyner girişi
        L = int(input("Konteyner uzunluğu (L): "))
        W = int(input("Konteyner genişliği (W): "))
        H = int(input("Konteyner yüksekliği (H): "))
        container = {"L": L, "W": W, "H": H}

        boxes = []
        print("\nKutu bilgilerini giriniz. Format: L W H Q (bitirmek için 0 0 0 0 yazın)")
        while True:
            line = input("Kutu: ").strip()
            parts = line.split()
            if len(parts) != 4:
                print("❌ Hatalı giriş, format: L W H Q")
                continue
            l, w, h, q = map(int, parts)
            if l == 0 and w == 0 and h == 0 and q == 0:
                break
            for _ in range(q):
                boxes.append({"id": len(boxes), "L": l, "W": w, "H": h})
    else:
        print("Geçersiz seçim.")
        exit()

    # Yerleştirme
    placed_boxes, fill_ratio, unplaced_boxes = parallel_trials_time_limited(
        container, boxes, max_trials=1000, time_limit=30, batch_size=10
    )
    floating_boxes = check_floating_boxes(placed_boxes)

    # Sonuçları yazdır
    print("\n🔹 Sonuçlar:")
    print("Doldurma oranı:", fill_ratio)
    print("Yerleşen kutu sayısı:", len(placed_boxes))
    print("Yerleştirilmeyen kutu sayısı:", len(unplaced_boxes))
    print("Yerleştirilmeyen kutuların ID'leri:", [b['id'] for b in unplaced_boxes])
    print("Havada duran kutu sayısı:", len(floating_boxes))
    print("Havada duran kutuların ID'leri:", [b['id'] for b in floating_boxes])

    # Görselleştirme
    plot_boxes(container, placed_boxes)


