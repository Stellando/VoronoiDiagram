import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from datastructer import* 
import copy
import math

# 畫布和計算範圍常數
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600
# 修改：大幅擴大計算邊界，確保遠處的交點能被計算到
CALC_MARGIN = 20000  # 計算範圍延伸
CALC_MIN = -CALC_MARGIN
CALC_MAX_X = CANVAS_WIDTH + CALC_MARGIN
CALC_MAX_Y = CANVAS_HEIGHT + CALC_MARGIN


# 幾何計算函數
def calculate_circumcenter(p1, p2, p3):
    """
    計算三角形外心
    返回 (cx, cy) 或 None（如果三點共線）
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    
    # 計算 D = 2(x1(y2-y3) + x2(y3-y1) + x3(y1-y2))
    D = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    
    # 如果 D 接近 0，表示三點共線
    if abs(D) < 1e-9:
        return None
    
    # 計算外心座標
    ux = ((x1*x1 + y1*y1) * (y2 - y3) + 
          (x2*x2 + y2*y2) * (y3 - y1) + 
          (x3*x3 + y3*y3) * (y1 - y2)) / D
    
    uy = ((x1*x1 + y1*y1) * (x3 - x2) + 
          (x2*x2 + y2*y2) * (x1 - x3) + 
          (x3*x3 + y3*y3) * (x2 - x1)) / D
    
    return (ux, uy)


def are_collinear(p1, p2, p3, tolerance=1e-6):
    """判斷三點是否共線"""
    # 使用叉積判斷
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    
    # 計算向量 (p1->p2) 和 (p1->p3) 的叉積
    cross = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    
    return abs(cross) < tolerance


def is_obtuse_triangle(p1, p2, p3):
    """
    判斷三角形是否為鈍角三角形
    返回 True 如果是鈍角三角形
    """
    # 計算三邊長度的平方
    def dist_squared(a, b):
        return (a.x - b.x)**2 + (a.y - b.y)**2
    
    a2 = dist_squared(p2, p3)  # BC^2
    b2 = dist_squared(p1, p3)  # AC^2
    c2 = dist_squared(p1, p2)  # AB^2
    
    # 檢查任一角是否為鈍角
    # 角A為鈍角: a^2 > b^2 + c^2
    if a2 > b2 + c2 + 1e-9:
        return True
    # 角B為鈍角: b^2 > a^2 + c^2
    if b2 > a2 + c2 + 1e-9:
        return True
    # 角C為鈍角: c^2 > a^2 + b^2
    if c2 > a2 + b2 + 1e-9:
        return True
    
    return False


def find_obtuse_vertex(p1, p2, p3):
    """
    找出鈍角三角形的鈍角頂點和對邊
    返回: (obtuse_vertex, opposite_edge_p1, opposite_edge_p2) 或 None
    
    例如：如果 A 是鈍角，返回 (A, B, C) - BC 是對邊
    """
    def dist_squared(a, b):
        return (a.x - b.x)**2 + (a.y - b.y)**2
    
    a2 = dist_squared(p2, p3)  # BC^2 (A的對邊)
    b2 = dist_squared(p1, p3)  # AC^2 (B的對邊)
    c2 = dist_squared(p1, p2)  # AB^2 (C的對邊)
    
    # 角A為鈍角: a^2 > b^2 + c^2
    if a2 > b2 + c2 + 1e-9:
        return (p1, p2, p3)  # A是鈍角，BC是對邊
    
    # 角B為鈍角: b^2 > a^2 + c^2
    if b2 > a2 + c2 + 1e-9:
        return (p2, p1, p3)  # B是鈍角，AC是對邊
    
    # 角C為鈍角: c^2 > a^2 + b^2
    if c2 > a2 + b2 + 1e-9:
        return (p3, p1, p2)  # C是鈍角，AB是對邊
    
    return None


def is_right_triangle(p1, p2, p3):
    """
    判斷三角形是否為直角三角形
    返回 True 如果是直角三角形（任一角為 90 度）
    """
    def dist_squared(a, b):
        return (a.x - b.x)**2 + (a.y - b.y)**2
    
    a2 = dist_squared(p2, p3)  # BC^2
    b2 = dist_squared(p1, p3)  # AC^2
    c2 = dist_squared(p1, p2)  # AB^2
    
    # 使用畢氏定理檢查：a² = b² + c²（容差 1e-6）
    epsilon = 1e-6
    
    # 檢查角A是否為直角: a² = b² + c²
    if abs(a2 - (b2 + c2)) < epsilon:
        return True
    # 檢查角B是否為直角: b² = a² + c²
    if abs(b2 - (a2 + c2)) < epsilon:
        return True
    # 檢查角C是否為直角: c² = a² + b²
    if abs(c2 - (a2 + b2)) < epsilon:
        return True
    
    return False


def find_right_vertex(p1, p2, p3):
    """
    找出直角三角形的直角頂點和對邊
    返回: (right_vertex, opposite_edge_p1, opposite_edge_p2) 或 None
    
    例如：如果 A 是直角，返回 (A, B, C) - BC 是對邊
    """
    def dist_squared(a, b):
        return (a.x - b.x)**2 + (a.y - b.y)**2
    
    a2 = dist_squared(p2, p3)  # BC^2 (A的對邊)
    b2 = dist_squared(p1, p3)  # AC^2 (B的對邊)
    c2 = dist_squared(p1, p2)  # AB^2 (C的對邊)
    
    epsilon = 1e-6
    
    # 角A為直角: a² = b² + c²
    if abs(a2 - (b2 + c2)) < epsilon:
        return (p1, p2, p3)  # A是直角，BC是對邊
    
    # 角B為直角: b² = a² + c²
    if abs(b2 - (a2 + c2)) < epsilon:
        return (p2, p1, p3)  # B是直角，AC是對邊
    
    # 角C為直角: c² = a² + b²
    if abs(c2 - (a2 + b2)) < epsilon:
        return (p3, p1, p2)  # C是直角，AB是對邊
    
    return None


def find_farthest_two_points(p1, p2, p3):
    """
    找出三點中距離最遠的兩個點
    返回: (point1, point2, point3) 其中 point1 和 point2 距離最遠
    """
    def dist_squared(a, b):
        return (a.x - b.x)**2 + (a.y - b.y)**2
    
    d12 = dist_squared(p1, p2)
    d23 = dist_squared(p2, p3)
    d13 = dist_squared(p1, p3)
    
    if d12 >= d23 and d12 >= d13:
        return (p1, p2, p3)
    elif d23 >= d12 and d23 >= d13:
        return (p2, p3, p1)
    else:
        return (p1, p3, p2)


def compute_convex_hull(points):
    """
    計算點集的凸包（Andrew's Monotone Chain 演算法）
    
    參數:
        points: List[Point] 或 List[VoronoiSite] - 點的列表
    
    返回:
        ConvexHull - 包含凸包頂點（逆時針順序）和邊
    """
    if not points:
        return ConvexHull(points=[], edges=[])
    
    if len(points) == 1:
        return ConvexHull(points=list(points), edges=[])
    
    if len(points) == 2:
        p1, p2 = points[0], points[1]
        return ConvexHull(points=list(points), edges=[(p1, p2)])
    
    # 將點按照 (x, y) 排序
    sorted_points = sorted(points, key=lambda p: (p.x, p.y))
    
    def cross_product(o, a, b):
        """計算叉積 (a-o) × (b-o)"""
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
    
    # 構建下凸包
    lower = []
    for p in sorted_points:
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    # 構建上凸包
    upper = []
    for p in reversed(sorted_points):
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    # 移除重複的首尾點
    hull_points = lower[:-1] + upper[:-1]
    
    # 如果只有兩個點，特殊處理
    if len(hull_points) < 3:
        hull_points = sorted_points
    
    # 構建邊
    edges = []
    for i in range(len(hull_points)):
        p1 = hull_points[i]
        p2 = hull_points[(i + 1) % len(hull_points)]
        edges.append((p1, p2))
    
    return ConvexHull(points=hull_points, edges=edges)


def compute_hyperplane_points(left_sites, right_sites, merged_hull, left_hull, right_hull):
    """
    計算 hyperplane 的兩個端點（上切線 Upper Tangent）
    
    修正版：使用更穩健的 Walking Algorithm
    1. 修正起始點選擇邏輯
    2. 修正幾何方向判斷（螢幕座標系 Y 軸向下）
    """
    if not left_hull or not left_hull.points:
        return None
    if not right_hull or not right_hull.points:
        return None
        
    l_points = left_hull.points
    r_points = right_hull.points
    n_l = len(l_points)
    n_r = len(r_points)
    
    # =========================================================================
    # 1. 尋找最佳起始點
    # 原本只找最右/最左，現在加入 Y 軸考量，避免起點落在凸包底部導致搜尋路徑被卡住
    # 左凸包：找 X 最大者；若 X 相同，找 Y 最小者（最右上）
    l_idx = max(range(n_l), key=lambda i: (l_points[i].x, -l_points[i].y))
    # 右凸包：找 X 最小者；若 X 相同，找 Y 最小者（最左上）
    r_idx = min(range(n_r), key=lambda i: (r_points[i].x, r_points[i].y))
    # =========================================================================

    def is_upper_tangent_violated(p_curr, p_other, p_candidate):
        """
        判斷 p_candidate 是否比當前切線 (p_curr -> p_other) '更高'
        在螢幕座標系(Y向下)中:
        向量 V = p_other - p_curr
        如果 p_candidate 在 V 的 '左側' (逆時針)，則代表它更靠上方
        """
        # 叉積計算: (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x)
        # 此處 a=p_curr, b=p_other, c=p_candidate
        val = (p_other.x - p_curr.x) * (p_candidate.y - p_curr.y) - \
              (p_other.y - p_curr.y) * (p_candidate.x - p_curr.x)
        
        # 在螢幕座標系中，如果 val < 0，表示 p_candidate 在 p_curr->p_other 的 '左側' (上方)
        # 我們使用一個微小的容差值來處理共線情況
        return val < -1e-7

    # 2. Walking Algorithm 尋找上切線
    done = False
    while not done:
        done = True
        
        # 左凸包：嘗試逆時針移動 (Index + 1)
        # 我們希望切線是該凸包的"最高"邊界，所以如果下一個點在當前連線的"上方"，就移動過去
        while True:
            l_next = (l_idx + 1) % n_l
            if is_upper_tangent_violated(l_points[l_idx], r_points[r_idx], l_points[l_next]):
                l_idx = l_next
                done = False
            else:
                break
                
        # 右凸包：嘗試順時針移動 (Index - 1)
        # 我們希望切線是該凸包的"最高"邊界，如果前一個點在當前連線的"上方"，就移動過去
        while True:
            r_prev = (r_idx - 1 + n_r) % n_r
            # 注意這裡向量方向是 左->右，判斷邏輯一致
            if is_upper_tangent_violated(l_points[l_idx], r_points[r_idx], r_points[r_prev]):
                r_idx = r_prev
                done = False
            else:
                break

    left_point = l_points[l_idx]
    right_point = r_points[r_idx]
    
    print(f"    [Hyperplane Start] 鎖定上切線: 左 ({left_point.x:.1f}, {left_point.y:.1f}) -> 右 ({right_point.x:.1f}, {right_point.y:.1f})")
    
    return (left_point, right_point)


def line_intersection(p1, p2, p3, p4):
    """
    計算兩條線段的交點
    線段1: p1 到 p2
    線段2: p3 到 p4
    
    返回: (x, y, t1, t2) 或 None
    其中 t1 是交點在線段1上的參數 (0-1 表示在線段內)
         t2 是交點在線段2上的參數 (0-1 表示在線段內)
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y
    
    # 計算方向向量
    dx1 = x2 - x1
    dy1 = y2 - y1
    dx2 = x4 - x3
    dy2 = y4 - y3
    
    # 計算行列式
    det = dx1 * dy2 - dy1 * dx2
    
    # 平行或重合
    if abs(det) < 1e-9:
        return None
    
    # 計算參數 t1 和 t2
    t1 = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / det
    t2 = ((x3 - x1) * dy1 - (y3 - y1) * dx1) / det
    
    # 計算交點
    x = x1 + t1 * dx1
    y = y1 + t1 * dy1
    
    return (x, y, t1, t2)


# ==========================================
# 輔助函數：判斷點在直線的哪一側
# ==========================================
def get_point_side(p, line_start, line_end):
    """
    計算點 p 相對於有向線段 (line_start -> line_end) 的位置
    使用叉積原理 (Cross Product)
    返回:
        正值: 點在線段左側
        負值: 點在線段右側
        0: 點在線上
    注意：螢幕座標系 Y 軸向下，方向性可能與笛卡爾座標相反，
    但只要相對比較符號相同即可。
    """
    return (line_end.x - line_start.x) * (p.y - line_start.y) - \
           (line_end.y - line_start.y) * (p.x - line_start.x)


def truncate_hyperplane(hyperplane_start, hyperplane_end, all_edges, left_sites, right_sites, active_sites=None, depth=0):
    """
    截斷 hyperplane：找到由上往下第一個交點，並截斷所有在該點重疊的中垂線
    修正：傳入 active_sites (產生當前 hyperplane 的站點對)，確保使用正確的參考站點來判斷保留方向
    """
    # 確保 start 的 Y 小於 end 的 Y（由上往下繪製）
    if hyperplane_start.y > hyperplane_end.y:
        hyperplane_start, hyperplane_end = hyperplane_end, hyperplane_start
        print(f"{'  '*depth}    [截斷] 對調起始點和結束點")
    
    print(f"{'  '*depth}    [截斷] Hyperplane: ({hyperplane_start.x:.1f}, {hyperplane_start.y:.1f}) -> ({hyperplane_end.x:.1f}, {hyperplane_end.y:.1f})")
    
    # 修正：提高精度，1.0 像素誤差太大，容易導致拓樸錯誤
    INTERSECTION_TOLERANCE = 1e-5
    
    closest_intersection = None
    closest_t = float('inf')
    all_intersections = []  # 存儲所有交點資訊：(x, y, t1, t2, edge)
    
    # 遍歷所有邊，找到所有交點
    for edge in all_edges:
        if not edge.start or not edge.end:
            continue
        
        # 計算交點
        result = line_intersection(hyperplane_start, hyperplane_end, edge.start, edge.end)
        
        if result:
            x, y, t1, t2 = result
            
            # t1 是 hyperplane 上的參數，t2 是邊上的參數
            # 嚴格檢查 t1 > epsilon 避免在起始點重複碰撞
            if 1e-9 < t1 < 1 and 0 <= t2 <= 1:
                all_intersections.append((x, y, t1, t2, edge))
                # print(f"{'  '*depth}      找到交點: ({x:.1f}, {y:.1f}), t1={t1:.3f}")
                
                # 記錄最近的交點
                if t1 < closest_t:
                    closest_t = t1
                    closest_intersection = (x, y)
    
    if closest_intersection:
        x, y = closest_intersection
        
        # 找出所有在容差範圍內的重疊交點（處理多邊共點情況）
        overlapping_intersections = []
        for ix, iy, t1, t2, edge in all_intersections:
            distance = math.sqrt((ix - x)**2 + (iy - y)**2)
            # 使用稍大的容差來合併非常接近的交點
            if distance <= 1e-4: 
                overlapping_intersections.append((ix, iy, t1, t2, edge))
        
        print(f"{'  '*depth}    [截斷] 最近交點: ({x:.1f}, {y:.1f})")
        
        # 收集所有涉及的站點
        all_sites = set()
        intersected_edges = []
        
        for ix, iy, t1, t2, edge in overlapping_intersections:
            site1 = edge.site1
            site2 = edge.site2
            all_sites.add(site1)
            all_sites.add(site2)
            intersected_edges.append(edge)
        
        # 創建新的交點頂點
        from datastructer import VoronoiVertex, Point
        intersection_vertex = VoronoiVertex(x, y, sites=list(all_sites))
        intersection_vertex.is_junction = True
        
        # -----------------------------------------------------
        # 核心修正邏輯：決定保留邊的哪一端
        # -----------------------------------------------------
        for edge in intersected_edges:
            # 關鍵修正：優先從 active_sites 中選取參考站點
            ref_site = edge.site1  # 預設值
            
            if active_sites:
                # 檢查這條邊是否連接著產生當前 Hyperplane 的站點
                if edge.site1 in active_sites:
                    ref_site = edge.site1
                elif edge.site2 in active_sites:
                    ref_site = edge.site2
                else:
                    # 這條邊不連接 active sites，可能是數值誤差選到了鄰近的邊
                    # 這種情況下，保留預設行為，但印出警告
                    print(f"{'  '*depth}    [警告] 被截斷的邊不屬於當前 Hyperplane 產生點")
            
            # 計算參考站點在 Hyperplane 的哪一側
            #    Hyperplane 方向向量為 hyperplane_start -> hyperplane_end
            site_side = get_point_side(ref_site, hyperplane_start, hyperplane_end)
            
            # 3. 計算邊的兩個端點在 Hyperplane 的哪一側
            start_side = get_point_side(edge.start, hyperplane_start, hyperplane_end)
            end_side = get_point_side(edge.end, hyperplane_start, hyperplane_end)
            
            # 4. 判斷邏輯：
            #    我們要保留 "與參考站點在同一側" 的那個端點
            #    如果端點與參考站點同號 (相乘 > 0)，則保留該端點
            
            # 判斷 Start 點是否與 Site 同側
            keep_start = (start_side * site_side) >= 0
            
            # 判斷 End 點是否與 Site 同側
            keep_end = (end_side * site_side) >= 0
            
            # 執行截斷與替換
            modified = False
            if keep_start and not keep_end:
                # 保留 Start，修改 End 為交點
                print(f"{'  '*depth}    [截斷] 修改 End 為交點")
                edge.end = intersection_vertex
                modified = True
            elif keep_end and not keep_start:
                # 保留 End，修改 Start 為交點
                print(f"{'  '*depth}    [截斷] 修改 Start 為交點")
                edge.start = intersection_vertex
                modified = True
            elif not keep_start and not keep_end:
                # 兩端都在異側（理論上不應發生，除非線段完全穿過且很短），
                # 或是數值誤差。這裡保守處理，找較遠的點替換，或者報錯。
                # 這裡假設保留幾何上較合理的一端(距離交點較遠的?)
                # 暫時強制修改 End
                edge.end = intersection_vertex
                print(f"{'  '*depth}    [截斷警告] 兩端點皆異側，強制修改 End")
            else:
                # 兩端都在同側：表示這條線根本不該被切（可能是數值誤差導致誤判交點）
                # 或者交點就在端點上。
                # 計算距離，將較近的端點吸附到交點
                d_start = (edge.start.x - x)**2 + (edge.start.y - y)**2
                d_end = (edge.end.x - x)**2 + (edge.end.y - y)**2
                if d_start < d_end:
                     edge.start = intersection_vertex
                else:
                     edge.end = intersection_vertex
                print(f"{'  '*depth}    [截斷微調] 吸附端點到交點")

        intersection_point = Point(x, y)
        return (intersection_point, intersected_edges, list(all_sites))
    else:
        return (None, None, None)


def continue_hyperplane_from_intersection(vd, initial_start, initial_generating_sites, left_sites, right_sites, depth=0):
    """
    從初始 hyperplane 的碰撞點開始，繼續繪製 hyperplane 直到離開畫布
    
    參數:
        vd: VoronoiDiagram 實例
        initial_start: 初始 hyperplane 的碰撞點，作為下一段的起始點 (Point)
        initial_generating_sites: 產生下一段 hyperplane 的兩個站點 (tuple of two sites)
        left_sites: 左半邊的站點列表
        right_sites: 右半邊的站點列表
        depth: 遞迴深度（用於輸出）
    
    返回:
        所有創建的 hyperplane 邊的列表
    """
    from datastructer import Point, VoronoiVertex
    
    # 最大迭代次數保護（可在此處修改以調整迭代上限）
    MAX_ITERATIONS = 100
    
    print(f"{'  '*depth}  [繼續 Hyperplane] 開始從碰撞點延伸 hyperplane")
    
    all_hyperplane_edges = []
    current_start = initial_start
    
    # 記錄當前 hyperplane 是由哪兩個站點產生的
    current_generating_sites = initial_generating_sites
    
    # 首先計算初始的延伸方向
    site_a, site_c = current_generating_sites
    
    # 計算中點
    mid_x = (site_a.x + site_c.x) / 2.0
    mid_y = (site_a.y + site_c.y) / 2.0
    
    # 計算中垂線的方向向量（垂直於 A-C 連線）
    dx = site_c.x - site_a.x
    dy = site_c.y - site_a.y
    
    # 垂直方向（旋轉90度）
    direction_x = -dy
    direction_y = dx
    
    # 正規化方向向量
    length = math.sqrt(direction_x**2 + direction_y**2)
    if length > 1e-9:
        direction_x /= length
        direction_y /= length
    
    # 確保方向向量指向下方（direction_y > 0）
    if direction_y < 0:
        direction_x = -direction_x
        direction_y = -direction_y
    
    print(f"{'  '*depth}  [繼續 Hyperplane] 初始產生點: ({site_a.x:.1f}, {site_a.y:.1f}) 和 ({site_c.x:.1f}, {site_c.y:.1f})")
    print(f"{'  '*depth}  [繼續 Hyperplane] 中垂線方向: ({direction_x:.3f}, {direction_y:.3f})")
    
    # 修改:大幅增加延伸長度,確保能延伸出計算邊界 (配合 CALC_MARGIN)
    extension_length = 40000  # 原本是 2000
    current_end_x = current_start.x + direction_x * extension_length
    current_end_y = current_start.y + direction_y * extension_length
    current_end = Point(current_end_x, current_end_y)
    
    iteration = 0
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"{'  '*depth}  [繼續 Hyperplane] 迭代 {iteration}/{MAX_ITERATIONS}")
        
        # 收集當前合併層級的邊（只包含左半邊和右半邊的邊，包括 hyperplane）
        current_level_edges = []
        for e in vd.edges:
            # 檢查是否屬於左半邊
            if e.site1 in left_sites and e.site2 in left_sites:
                current_level_edges.append(e)
            # 檢查是否屬於右半邊
            elif e.site1 in right_sites and e.site2 in right_sites:
                current_level_edges.append(e)
            # 檢查是否為跨越左右的 hyperplane（之前更深層或本層產生的）
            elif e.is_hyperplane and ((e.site1 in left_sites and e.site2 in right_sites) or 
                                       (e.site1 in right_sites and e.site2 in left_sites)):
                current_level_edges.append(e)
        
        print(f"{'  '*depth}  [繼續 Hyperplane] 當前層級共有 {len(current_level_edges)} 條邊")
        
        # 執行截斷，找到下一個碰撞點
        # 修正：傳入 active_sites=current_generating_sites
        new_end, intersected_edges, all_intersected_sites = truncate_hyperplane(
            current_start, current_end, current_level_edges, left_sites, right_sites, 
            active_sites=current_generating_sites, depth=depth + 1
        )
        
        # 檢查是否找到碰撞點
        if not new_end:
            print(f"{'  '*depth}  [繼續 Hyperplane] 未找到碰撞點，繪製最後一段延伸到邊界")
            # 沒有碰撞點，使用原本計算的終點（延伸到邊界）
            new_end = current_end
            is_final_segment = True
        elif new_end.y > CANVAS_HEIGHT:
            print(f"{'  '*depth}  [繼續 Hyperplane] 碰撞點 Y={new_end.y:.1f} > {CANVAS_HEIGHT}，離開畫布，繪製最後一段")
            # 碰撞點在畫布外，仍然繪製這一段
            is_final_segment = True
        else:
            # 碰撞點在畫布內
            print(f"{'  '*depth}  [繼續 Hyperplane] 碰撞點在畫布內: ({new_end.x:.1f}, {new_end.y:.1f})")
            is_final_segment = False
        
        # 創建這一段的端點頂點
        start_vertex = vd.create_vertex(current_start.x, current_start.y, sites=list(current_generating_sites))
        end_vertex = vd.create_vertex(new_end.x, new_end.y, sites=list(current_generating_sites))
        
        # 創建 hyperplane 邊
        site_a, site_c = current_generating_sites
        edge = vd.create_edge(site_a, site_c)
        edge.start = start_vertex
        edge.end = end_vertex
        edge.is_hyperplane = True
        
        all_hyperplane_edges.append(edge)
        print(f"{'  '*depth}  [繼續 Hyperplane] 創建 hyperplane 段: ({current_start.x:.1f}, {current_start.y:.1f}) -> ({new_end.x:.1f}, {new_end.y:.1f})")
        
        # 如果是最後一段，停止延伸
        if is_final_segment:
            print(f"{'  '*depth}  [繼續 Hyperplane] 已繪製最後一段，停止延伸")
            break
        
        # 獲取所有被碰撞邊涉及的站點
        if not all_intersected_sites:
            print(f"{'  '*depth}  [繼續 Hyperplane] 錯誤：未能獲取被碰撞邊的站點，停止延伸")
            break
        
        print(f"{'  '*depth}  [繼續 Hyperplane] 碰撞涉及 {len(all_intersected_sites)} 個站點")
        for site in all_intersected_sites:
            print(f"{'  '*depth}    站點: ({site.x:.1f}, {site.y:.1f})")
        
        # 確定下一段 hyperplane 的產生點
        # 規則：從所有涉及的站點中，排除當前 hyperplane 的產生點
        prev_site1, prev_site2 = current_generating_sites
        
        # 找出不是當前產生點的站點
        remaining_sites = [s for s in all_intersected_sites if s != prev_site1 and s != prev_site2]
        
        print(f"{'  '*depth}  [繼續 Hyperplane] 當前產生點: ({prev_site1.x:.1f},{prev_site1.y:.1f}) 和 ({prev_site2.x:.1f},{prev_site2.y:.1f})")
        print(f"{'  '*depth}  [繼續 Hyperplane] 排除後剩餘 {len(remaining_sites)} 個站點")
        
        if len(remaining_sites) == 0:
            print(f"{'  '*depth}  [繼續 Hyperplane] 錯誤：沒有剩餘站點可以產生下一段，停止延伸")
            break
        elif len(remaining_sites) == 1:
            # 只有一個新站點，找出是哪個舊站點被重用
            new_site = remaining_sites[0]
            
            # 找出共同站點（在 all_intersected_sites 和 current_generating_sites 中都出現）
            common_sites = [s for s in all_intersected_sites if s == prev_site1 or s == prev_site2]
            
            if len(common_sites) == 1:
                common_site = common_sites[0]
                # 找出另一個舊站點
                other_prev_site = prev_site1 if common_site == prev_site2 else prev_site2
                
                print(f"{'  '*depth}  [繼續 Hyperplane] 共同站點: ({common_site.x:.1f}, {common_site.y:.1f})")
                print(f"{'  '*depth}  [繼續 Hyperplane] 新站點: ({new_site.x:.1f}, {new_site.y:.1f})")
                print(f"{'  '*depth}  [繼續 Hyperplane] 保留站點: ({other_prev_site.x:.1f}, {other_prev_site.y:.1f})")
                print(f"{'  '*depth}  [繼續 Hyperplane] 下一段將由 ({other_prev_site.x:.1f}, {other_prev_site.y:.1f}) 和 ({new_site.x:.1f}, {new_site.y:.1f}) 產生")
                
                current_generating_sites = (other_prev_site, new_site)
            else:
                print(f"{'  '*depth}  [繼續 Hyperplane] 錯誤：找到 {len(common_sites)} 個共同站點（應為1個），停止延伸")
                break
                
        elif len(remaining_sites) == 2:
            # 有兩個新站點，這是重疊中垂線的情況
            site1 = remaining_sites[0]
            site2 = remaining_sites[1]
            
            print(f"{'  '*depth}  [繼續 Hyperplane] 檢測到重疊中垂線！")
            print(f"{'  '*depth}  [繼續 Hyperplane] 兩個新站點: ({site1.x:.1f}, {site1.y:.1f}) 和 ({site2.x:.1f}, {site2.y:.1f})")
            print(f"{'  '*depth}  [繼續 Hyperplane] 下一段將由這兩個站點產生")
            
            current_generating_sites = (site1, site2)
            
        else:
            # 有超過2個新站點，無法自動處理
            from tkinter import messagebox
            messagebox.showwarning("警告", 
                f"Hyperplane 碰撞到 {len(remaining_sites)} 個新站點，無法自動決定下一段的產生點。\n"
                f"涉及站點數：{len(all_intersected_sites)}\n"
                f"當前產生點：2個\n"
                f"新站點：{len(remaining_sites)}個")
            print(f"{'  '*depth}  [繼續 Hyperplane] 警告：有 {len(remaining_sites)} 個新站點，無法自動處理，停止延伸")
            break
        
        # 計算新的中垂線（使用更新後的 current_generating_sites）
        site_a, site_c = current_generating_sites
        
        # 計算中點
        mid_x = (site_a.x + site_c.x) / 2.0
        mid_y = (site_a.y + site_c.y) / 2.0
        
        # 計算中垂線的方向向量（垂直於 A-C 連線）
        dx = site_c.x - site_a.x
        dy = site_c.y - site_a.y
        
        # 垂直方向（旋轉90度）
        direction_x = -dy
        direction_y = dx
        
        # 正規化方向向量
        length = math.sqrt(direction_x**2 + direction_y**2)
        if length > 1e-9:
            direction_x /= length
            direction_y /= length
        
        # 從碰撞點開始，往下延伸（Y 增加方向）
        # 確保方向向量指向下方（direction_y > 0）
        if direction_y < 0:
            direction_x = -direction_x
            direction_y = -direction_y
        
        print(f"{'  '*depth}  [繼續 Hyperplane] 中垂線方向: ({direction_x:.3f}, {direction_y:.3f})")
        
        # 修改:大幅增加延伸長度
        extension_length = 40000  # 原本是 2000
        next_end_x = new_end.x + direction_x * extension_length
        next_end_y = new_end.y + direction_y * extension_length
        
        # 更新當前的起點和終點
        current_start = new_end  # 新的起點是上一次的碰撞點
        current_end = Point(next_end_x, next_end_y)
        
        print(f"{'  '*depth}  [繼續 Hyperplane] 準備下一段: ({current_start.x:.1f}, {current_start.y:.1f}) -> ({current_end.x:.1f}, {current_end.y:.1f})")
    
    if iteration >= MAX_ITERATIONS:
        print(f"{'  '*depth}  [繼續 Hyperplane] 警告：達到最大迭代次數 {MAX_ITERATIONS}，停止延伸")
    
    print(f"{'  '*depth}  [繼續 Hyperplane] 完成，共創建 {len(all_hyperplane_edges)} 段 hyperplane")
    
    # 整條 hyperplane 完成後，清理孤立邊
    print(f"{'  '*depth}  [繼續 Hyperplane] 開始清理孤立邊...")
    removed_edges = vd.remove_orphaned_edges()
    if removed_edges:
        print(f"{'  '*depth}  [繼續 Hyperplane] 清理了 {len(removed_edges)} 條孤立邊")
    else:
        print(f"{'  '*depth}  [繼續 Hyperplane] 沒有孤立邊需要清理")
    
    return all_hyperplane_edges


def extend_line_to_boundary(mid_x, mid_y, direction_x, direction_y):
    """
    將中垂線從中點延伸到計算邊界
    返回兩個端點 (x1, y1, x2, y2)
    """
    # 計算延伸到邊界所需的參數 t
    # 我們需要找到線段與矩形邊界的交點
    
    # 防止除零
    if abs(direction_x) < 1e-9 and abs(direction_y) < 1e-9:
        return (mid_x, mid_y, mid_x, mid_y)
    
    # 計算與四條邊界的交點
    t_values = []
    
    # 左邊界 (x = CALC_MIN)
    if abs(direction_x) > 1e-9:
        t = (CALC_MIN - mid_x) / direction_x
        t_values.append(t)
    
    # 右邊界 (x = CALC_MAX_X)
    if abs(direction_x) > 1e-9:
        t = (CALC_MAX_X - mid_x) / direction_x
        t_values.append(t)
    
    # 上邊界 (y = CALC_MIN)
    if abs(direction_y) > 1e-9:
        t = (CALC_MIN - mid_y) / direction_y
        t_values.append(t)
    
    # 下邊界 (y = CALC_MAX_Y)
    if abs(direction_y) > 1e-9:
        t = (CALC_MAX_Y - mid_y) / direction_y
        t_values.append(t)
    
    # 如果沒有交點，使用一個大的值
    if not t_values:
        large_t = 2000
        t_values = [-large_t, large_t]
    
    # 取最小和最大的 t 值
    t_min = min(t_values)
    t_max = max(t_values)
    
    # 計算兩個端點
    x1 = mid_x + t_min * direction_x
    y1 = mid_y + t_min * direction_y
    x2 = mid_x + t_max * direction_x
    y2 = mid_y + t_max * direction_y
    
    return (x1, y1, x2, y2)


def clip_to_canvas(x, y):
    """將座標裁剪到畫布範圍內"""
    x = max(0, min(CANVAS_WIDTH, x))
    y = max(0, min(CANVAS_HEIGHT, y))
    return (x, y)


def clip_line_to_canvas(x1, y1, x2, y2):
    """
    使用 Cohen-Sutherland 算法將線段裁剪到畫布範圍
    返回裁剪後的線段端點，如果完全在畫布外則返回 None
    """
    # 定義區域碼
    INSIDE = 0  # 0000
    LEFT = 1    # 0001
    RIGHT = 2   # 0010
    BOTTOM = 4  # 0100
    TOP = 8     # 1000
    
    def compute_code(x, y):
        """計算點的區域碼"""
        code = INSIDE
        if x < 0:
            code |= LEFT
        elif x > CANVAS_WIDTH:
            code |= RIGHT
        if y < 0:
            code |= TOP
        elif y > CANVAS_HEIGHT:
            code |= BOTTOM
        return code
    
    # 計算兩個端點的區域碼
    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)
    
    accept = False
    
    while True:
        # 情況1: 兩點都在畫布內
        if code1 == 0 and code2 == 0:
            accept = True
            break
        
        # 情況2: 兩點在畫布同一側外部
        elif (code1 & code2) != 0:
            break
        
        # 情況3: 部分在內部，需要裁剪
        else:
            # 選擇一個在外部的點
            code_out = code1 if code1 != 0 else code2
            
            # 計算交點
            if code_out & TOP:  # 上邊界 y = 0
                x = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
                y = 0
            elif code_out & BOTTOM:  # 下邊界 y = CANVAS_HEIGHT
                x = x1 + (x2 - x1) * (CANVAS_HEIGHT - y1) / (y2 - y1)
                y = CANVAS_HEIGHT
            elif code_out & RIGHT:  # 右邊界 x = CANVAS_WIDTH
                y = y1 + (y2 - y1) * (CANVAS_WIDTH - x1) / (x2 - x1)
                x = CANVAS_WIDTH
            elif code_out & LEFT:  # 左邊界 x = 0
                y = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
                x = 0
            
            # 更新端點和區域碼
            if code_out == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)
    
    if accept:
        return (x1, y1, x2, y2)
    else:
        return None


# 主程式部分
class VoronoiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voronoi Diagram")
        
        # 創建主框架
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側畫布框架
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 畫布
        self.canvas = tk.Canvas(canvas_frame, width=600, height=600, bg="white")
        self.canvas.pack()
        
        # 右側資訊面板框架
        info_frame = tk.Frame(main_frame, width=200, bg="lightgray")
        info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        info_frame.pack_propagate(False)  # 保持固定寬度
        
        # 座標顯示區域
        coord_label = tk.Label(info_frame, text="滑鼠座標", font=("Arial", 12, "bold"), bg="lightgray")
        coord_label.pack(pady=10)
        
        self.coord_display = tk.Label(info_frame, text="X: --\nY: --", 
                                     font=("Arial", 11), bg="white", 
                                     relief=tk.SUNKEN, width=15, height=3)
        self.coord_display.pack(pady=5, padx=10)
        
        # 分隔線
        separator1 = tk.Frame(info_frame, height=2, bg="gray")
        separator1.pack(fill=tk.X, padx=10, pady=10)
        
        # 點數統計
        stats_label = tk.Label(info_frame, text="統計資訊", font=("Arial", 12, "bold"), bg="lightgray")
        stats_label.pack(pady=(10, 5))
        
        self.stats_display = tk.Label(info_frame, text="點數: 0\n邊數: 0\n頂點數: 0", 
                                     font=("Arial", 9), bg="white", 
                                     relief=tk.SUNKEN, width=18, height=12,
                                     justify=tk.LEFT, anchor="nw")
        self.stats_display.pack(pady=5, padx=10)
        
        # 分隔線
        separator2 = tk.Frame(info_frame, height=2, bg="gray")
        separator2.pack(fill=tk.X, padx=10, pady=10)
        
        # 核心資料
        self.points = []  # 當前的點集合
        self.groups = []  # 從檔案讀取的多組測試資料
        self.current_group = 0  # 當前顯示的組別
        self.vd = VoronoiDiagram()  # Voronoi Diagram 實例
        
        # Step-by-step 控制
        self.is_step_mode = False  # 是否處於step模式
        self.current_step = -1  # -1表示顯示完整結果
        self.steps_calculated = False  # 是否已計算過步驟
        self.previous_points = []  # 上次計算的點集
        
        # UI 控制
        self.show_convex_hull = tk.BooleanVar(value=False)
        self.show_merged_hull = tk.BooleanVar(value=False)
        
        # 初始化顯示
        self.update_stats_display()
        self.update_step_display()

        # 按鈕
        self.run_button = tk.Button(root, text="Run", command=self.run_voronoi)
        self.run_button.pack(side=tk.LEFT)
        self.step_button = tk.Button(root, text="Step by Step", command=self.step_voronoi)
        self.step_button.pack(side=tk.LEFT)
        
        self.load_button = tk.Button(root, text="Load File", command=self.load_file)
        self.load_button.pack(side=tk.LEFT)
        self.clear_button = tk.Button(root, text="Clear Points", command=self.clear_points)
        self.clear_button.pack(side=tk.LEFT)
        self.next_button = tk.Button(root, text="Next Group", command=self.next_group)
        self.next_button.pack(side=tk.LEFT)
        self.prev_button = tk.Button(root, text="Previous Group", command=self.prev_group)
        self.prev_button.pack(side=tk.LEFT)
        
        # 輸出按鈕
        self.export_button = tk.Button(root, text="Export to File", command=self.export_result)
        self.export_button.pack(side=tk.LEFT)
        
        # 輸入按鈕
        self.import_button = tk.Button(root, text="Import from File", command=self.import_and_display)
        self.import_button.pack(side=tk.LEFT)
        
        # 切換顯示選項
        self.hull_toggle = tk.Checkbutton(root, text="Show Convex Hull", 
                                         variable=self.show_convex_hull, 
                                         command=self.refresh_display)
        self.hull_toggle.pack(side=tk.LEFT)
        
        self.merged_hull_toggle = tk.Checkbutton(root, text="Show Merged Hull", 
                                                variable=self.show_merged_hull, 
                                                command=self.refresh_display)
        self.merged_hull_toggle.pack(side=tk.LEFT)
        
        # 滑鼠事件
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        
        # 鍵盤事件
        self.root.bind("<Key>", self.on_key_press)
    
    def on_key_press(self, event):
        """處理鍵盤按鍵事件"""
        key = event.keysym.lower()
        
        if key == 'e':
            # E 鍵：輸出到檔案
            self.export_result()
        elif key == 'i':
            # I 鍵：從檔案讀取
            self.import_and_display()
        elif key == 'c':
            # C 鍵：清空
            self.clear_points()
        elif key == 'v':
            # V 鍵：計算 Voronoi
            self.run_voronoi()
        elif key == 's':
            # S 鍵：Step by step
            self.step_voronoi()
        elif key == 'left':
            # 左箭頭：上一步
            self.prev_step()
        elif key == 'right':
            # 右箭頭：下一步
            self.next_step()
    
    def on_mouse_move(self, event):
        """處理滑鼠移動事件，更新座標顯示"""
        x, y = event.x, event.y
        self.coord_display.config(text=f"X: {x}\nY: {y}")
    
    def on_mouse_leave(self, event):
        """處理滑鼠離開畫布事件"""
        self.coord_display.config(text="X: --\nY: --")
    
    def update_stats_display(self):
        """更新統計資訊顯示"""
        num_sites = len(self.vd.sites) if hasattr(self, 'vd') else len(self.points)
        num_edges = len(self.vd.edges) if hasattr(self, 'vd') else 0
        num_vertices = len(self.vd.vertices) if hasattr(self, 'vd') else 0
        
        # 顯示座標列表
        coords_text = ""
        if self.points:
            coords_text = "\n座標列表:\n"
            for i, (x, y) in enumerate(self.points[-5:], start=max(0, len(self.points)-5)):
                coords_text += f"  {i+1}. ({x:.0f}, {y:.0f})\n"
            if len(self.points) > 5:
                coords_text = f"\n...（共{len(self.points)}點）\n" + coords_text
        
        self.stats_display.config(
            text=f"點數: {num_sites}\n邊數: {num_edges}\n頂點數: {num_vertices}{coords_text}"
        )
    
    def update_step_display(self):
        """更新步驟顯示（預留用於顯示當前步驟資訊）"""
        pass
    
    def add_point(self, event):
        """處理滑鼠點擊，添加點"""
        x, y = event.x, event.y
        self.points.append((x, y))
        
        # 重繪所有點：舊點為黑色，新點為紅色
        self.redraw_points()
        self.update_stats_display()
        print(f"添加點: ({x}, {y})")
    
    def redraw_points(self):
        """重繪所有點：最後一個點為紅色（新加入），其餘為黑色"""
        self.canvas.delete("all")
        
        # 繪製舊點（黑色）
        for i, (x, y) in enumerate(self.points[:-1]):
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black", outline="black")
        
        # 繪製新點（紅色）
        if self.points:
            x, y = self.points[-1]
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", outline="red")
    
    def load_file(self):
        """從文件讀取點資料"""
        file_path = filedialog.askopenfilename(
            title="選擇測試檔案",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.groups = []
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # 跳過空行和註解
                if not line or line.startswith('#'):
                    i += 1
                    continue
                
                try:
                    n = int(line)
                    if n == 0:
                        print("讀入點數為零，檔案測試停止")
                        break
                    
                    # 讀取 n 個點
                    points = []
                    for j in range(n):
                        i += 1
                        if i >= len(lines):
                            break
                        
                        point_line = lines[i].strip()
                        
                        # 跳過註解行
                        while point_line.startswith('#') or not point_line:
                            i += 1
                            if i >= len(lines):
                                break
                            point_line = lines[i].strip()
                        
                        if point_line and not point_line.startswith('#'):
                            parts = point_line.split()
                            if len(parts) >= 2:
                                x, y = float(parts[0]), float(parts[1])
                                points.append((x, y))
                    
                    if points:
                        self.groups.append(points)
                        print(f"讀入第 {len(self.groups)} 組: {len(points)} 個點")
                
                except ValueError:
                    pass
                
                i += 1
            
            if self.groups:
                messagebox.showinfo("讀取成功", f"成功讀取 {len(self.groups)} 組測試資料")
                self.current_group = 0
                self.load_current_group()
            else:
                messagebox.showwarning("讀取失敗", "未找到有效的測試資料")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取檔案時發生錯誤：{str(e)}")
    
    def load_current_group(self):
        """載入當前組的點"""
        if 0 <= self.current_group < len(self.groups):
            self.canvas.delete("all")
            self.vd.clear()
            self.points = self.groups[self.current_group].copy()
            self.reset_state()
            
            # 繪製所有點為黑色（已載入的點）
            for x, y in self.points:
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black", outline="black")
            
            self.update_stats_display()
            print(f"\n載入第 {self.current_group + 1}/{len(self.groups)} 組: {len(self.points)} 個點")
            print(f"座標: {self.points}")
    
    def next_group(self):
        """載入下一組測試資料"""
        if not self.groups:
            messagebox.showinfo("提示", "請先載入測試檔案")
            return
        
        if self.current_group < len(self.groups) - 1:
            self.current_group += 1
            self.load_current_group()
        else:
            messagebox.showinfo("提示", "已經是最後一組資料")
    
    def prev_group(self):
        """載入上一組測試資料"""
        if not self.groups:
            messagebox.showinfo("提示", "請先載入測試檔案")
            return
        
        if self.current_group > 0:
            self.current_group -= 1
            self.load_current_group()
        else:
            messagebox.showinfo("提示", "已經是第一組資料")
    
    def clear_points(self):
        """清空所有點和資料"""
        self.canvas.delete("all")
        self.points.clear()
        self.vd.clear()
        self.groups.clear()
        self.current_group = 0
        self.reset_state()
        self.update_stats_display()
        print("清空所有資料")
    
    def export_result(self):
        """輸出 Voronoi Diagram 結果到文字檔案"""
        if not self.vd.edges or len(self.vd.sites) == 0:
            messagebox.showwarning("無法輸出", "請先計算 Voronoi Diagram！")
            return
        
        # 使用檔案對話框讓使用者選擇儲存位置
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="output.txt",
            title="儲存 Voronoi Diagram 結果"
        )
        
        if filename:
            self.export_to_text_file(filename)
    
    def import_and_display(self):
        """讀取輸出文字檔案並顯示圖形"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="讀取 Voronoi Diagram 輸出檔案"
        )
        
        if not filename:
            return
        
        try:
            points = []
            edges = []
            
            # 讀取檔案
            with open(filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) == 0:
                        continue
                    
                    if parts[0] == 'P':
                        # 點：P x y
                        if len(parts) >= 3:
                            try:
                                x, y = float(parts[1]), float(parts[2])
                                points.append((int(round(x)), int(round(y))))
                            except ValueError:
                                print(f"警告：第 {line_num} 行點座標格式錯誤: {line}")
                                continue
                    elif parts[0] == 'E':
                        # 線段：E x1 y1 x2 y2
                        if len(parts) >= 5:
                            try:
                                x1, y1 = float(parts[1]), float(parts[2])
                                x2, y2 = float(parts[3]), float(parts[4])
                                edges.append((int(round(x1)), int(round(y1)), 
                                            int(round(x2)), int(round(y2))))
                            except ValueError:
                                print(f"警告：第 {line_num} 行線段座標格式錯誤: {line}")
                                continue
            
            if len(points) == 0:
                messagebox.showwarning("讀取失敗", "檔案中沒有找到任何點（P 開頭的行）")
                return
            
            print(f"成功讀取: {len(points)} 個點, {len(edges)} 條線段")
            
            # 清空當前顯示
            self.canvas.delete("all")
            self.reset_state()
            
            # 繪製讀取的圖形
            self.draw_imported_diagram(points, edges)
            
            # 更新統計資訊
            stats_text = (
                f"【從檔案讀取】\n"
                f"檔案: {filename.split('/')[-1]}\n"
                f"\n"
                f"點數: {len(points)}\n"
                f"線段數: {len(edges)}\n"
            )
            self.stats_display.config(text=stats_text)
            
            messagebox.showinfo("讀取成功", 
                f"成功讀取並顯示 Voronoi Diagram\n\n"
                f"輸入點數: {len(points)}\n"
                f"線段數: {len(edges)}")
            
        except FileNotFoundError as e:
            messagebox.showerror("錯誤", f"找不到檔案\n\n錯誤: {e}")
        except ValueError as e:
            messagebox.showerror("格式錯誤", f"檔案格式不正確\n\n錯誤: {e}")
        except Exception as e:
            messagebox.showerror("讀取失敗", f"無法讀取檔案\n\n錯誤: {e}")
    
    def draw_imported_diagram(self, points, edges):
        """繪製從檔案讀取的 Voronoi Diagram
        
        Args:
            points: 點的列表 [(x, y), ...]
            edges: 線段的列表 [(x1, y1, x2, y2), ...]
        """
        # 繪製線段（中垂線）
        for x1, y1, x2, y2 in edges:
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="black",
                width=2,
                tags="voronoi_edge"
            )
        
        # 繪製輸入點
        for x, y in points:
            self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill="blue",
                outline="darkblue",
                width=2,
                tags="site"
            )
            # 標註座標
            self.canvas.create_text(
                x, y - 15,
                text=f"({x},{y})",
                font=("Arial", 8),
                fill="blue",
                tags="site_label"
            )
    
    def reset_state(self):
        """重置計算狀態"""
        self.current_step = -1
        self.is_step_mode = False
        self.steps_calculated = False
        self.previous_points = []
    
    def run_voronoi(self):
        """執行 Voronoi Diagram 計算並直接顯示最終結果"""
        if not self.points:
            messagebox.showwarning("警告", "請先添加點或載入測試資料")
            return
        
        try:
            # 初始化
            self.vd.clear()
            for x, y in self.points:
                self.vd.add_site(x, y)
            
            print(f"\n===== 執行 Run - 計算 Voronoi Diagram =====")
            print(f"點數: {len(self.points)}")
            
            # 執行計算
            self.compute_voronoi_divide_conquer()
            
            # 設置為最終結果模式
            self.is_step_mode = False
            self.current_step = -1
            
            # 繪製結果
            self.draw_voronoi_result()
            
            print(f"完成！產生 {len(self.vd.edges)} 條邊，{len(self.vd.vertices)} 個頂點")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"計算過程發生錯誤：{str(e)}")
            print(f"錯誤詳情：{e}")
            import traceback
            traceback.print_exc()
    
    def step_voronoi(self):
        """Step by Step 模式 - 逐步展示計算過程"""
        if not self.points:
            messagebox.showwarning("警告", "請先添加點或載入測試資料")
            return
        
        # 第一次執行或點集改變：計算所有步驟
        if self.points != self.previous_points or not self.steps_calculated:
            try:
                # 初始化
                self.vd.clear()
                for x, y in self.points:
                    self.vd.add_site(x, y)
                
                print(f"\n===== 執行 Step by Step - 計算所有步驟 =====")
                print(f"點數: {len(self.points)}")
                
                # 背後執行完整計算並記錄步驟
                self.compute_voronoi_divide_conquer()
                
                # 設置狀態
                self.previous_points = self.points.copy()
                self.steps_calculated = True
                self.is_step_mode = True
                self.current_step = 0
                
                print(f"計算完成！共 {len(self.vd.merge_steps)} 個步驟")
                
            except Exception as e:
                messagebox.showerror("錯誤", f"計算過程發生錯誤：{str(e)}")
                print(f"錯誤詳情：{e}")
                import traceback
                traceback.print_exc()
                return
        else:
            # 前進到下一步
            if self.current_step < len(self.vd.merge_steps) - 1:
                self.current_step += 1
                print(f"\n前進到步驟 {self.current_step + 1}/{len(self.vd.merge_steps)}")
            else:
                # 已經是最後一步，不顯示提示視窗
                print(f"\n已經是最後一步 ({len(self.vd.merge_steps)}/{len(self.vd.merge_steps)})")
                return
        
        # 繪製當前步驟
        self.draw_current_step()
    
    def draw_current_step(self):
        """繪製當前步驟的狀態 - 用顏色區分不同狀態的點"""
        self.canvas.delete("all")
        
        if not self.vd.merge_steps or self.current_step < 0:
            return
        
        step = self.vd.merge_steps[self.current_step]
        
        # 獲取當前正在處理的點集 - 使用列表而非集合
        current_processing = []
        if step.left_sites:
            current_processing.extend(step.left_sites)
        if step.right_sites:
            current_processing.extend(step.right_sites)
        
        # 繪製所有站點 - 根據狀態使用不同顏色
        for site in self.vd.sites:
            if site in current_processing:
                # 正在處理的點 - 紅色（突出顯示）
                color = "red"
                radius = 4
            else:
                # 其他點 - 灰色（已處理或未處理）
                color = "gray"
                radius = 3
            
            self.canvas.create_oval(
                site.x-radius, site.y-radius, 
                site.x+radius, site.y+radius,
                fill=color, outline=color
            )
        
        # 繪製邊：如果有 left_edges 和 right_edges，使用它們；否則根據步驟類型決定
        has_step_edges = (step.left_edges or step.right_edges)
        
        if has_step_edges:
            # 繪製左半邊的邊（藍色）- 裁剪到畫布
            for edge in step.left_edges:
                if edge.start and edge.end:
                    clipped = clip_line_to_canvas(edge.start.x, edge.start.y, edge.end.x, edge.end.y)
                    if clipped:
                        x1, y1, x2, y2 = clipped
                        # hyperplane 用橘色，其他用藍色
                        color = "orange" if edge.is_hyperplane else "blue"
                        width = 2
                        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            
            # 繪製右半邊的邊（綠色或橘色）- 裁剪到畫布
            for edge in step.right_edges:
                if edge.start and edge.end:
                    clipped = clip_line_to_canvas(edge.start.x, edge.start.y, edge.end.x, edge.end.y)
                    if clipped:
                        x1, y1, x2, y2 = clipped
                        # hyperplane 用橘色，其他用綠色
                        color = "orange" if edge.is_hyperplane else "green"
                        width = 2
                        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        else:
            # 沒有 step-specific 的邊
            # 只有在「合併」步驟時才繪製所有累積的邊，分割步驟不繪製任何邊
            if "合併" in step.description:
                for edge in self.vd.edges:
                    if edge.start and edge.end:
                        clipped = clip_line_to_canvas(edge.start.x, edge.start.y, edge.end.x, edge.end.y)
                        if clipped:
                            x1, y1, x2, y2 = clipped
                            # hyperplane 用橘色實線，其他邊用藍色細線
                            color = "orange" if edge.is_hyperplane else "blue"
                            width = 2 if edge.is_hyperplane else 1
                            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        
        # 繪製 Convex Hull（如果選項開啟）
        if self.show_convex_hull.get():
            # 繪製左側凸包（藍色虛線）
            if step.left_hull and step.left_hull.edges:
                for p1, p2 in step.left_hull.edges:
                    self.canvas.create_line(
                        p1.x, p1.y, p2.x, p2.y, 
                        fill="cyan", width=2, dash=(4, 2)
                    )
            
            # 繪製右側凸包（綠色虛線）
            if step.right_hull and step.right_hull.edges:
                for p1, p2 in step.right_hull.edges:
                    self.canvas.create_line(
                        p1.x, p1.y, p2.x, p2.y, 
                        fill="lime", width=2, dash=(4, 2)
                    )
        
        # 繪製合併後的凸包（如果選項開啟）
        if self.show_merged_hull.get():
            if step.merged_hull and step.merged_hull.edges:
                for p1, p2 in step.merged_hull.edges:
                    self.canvas.create_line(
                        p1.x, p1.y, p2.x, p2.y, 
                        fill="purple", width=3, dash=(6, 3)
                    )
        
        # 顯示步驟資訊
        print(f"步驟 {self.current_step + 1}/{len(self.vd.merge_steps)}: {step.description}")
    
    def draw_voronoi_result(self):
        """繪製最終的 Voronoi Diagram 結果"""
        self.canvas.delete("all")
        
        # 繪製所有邊（裁剪到畫布範圍）
        for edge in self.vd.edges:
            if edge.start and edge.end:
                # 使用線段裁剪算法
                clipped = clip_line_to_canvas(edge.start.x, edge.start.y, edge.end.x, edge.end.y)
                if clipped:
                    x1, y1, x2, y2 = clipped
                    
                    color = "orange" if edge.is_hyperplane else "blue"
                    width = 2 if edge.is_hyperplane else 1
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        
        # 繪製 Convex Hull（如果選項開啟且有最後一步）
        if len(self.vd.merge_steps) > 0:
            last_step = self.vd.merge_steps[-1]
            
            if self.show_convex_hull.get():
                # 繪製左側凸包（青色虛線）
                if last_step.left_hull and last_step.left_hull.edges:
                    for p1, p2 in last_step.left_hull.edges:
                        self.canvas.create_line(
                            p1.x, p1.y, p2.x, p2.y, 
                            fill="cyan", width=2, dash=(4, 2)
                        )
                
                # 繪製右側凸包（萊姆色虛線）
                if last_step.right_hull and last_step.right_hull.edges:
                    for p1, p2 in last_step.right_hull.edges:
                        self.canvas.create_line(
                            p1.x, p1.y, p2.x, p2.y, 
                            fill="lime", width=2, dash=(4, 2)
                        )
            
            # 繪製合併後的凸包（如果選項開啟）
            if self.show_merged_hull.get():
                if last_step.merged_hull and last_step.merged_hull.edges:
                    for p1, p2 in last_step.merged_hull.edges:
                        self.canvas.create_line(
                            p1.x, p1.y, p2.x, p2.y, 
                            fill="purple", width=3, dash=(6, 3)
                        )
        
        # 繪製所有 Voronoi 頂點（只繪製在畫布內的）
        for vertex in self.vd.vertices:
            if 0 <= vertex.x <= CANVAS_WIDTH and 0 <= vertex.y <= CANVAS_HEIGHT:
                self.canvas.create_oval(
                    vertex.x-2, vertex.y-2, vertex.x+2, vertex.y+2,
                    fill="orange", outline="orange"
                )
        
        # 繪製所有站點（原始輸入點）- 黑色
        for site in self.vd.sites:
            self.canvas.create_oval(
                site.x-3, site.y-3, site.x+3, site.y+3,
                fill="black", outline="black"
            )
        
        self.update_stats_display()
    
    def refresh_display(self):
        """刷新顯示（用於切換顯示選項時）"""
        if self.is_step_mode and self.current_step >= 0:
            self.draw_current_step()
        else:
            # 如果還沒有點擊 Step by Step 或 Run（沒有進行計算）
            if not self.steps_calculated and len(self.vd.merge_steps) == 0:
                self.canvas.delete("all")
                # 繪製站點：優先使用 self.points，其次使用 self.vd.sites
                if self.points:
                    for x, y in self.points:
                        self.canvas.create_oval(
                            x-3, y-3, x+3, y+3,
                            fill="black", outline="black"
                        )
                else:
                    for site in self.vd.sites:
                        self.canvas.create_oval(
                            site.x-3, site.y-3, site.x+3, site.y+3,
                            fill="black", outline="black"
                        )
            else:
                # 已經計算過 Voronoi，顯示完整結果
                self.draw_voronoi_result()
    
    def compute_voronoi_divide_conquer(self):
        """使用 Divide and Conquer 方法計算 Voronoi Diagram"""
        if len(self.vd.sites) == 0:
            return
        
        # 按 x 座標排序站點
        sorted_sites = sorted(self.vd.sites, key=lambda s: (s.x, s.y))
        print(f"開始 Divide and Conquer，站點數: {len(sorted_sites)}")
        
        # 遞迴分治
        self._divide_conquer_recursive(sorted_sites, 0)

        # =========================================================
        # 新增：最終全域清理
        # 遞迴結束後，針對最上層合併可能殘留的孤立邊進行最後一次掃描
        # =========================================================
        print(f"===== 計算結束，執行最終孤立邊清理 =====")
        final_removed = self.vd.remove_orphaned_edges()
        if final_removed:
            print(f"最終清理移除 {len(final_removed)} 條邊")
            
            # 如果有移除邊，記錄一個額外的步驟以便 Step-by-Step 觀察
            step = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"[最終清理] 移除 {len(final_removed)} 條殘留孤立邊",
                left_sites=sorted_sites,
                right_sites=[],
                # 這裡簡單複製最後一個狀態的凸包
                left_hull=self.vd.merge_steps[-1].merged_hull if self.vd.merge_steps else None,
                merged_hull=self.vd.merge_steps[-1].merged_hull if self.vd.merge_steps else None
            )
            self.vd.merge_steps.append(step)
    
    def _divide_conquer_recursive(self, sites, depth):
        """
        遞迴的分治方法
        sites: 當前要處理的站點列表
        depth: 遞迴深度（用於記錄步驟）
        """
        n = len(sites)
        
        # 基本情況：1個點
        if n == 1:
            print(f"  {'  '*depth}[警告] 出現單一點的情況，這不應該發生！")
            # messagebox.showwarning("警告", 
            #     f"遞迴過程中出現單一點，請檢查點分割邏輯\n點座標: ({sites[0].x:.1f}, {sites[0].y:.1f})")
            
            # 計算單點的凸包
            left_hull = compute_convex_hull([])
            right_hull = compute_convex_hull([sites[0]])
            merged_hull = compute_convex_hull([sites[0]])
            
            step = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"[異常] 單一點 ({sites[0].x:.1f}, {sites[0].y:.1f})",
                left_sites=[],
                right_sites=[sites[0]],
                left_hull=left_hull,
                right_hull=right_hull,
                merged_hull=merged_hull
            )
            self.vd.merge_steps.append(step)
            return
        
        # 基本情況：2個點
        elif n == 2:
            self._handle_two_points(sites[0], sites[1], depth)
        
        # 基本情況：3個點
        elif n == 3:
            self._handle_three_points(sites[0], sites[1], sites[2], depth)
        
        # 遞迴情況：大於3個點
        else:
            # 分割：找中間點
            mid = n // 2
            
            # 優化分割：如果中間點切在相同的 X 座標上，嘗試尋找更好的分割點
            # 這樣可以確保左半部和右半部的 X 座標盡量不重疊，減少合併時的幾何錯誤
            if sites[mid-1].x == sites[mid].x:
                # 向左尋找第一個 X 座標不同的位置
                l_split = mid
                while l_split > 0 and sites[l_split-1].x == sites[l_split].x:
                    l_split -= 1
                
                # 向右尋找第一個 X 座標不同的位置
                r_split = mid
                while r_split < n and sites[r_split-1].x == sites[r_split].x:
                    r_split += 1
                
                # 評估哪個分割點更好（更接近中間，且有效）
                valid_l = l_split > 0
                valid_r = r_split < n
                
                if valid_l and valid_r:
                    # 兩邊都有效，選離中間最近的
                    if (mid - l_split) <= (r_split - mid):
                        mid = l_split
                    else:
                        mid = r_split
                elif valid_l:
                    mid = l_split
                elif valid_r:
                    mid = r_split
                # 如果都無效（所有點 X 都相同），則保持原來的 mid (按 Y 排序分割)

            left_sites = sites[:mid]
            right_sites = sites[mid:]
            
            # 計算分割時的凸包
            left_hull = compute_convex_hull(left_sites)
            right_hull = compute_convex_hull(right_sites)
            merged_hull = compute_convex_hull(sites)
            
            # 記錄分割步驟
            step = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"{'  '*depth}分割：左 {len(left_sites)} 點，右 {len(right_sites)} 點",
                left_sites=left_sites,
                right_sites=right_sites,
                left_hull=left_hull,
                right_hull=right_hull,
                merged_hull=merged_hull
            )
            self.vd.merge_steps.append(step)
            print(f"{'  '*depth}分割：左 {len(left_sites)} 點，右 {len(right_sites)} 點")
            
            # 步驟1: 處理左半邊，記錄左半邊的結果
            print(f"{'  '*depth}步驟1: 處理左半邊")
            self._divide_conquer_recursive(left_sites, depth + 1)
            
            # 收集左半邊處理完成後的所有邊（包括該半邊內部的 hyperplane）
            left_edges_after = []
            for edge in self.vd.edges:
                # 檢查邊是否完全屬於左半邊的站點
                # 條件：site1 和 site2 都在 left_sites 中
                if edge.site1 in left_sites and edge.site2 in left_sites:
                    left_edges_after.append(edge.copy_snapshot())
            
            # 記錄左半邊完成的步驟
            left_hull_after = compute_convex_hull(left_sites)
            step_left = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"{'  '*depth}左半邊完成：{len(left_sites)} 點處理完畢（外心截斷）",
                left_sites=left_sites,
                right_sites=[],
                left_hull=left_hull_after,
                right_hull=compute_convex_hull([]),
                merged_hull=left_hull_after,
                left_edges=left_edges_after,
                right_edges=[]
            )
            self.vd.merge_steps.append(step_left)
            
            # 步驟2: 處理右半邊，記錄右半邊的結果
            print(f"{'  '*depth}步驟2: 處理右半邊")
            self._divide_conquer_recursive(right_sites, depth + 1)
            
            # 收集右半邊處理完成後的所有邊（包括該半邊內部的 hyperplane）
            right_edges_after = []
            for edge in self.vd.edges:
                # 檢查邊是否完全屬於右半邊的站點
                # 條件：site1 和 site2 都在 right_sites 中
                if edge.site1 in right_sites and edge.site2 in right_sites:
                    right_edges_after.append(edge.copy_snapshot())
            
            # 記錄右半邊完成的步驟
            right_hull_after = compute_convex_hull(right_sites)
            step_right = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"{'  '*depth}右半邊完成：{len(right_sites)} 點處理完畢（外心截斷）",
                left_sites=[],
                right_sites=right_sites,
                left_hull=compute_convex_hull([]),
                right_hull=right_hull_after,
                merged_hull=right_hull_after,
                left_edges=[],
                right_edges=right_edges_after
            )
            self.vd.merge_steps.append(step_right)
            
            # 步驟3a: 顯示左右半邊外心截斷完成後的結果（用顏色區分）
            print(f"{'  '*depth}步驟3a: 顯示左右半邊外心截斷結果")
            # 重新收集當前的左右邊（因為之前已經拷貝過了）
            all_left_edges = [e.copy_snapshot() for e in left_edges_after]
            all_right_edges = [e.copy_snapshot() for e in right_edges_after]
            
            step_combined = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"{'  '*depth}合併展示：左右半邊外心截斷結果（合併前）",
                left_sites=left_sites,
                right_sites=right_sites,
                left_hull=compute_convex_hull(left_sites),
                right_hull=compute_convex_hull(right_sites),
                merged_hull=compute_convex_hull(sites),
                left_edges=all_left_edges,
                right_edges=all_right_edges
            )
            self.vd.merge_steps.append(step_combined)
            
            # 步驟3b: 合併左右兩半，計算 hyperplane
            print(f"{'  '*depth}步驟3b: 計算和繪製hyperplane")
            # 重新計算合併時的凸包（因為遞迴後可能有變化）
            left_hull = compute_convex_hull(left_sites)
            right_hull = compute_convex_hull(right_sites)
            merged_hull = compute_convex_hull(sites)
            
            print(f"{'  '*depth}合併：左 {len(left_sites)} 點與右 {len(right_sites)} 點")
            
            # 計算 hyperplane 的端點
            hyperplane_points = compute_hyperplane_points(left_sites, right_sites, merged_hull, left_hull, right_hull)
            hyperplane = None
            
            if hyperplane_points:
                point1, point2 = hyperplane_points
                print(f"{'  '*depth}  計算 hyperplane: ({point1.x:.1f}, {point1.y:.1f}) - ({point2.x:.1f}, {point2.y:.1f})")
                
                # 創建 hyperplane 邊（中垂線）
                edge = self.vd.create_edge(point1, point2)
                edge.is_hyperplane = True
                
                # 計算中點
                mid_x = (point1.x + point2.x) / 2.0
                mid_y = (point1.y + point2.y) / 2.0
                
                # 計算中垂線的方向向量（垂直於兩點連線）
                dx = point2.x - point1.x
                dy = point2.y - point1.y
                
                # 垂直方向（旋轉90度）
                direction_x = -dy
                direction_y = dx
                
                # 正規化方向向量
                length = math.sqrt(direction_x**2 + direction_y**2)
                if length > 1e-9:
                    direction_x /= length
                    direction_y /= length
                
                # 延伸到邊界
                x1, y1, x2, y2 = extend_line_to_boundary(mid_x, mid_y, direction_x, direction_y)
                
                # 創建端點（臨時的，用於截斷計算）
                from datastructer import Point
                temp_start = Point(x1, y1)
                temp_end = Point(x2, y2)
                
                # 收集當前合併層級的邊（只包含左半邊和右半邊的邊，包括 hyperplane）
                # 篩選條件：edge 的兩個站點都在 left_sites 或都在 right_sites 中
                current_level_edges = []
                for e in self.vd.edges:
                    # 檢查是否屬於左半邊
                    if e.site1 in left_sites and e.site2 in left_sites:
                        current_level_edges.append(e)
                    # 檢查是否屬於右半邊
                    elif e.site1 in right_sites and e.site2 in right_sites:
                        current_level_edges.append(e)
                    # 檢查是否為跨越左右的 hyperplane（之前更深層產生的）
                    elif e.is_hyperplane and ((e.site1 in left_sites and e.site2 in right_sites) or 
                                               (e.site1 in right_sites and e.site2 in left_sites)):
                        current_level_edges.append(e)
                
                print(f"{'  '*depth}  -> 當前層級共有 {len(current_level_edges)} 條邊可能與 hyperplane 碰撞")
                
                # 截斷 hyperplane 找到第一個碰撞點
                # 修正：傳入 active_sites=[point1, point2]
                new_end, intersected_edges, all_intersected_sites = truncate_hyperplane(
                    temp_start, temp_end, current_level_edges, left_sites, right_sites, 
                    active_sites=[point1, point2], depth=depth
                )
                
                # 確定第一段 hyperplane 的起始點和結束點
                if new_end:
                    # 找到交點，使用截斷後的結束點
                    final_start = temp_start
                    final_end = new_end
                    
                    print(f"{'  '*depth}  -> 第一段 Hyperplane 從 ({final_start.x:.1f}, {final_start.y:.1f}) 到 ({final_end.x:.1f}, {final_end.y:.1f})")
                    
                    # 創建第一段的頂點
                    start_vertex = self.vd.create_vertex(final_start.x, final_start.y, sites=[point1, point2])
                    end_vertex = self.vd.create_vertex(final_end.x, final_end.y, sites=[point1, point2])
                    
                    # 設置第一段邊的端點
                    edge.start = start_vertex
                    edge.end = end_vertex
                    
                    # 繼續從碰撞點繪製後續的 hyperplane
                    if all_intersected_sites and final_end.y <= CANVAS_HEIGHT:
                        print(f"{'  '*depth}  -> 繼續繪製 hyperplane，從碰撞點開始")
                        print(f"{'  '*depth}  -> 初始產生點: ({point1.x:.1f},{point1.y:.1f}) 和 ({point2.x:.1f},{point2.y:.1f})")
                        print(f"{'  '*depth}  -> 碰撞涉及 {len(all_intersected_sites)} 個站點:")
                        for site in all_intersected_sites:
                            print(f"{'  '*depth}     站點: ({site.x:.1f},{site.y:.1f})")
                        
                        # 從所有涉及的站點中，排除當前 hyperplane 的產生點
                        remaining_sites = [s for s in all_intersected_sites if s != point1 and s != point2]
                        
                        print(f"{'  '*depth}  -> 排除初始產生點後，剩餘 {len(remaining_sites)} 個站點")
                        
                        if len(remaining_sites) == 1:
                            # 單一新站點，找出共同站點
                            new_site = remaining_sites[0]
                            common_sites = [s for s in all_intersected_sites if s == point1 or s == point2]
                            
                            if len(common_sites) == 1:
                                common = common_sites[0]
                                other_from_hyperplane = point1 if common == point2 else point2
                                
                                print(f"{'  '*depth}  -> 共同站點: ({common.x:.1f},{common.y:.1f})")
                                print(f"{'  '*depth}  -> 下一段將由 ({other_from_hyperplane.x:.1f},{other_from_hyperplane.y:.1f}) 和 ({new_site.x:.1f},{new_site.y:.1f}) 產生")
                                
                                # 調用繼續繪製函數
                                from datastructer import Point
                                additional_edges = continue_hyperplane_from_intersection(
                                    self.vd, 
                                    Point(final_end.x, final_end.y),  # 從碰撞點開始
                                    (other_from_hyperplane, new_site),  # 產生點
                                    left_sites, 
                                    right_sites, 
                                    depth
                                )
                                
                                print(f"{'  '*depth}  -> 額外創建了 {len(additional_edges)} 段 hyperplane")
                            else:
                                print(f"{'  '*depth}  -> 錯誤：找到 {len(common_sites)} 個共同站點（應為1個）")
                                
                        elif len(remaining_sites) == 2:
                            # 兩個新站點，這是重疊中垂線的情況
                            site1, site2 = remaining_sites[0], remaining_sites[1]
                            
                            print(f"{'  '*depth}  -> 檢測到重疊中垂線！")
                            print(f"{'  '*depth}  -> 下一段將由 ({site1.x:.1f},{site1.y:.1f}) 和 ({site2.x:.1f},{site2.y:.1f}) 產生")
                            
                            # 調用繼續繪製函數
                            from datastructer import Point
                            additional_edges = continue_hyperplane_from_intersection(
                                self.vd, 
                                Point(final_end.x, final_end.y),  # 從碰撞點開始
                                (site1, site2),  # 產生點
                                left_sites, 
                                right_sites, 
                                depth
                            )
                            
                            print(f"{'  '*depth}  -> 額外創建了 {len(additional_edges)} 段 hyperplane")
                        else:
                            print(f"{'  '*depth}  -> 警告：有 {len(remaining_sites)} 個新站點，無法自動處理")
                    
                else:
                    # 沒找到交點，使用原始端點
                    final_start = temp_start
                    final_end = temp_end
                    
                    # 創建最終的頂點
                    start_vertex = self.vd.create_vertex(final_start.x, final_start.y, sites=[point1, point2])
                    end_vertex = self.vd.create_vertex(final_end.x, final_end.y, sites=[point1, point2])
                    
                    # 設置邊的端點
                    edge.start = start_vertex
                    edge.end = end_vertex
                    
                    print(f"{'  '*depth}  -> 最終 Hyperplane 從 ({final_start.x:.1f}, {final_start.y:.1f}) 到 ({final_end.x:.1f}, {final_end.y:.1f})")
            else:
                print(f"{'  '*depth}  -> 無法計算 hyperplane")
            
            # =================================================================
            # 【關鍵修正】 在合併步驟結束前，強制清理所有孤立邊
            # 這一步確保了即使沒有進入 continue_hyperplane_from_intersection，
            # 由 truncate_hyperplane 產生的孤立線段也會被清除。
            # =================================================================
            print(f"{'  '*depth}  [Merge End] 清理本層級產生的孤立邊...")
            self.vd.remove_orphaned_edges()
            # =================================================================
            
            # 收集當前所有邊的最終狀態（包括被hyperplane截斷後的邊）
            final_left_edges = []
            final_right_edges = []
            final_hyperplane_edges = []
            
            for edge in self.vd.edges:
                # 只收集屬於當前這個合併層級的邊
                if edge.site1 in left_sites and edge.site2 in left_sites:
                    # 左半邊的邊
                    final_left_edges.append(edge.copy_snapshot())
                elif edge.site1 in right_sites and edge.site2 in right_sites:
                    # 右半邊的邊
                    final_right_edges.append(edge.copy_snapshot())
                elif edge.is_hyperplane:
                    # 檢查這個 hyperplane 是否是當前層級的（連接左右兩側的站點）
                    # 如果 site1 在左側且 site2 在右側，或反之
                    if ((edge.site1 in left_sites and edge.site2 in right_sites) or
                        (edge.site1 in right_sites and edge.site2 in left_sites)):
                        final_hyperplane_edges.append(edge.copy_snapshot())
            
            merge_step = MergeStep(
                step_id=len(self.vd.merge_steps),
                description=f"{'  '*depth}合併完成：hyperplane 繪製並截斷完畢",
                left_sites=left_sites,
                right_sites=right_sites,
                left_hull=left_hull,
                right_hull=right_hull,
                merged_hull=merged_hull,
                left_edges=final_left_edges,
                right_edges=final_right_edges + final_hyperplane_edges
            )
            self.vd.merge_steps.append(merge_step)
    
    def _handle_two_points(self, site1, site2, depth):
        """處理兩個點的情況：創建中垂線"""
        print(f"{'  '*depth}處理兩點: ({site1.x:.1f}, {site1.y:.1f}) 和 ({site2.x:.1f}, {site2.y:.1f})")
        
        # 創建中垂線
        edge = self.vd.create_edge(site1, site2)
        
        # 計算中點
        mid_x, mid_y = edge.get_midpoint()
        
        # 計算中垂線的方向向量（垂直於兩點連線）
        dx = site2.x - site1.x
        dy = site2.y - site1.y
        
        # 垂直方向（旋轉90度）
        direction_x = -dy
        direction_y = dx
        
        # 正規化方向向量
        length = math.sqrt(direction_x**2 + direction_y**2)
        if length > 1e-9:
            direction_x /= length
            direction_y /= length
        
        # 延伸到邊界
        x1, y1, x2, y2 = extend_line_to_boundary(mid_x, mid_y, direction_x, direction_y)
        
        # 創建端點
        start_vertex = self.vd.create_vertex(x1, y1, sites=[site1, site2])
        end_vertex = self.vd.create_vertex(x2, y2, sites=[site1, site2])
        
        # 設置邊的端點
        edge.start = start_vertex
        edge.end = end_vertex
        
        # 不記錄步驟，因為這個中間狀態會被後續的 hyperplane 截斷
        # 最終狀態會在父層的「步驟1完成」或「步驟2完成」中被記錄
        
        print(f"{'  '*depth}  -> 中垂線從 ({x1:.1f}, {y1:.1f}) 到 ({x2:.1f}, {y2:.1f})")
    
    def _handle_three_points(self, site1, site2, site3, depth):
        """處理三個點的情況"""
        print(f"{'  '*depth}處理三點: ({site1.x:.1f}, {site1.y:.1f}), ({site2.x:.1f}, {site2.y:.1f}), ({site3.x:.1f}, {site3.y:.1f})")
        
        # 檢查是否共線
        if are_collinear(site1, site2, site3):
            self._handle_three_collinear_points(site1, site2, site3, depth)
        else:
            # 判斷三角形類型：直角 > 鈍角 > 銳角
            is_right = is_right_triangle(site1, site2, site3)
            is_obtuse = is_obtuse_triangle(site1, site2, site3)
            
            if is_right:
                print(f"{'  '*depth}  -> 直角三角形")
                self._handle_right_triangle(site1, site2, site3, depth)
            elif is_obtuse:
                print(f"{'  '*depth}  -> 鈍角三角形")
                self._handle_obtuse_triangle(site1, site2, site3, depth)
            else:
                print(f"{'  '*depth}  -> 銳角三角形")
                self._handle_acute_triangle(site1, site2, site3, depth)
    
    def _handle_three_collinear_points(self, site1, site2, site3, depth):
        """處理三點共線的情況"""
        print(f"{'  '*depth}  -> 三點共線")
        
        # 找出最遠的兩點和中間點
        points = [(site1, 0), (site2, 1), (site3, 2)]
        
        # 按 x 座標排序（如果x相同則按y）
        points.sort(key=lambda p: (p[0].x, p[0].y))
        
        leftmost = points[0][0]
        middle = points[1][0]
        rightmost = points[2][0]
        
        print(f"{'  '*depth}  -> 最左: ({leftmost.x:.1f}, {leftmost.y:.1f})")
        print(f"{'  '*depth}  -> 中間: ({middle.x:.1f}, {middle.y:.1f})")
        print(f"{'  '*depth}  -> 最右: ({rightmost.x:.1f}, {rightmost.y:.1f})")
        
        # 創建兩條中垂線：leftmost-middle 和 middle-rightmost
        edges = []
        
        # 第一條：leftmost 和 middle
        edge1 = self._create_perpendicular_bisector(leftmost, middle, depth)
        edges.append(edge1)
        
        # 第二條：middle 和 rightmost
        edge2 = self._create_perpendicular_bisector(middle, rightmost, depth)
        edges.append(edge2)
        
        # 記錄步驟
        step = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}三點共線：創建兩條平行中垂線",
            left_sites=[leftmost],
            right_sites=[middle, rightmost],
            new_edges=set(edges),
            left_edges=[edge1],
            right_edges=[edge2]
        )
        self.vd.merge_steps.append(step)
    
    def _handle_acute_triangle(self, site1, site2, site3, depth):
        """處理銳角三角形：外心在三角形內部 - 使用外心截斷中垂線"""
        # 計算外心
        circumcenter = calculate_circumcenter(site1, site2, site3)
        
        if circumcenter is None:
            print(f"{'  '*depth}  -> 錯誤：無法計算外心")
            return
        
        cx, cy = circumcenter
        print(f"{'  '*depth}  -> 外心: ({cx:.1f}, {cy:.1f})")
        
        # 創建外心頂點
        center_vertex = self.vd.create_vertex(cx, cy, sites=[site1, site2, site3])
        
        # 創建三條完整的中垂線（未截斷）
        edges = []
        
        # 中垂線 1: site1-site2
        edge1 = self._create_perpendicular_bisector(site1, site2, depth)
        edges.append(edge1)
        
        # 中垂線 2: site2-site3
        edge2 = self._create_perpendicular_bisector(site2, site3, depth)
        edges.append(edge2)
        
        # 中垂線 3: site1-site3
        edge3 = self._create_perpendicular_bisector(site1, site3, depth)
        edges.append(edge3)
        
        # 步驟1: 記錄未截斷的狀態（使用快照複製）
        edges_snapshot = [e.copy_snapshot() for e in edges]
        step1 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}銳角三角形：創建三條完整中垂線（未截斷）",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot),
            left_edges=edges_snapshot[:1],
            right_edges=edges_snapshot[1:]
        )
        self.vd.merge_steps.append(step1)
        
        # 進行截斷
        self._truncate_edge_with_circumcenter(edge1, center_vertex, depth)
        self._truncate_edge_with_circumcenter(edge2, center_vertex, depth)
        self._truncate_edge_with_circumcenter(edge3, center_vertex, depth)
        
        # 步驟2: 記錄截斷後的狀態（使用快照複製，避免後續修改影響）
        edges_snapshot_after = [e.copy_snapshot() for e in edges]
        step2 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}銳角三角形：用外心截斷中垂線",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot_after),
            left_edges=edges_snapshot_after[:1],
            right_edges=edges_snapshot_after[1:]
        )
        self.vd.merge_steps.append(step2)
    
    def _truncate_edge_with_circumcenter(self, edge, center_vertex, depth):
        """
        使用外心截斷中垂線
        邏輯：
        1. 計算起始點、結束點、外心在法向量線上的符號
        2. 保留與外心異號的端點
        3. 將與外心同號的端點替換為外心
        """
        if edge.start is None or edge.end is None:
            print(f"{'  '*depth}    警告：邊的端點未初始化")
            return
        
        # 計算外心在法向量線上的值
        center_value = edge.get_normal_line_value(center_vertex.x, center_vertex.y)
        
        # 計算起始點在法向量線上的值
        start_value = edge.get_normal_line_value(edge.start.x, edge.start.y)
        
        # 計算結束點在法向量線上的值
        end_value = edge.get_normal_line_value(edge.end.x, edge.end.y)
        
        print(f"{'  '*depth}    截斷檢查: 外心={center_value:.2f}, 起點={start_value:.2f}, 終點={end_value:.2f}")
        
        # 判斷符號並替換
        # 如果外心與起始點同號，將起始點替換為外心
        if (center_value > 0 and start_value > 0) or (center_value < 0 and start_value < 0):
            print(f"{'  '*depth}    -> 起始點與外心同號，替換為外心")
            edge.start = center_vertex  # property setter 會自動維護 incident_edges
        
        # 如果外心與結束點同號，將結束點替換為外心
        if (center_value > 0 and end_value > 0) or (center_value < 0 and end_value < 0):
            print(f"{'  '*depth}    -> 結束點與外心同號，替換為外心")
            edge.end = center_vertex  # property setter 會自動維護 incident_edges
    
    def _truncate_edge_with_circumcenter_opposite(self, edge, center_vertex, depth):
        """
        使用外心截斷中垂線（相反邏輯 - 用於鈍角三角形的對邊）
        
        邏輯：
        1. 計算起始點、結束點、外心在法向量線上的符號
        2. 保留與外心同號的端點（相反！）
        3. 將與外心異號的端點替換為外心
        """
        if edge.start is None or edge.end is None:
            print(f"{'  '*depth}    警告：邊的端點未初始化")
            return
        
        # 計算外心在法向量線上的值
        center_value = edge.get_normal_line_value(center_vertex.x, center_vertex.y)
        
        # 計算起始點在法向量線上的值
        start_value = edge.get_normal_line_value(edge.start.x, edge.start.y)
        
        # 計算結束點在法向量線上的值
        end_value = edge.get_normal_line_value(edge.end.x, edge.end.y)
        
        print(f"{'  '*depth}    截斷檢查（相反邏輯）: 外心={center_value:.2f}, 起點={start_value:.2f}, 終點={end_value:.2f}")
        
        # 判斷符號並替換（相反邏輯）
        # 如果外心與起始點異號，將起始點替換為外心
        if (center_value > 0 and start_value < 0) or (center_value < 0 and start_value > 0):
            print(f"{'  '*depth}    -> 起始點與外心異號，替換為外心（相反邏輯）")
            edge.start = center_vertex  # property setter 會自動維護 incident_edges
        
        # 如果外心與結束點異號，將結束點替換為外心
        if (center_value > 0 and end_value < 0) or (center_value < 0 and end_value > 0):
            print(f"{'  '*depth}    -> 結束點與外心異號，替換為外心（相反邏輯）")
            edge.end = center_vertex  # property setter 會自動維護 incident_edges
    
    def _truncate_edge_with_circumcenter_right_opposite(self, edge, center_vertex, right_vertex, depth):
        """
        使用外心截斷中垂線（直角三角形對邊專用）
        
        邏輯：
        1. 計算起始點、結束點、直角頂點在法向量線上的符號
        2. 保留與直角頂點異號的端點
        3. 將與直角頂點同號的端點替換為外心
        """
        if edge.start is None or edge.end is None:
            print(f"{'  '*depth}    警告：邊的端點未初始化")
            return
        
        # 計算直角頂點在法向量線上的值
        right_value = edge.get_normal_line_value(right_vertex.x, right_vertex.y)
        
        # 計算起始點在法向量線上的值
        start_value = edge.get_normal_line_value(edge.start.x, edge.start.y)
        
        # 計算結束點在法向量線上的值
        end_value = edge.get_normal_line_value(edge.end.x, edge.end.y)
        
        print(f"{'  '*depth}    截斷檢查（直角對邊）: 直角頂點={right_value:.2f}, 起點={start_value:.2f}, 終點={end_value:.2f}")
        
        # 判斷符號並替換
        # 如果直角頂點與起始點同號，將起始點替換為外心
        if (right_value > 0 and start_value > 0) or (right_value < 0 and start_value < 0):
            print(f"{'  '*depth}    -> 起始點與直角頂點同號，替換為外心")
            edge.start = center_vertex  # property setter 會自動維護 incident_edges
        
        # 如果直角頂點與結束點同號，將結束點替換為外心
        if (right_value > 0 and end_value > 0) or (right_value < 0 and end_value < 0):
            print(f"{'  '*depth}    -> 結束點與直角頂點同號，替換為外心")
            edge.end = center_vertex  # property setter 會自動維護 incident_edges
    
    def _handle_obtuse_triangle(self, site1, site2, site3, depth):
        """
        處理鈍角三角形：外心在三角形外部
        
        截斷邏輯：
        - 鈍角頂點的兩條鄰邊：保留與外心異號的端點（與銳角相同）
        - 鈍角的對邊：保留與外心同號的端點（相反邏輯）
        
        特殊情況：
        - 如果無法計算外心（角度極大），刪除最遠兩點的中垂線
        """
        # 計算外心
        circumcenter = calculate_circumcenter(site1, site2, site3)
        
        # 找出鈍角頂點和對邊
        obtuse_info = find_obtuse_vertex(site1, site2, site3)
        
        if circumcenter is None:
            print(f"{'  '*depth}  -> 警告：無法計算外心（角度極大）")
            
            if obtuse_info:
                obtuse_vertex, opposite_p1, opposite_p2 = obtuse_info
                print(f"{'  '*depth}  -> 鈍角頂點: ({obtuse_vertex.x:.1f}, {obtuse_vertex.y:.1f})")
                print(f"{'  '*depth}  -> 刪除對邊 ({opposite_p1.x:.1f}, {opposite_p1.y:.1f})-({opposite_p2.x:.1f}, {opposite_p2.y:.1f}) 的中垂線")
                
                # 創建兩條中垂線（排除對邊）
                edges = []
                
                # 找出鈍角頂點相鄰的兩條邊
                if obtuse_vertex == site1:
                    edge1 = self._create_perpendicular_bisector(site1, site2, depth)
                    edge2 = self._create_perpendicular_bisector(site1, site3, depth)
                    edges = [edge1, edge2]
                elif obtuse_vertex == site2:
                    edge1 = self._create_perpendicular_bisector(site1, site2, depth)
                    edge2 = self._create_perpendicular_bisector(site2, site3, depth)
                    edges = [edge1, edge2]
                else:  # obtuse_vertex == site3
                    edge1 = self._create_perpendicular_bisector(site1, site3, depth)
                    edge2 = self._create_perpendicular_bisector(site2, site3, depth)
                    edges = [edge1, edge2]
                
                # 記錄步驟（僅顯示兩條邊）
                step = MergeStep(
                    step_id=len(self.vd.merge_steps),
                    description=f"{'  '*depth}鈍角三角形（極大角度）：創建兩條中垂線，對邊已刪除",
                    left_sites=[site1],
                    right_sites=[site2, site3],
                    new_edges=set(edges),
                    left_edges=edges[:1],
                    right_edges=edges[1:]
                )
                self.vd.merge_steps.append(step)
            else:
                # 找不到鈍角也無外心，可能是數值誤差，使用最遠兩點
                far_p1, far_p2, remaining = find_farthest_two_points(site1, site2, site3)
                print(f"{'  '*depth}  -> 刪除最遠兩點 ({far_p1.x:.1f}, {far_p1.y:.1f})-({far_p2.x:.1f}, {far_p2.y:.1f}) 的中垂線")
                
                # 創建另外兩條中垂線
                edge1 = self._create_perpendicular_bisector(far_p1, remaining, depth)
                edge2 = self._create_perpendicular_bisector(far_p2, remaining, depth)
                edges = [edge1, edge2]
                
                step = MergeStep(
                    step_id=len(self.vd.merge_steps),
                    description=f"{'  '*depth}無法計算外心：創建兩條中垂線",
                    left_sites=[site1],
                    right_sites=[site2, site3],
                    new_edges=set(edges),
                    left_edges=edges[:1],
                    right_edges=edges[1:]
                )
                self.vd.merge_steps.append(step)
            
            return
        
        # 有外心的正常情況
        cx, cy = circumcenter
        print(f"{'  '*depth}  -> 外心: ({cx:.1f}, {cy:.1f}) [三角形外部]")
        
        if not obtuse_info:
            print(f"{'  '*depth}  -> 警告：判定為鈍角但找不到鈍角頂點")
            return
        
        obtuse_vertex, opposite_p1, opposite_p2 = obtuse_info
        print(f"{'  '*depth}  -> 鈍角頂點: ({obtuse_vertex.x:.1f}, {obtuse_vertex.y:.1f})")
        print(f"{'  '*depth}  -> 對邊: ({opposite_p1.x:.1f}, {opposite_p1.y:.1f})-({opposite_p2.x:.1f}, {opposite_p2.y:.1f})")
        
        # 創建外心頂點
        center_vertex = self.vd.create_vertex(cx, cy, sites=[site1, site2, site3])
        
        # 創建三條完整的中垂線
        edges = []
        edge_map = {}  # 用於識別對邊，使用 VoronoiSite 作為 key
        
        edge1 = self._create_perpendicular_bisector(site1, site2, depth)
        edges.append(edge1)
        edge_map[(site1, site2)] = edge1
        edge_map[(site2, site1)] = edge1
        
        edge2 = self._create_perpendicular_bisector(site2, site3, depth)
        edges.append(edge2)
        edge_map[(site2, site3)] = edge2
        edge_map[(site3, site2)] = edge2
        
        edge3 = self._create_perpendicular_bisector(site1, site3, depth)
        edges.append(edge3)
        edge_map[(site1, site3)] = edge3
        edge_map[(site3, site1)] = edge3
        
        # 步驟1: 顯示未截斷的中垂線（使用快照複製）
        edges_snapshot = [e.copy_snapshot() for e in edges]
        step1 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}鈍角三角形：創建三條完整中垂線（未截斷）",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot),
            left_edges=edges_snapshot[:1],
            right_edges=edges_snapshot[1:]
        )
        self.vd.merge_steps.append(step1)
        
        # 找出對邊（使用 VoronoiSite 作為 key）
        opposite_edge = edge_map.get((opposite_p1, opposite_p2))
        
        # 進行截斷
        for edge in edges:
            if edge == opposite_edge:
                # 對邊：使用相反邏輯（保留同號）
                print(f"{'  '*depth}    處理對邊中垂線（使用相反邏輯）")
                self._truncate_edge_with_circumcenter_opposite(edge, center_vertex, depth)
            else:
                # 鄰邊：使用正常邏輯（保留異號）
                self._truncate_edge_with_circumcenter(edge, center_vertex, depth)
        
        # 步驟2: 顯示截斷後的中垂線（使用快照複製，避免後續修改影響）
        edges_snapshot_after = [e.copy_snapshot() for e in edges]
        step2 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}鈍角三角形：用外心截斷中垂線（對邊使用相反邏輯）",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot_after),
            left_edges=edges_snapshot_after[:1],
            right_edges=edges_snapshot_after[1:]
        )
        self.vd.merge_steps.append(step2)
    
    def _handle_right_triangle(self, site1, site2, site3, depth):
        """
        處理直角三角形：外心在斜邊中點
        
        截斷邏輯：
        - 直角頂點的兩條鄰邊：保留與外心異號的端點（與銳角相同）
        - 直角的對邊（斜邊）：保留與直角頂點異號的端點（特殊邏輯）
        """
        # 計算外心
        circumcenter = calculate_circumcenter(site1, site2, site3)
        
        # 找出直角頂點和對邊
        right_info = find_right_vertex(site1, site2, site3)
        
        if circumcenter is None:
            print(f"{'  '*depth}  -> 警告：無法計算外心")
            return
        
        cx, cy = circumcenter
        print(f"{'  '*depth}  -> 外心: ({cx:.1f}, {cy:.1f}) [斜邊中點]")
        
        right_vertex, opposite_p1, opposite_p2 = right_info
        print(f"{'  '*depth}  -> 直角頂點: ({right_vertex.x:.1f}, {right_vertex.y:.1f})")
        print(f"{'  '*depth}  -> 對邊（斜邊）: ({opposite_p1.x:.1f}, {opposite_p1.y:.1f})-({opposite_p2.x:.1f}, {opposite_p2.y:.1f})")
        
        # 創建外心頂點
        center_vertex = self.vd.create_vertex(cx, cy, sites=[site1, site2, site3])
        
        # 創建三條完整的中垂線
        edges = []
        edge_map = {}  # 用於識別對邊
        
        edge1 = self._create_perpendicular_bisector(site1, site2, depth)
        edges.append(edge1)
        edge_map[(site1, site2)] = edge1
        edge_map[(site2, site1)] = edge1
        
        edge2 = self._create_perpendicular_bisector(site2, site3, depth)
        edges.append(edge2)
        edge_map[(site2, site3)] = edge2
        edge_map[(site3, site2)] = edge2
        
        edge3 = self._create_perpendicular_bisector(site1, site3, depth)
        edges.append(edge3)
        edge_map[(site1, site3)] = edge3
        edge_map[(site3, site1)] = edge3
        
        # 步驟1: 顯示未截斷的中垂線（使用快照複製）
        edges_snapshot = [e.copy_snapshot() for e in edges]
        step1 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}直角三角形：創建三條完整中垂線（未截斷）",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot),
            left_edges=edges_snapshot[:1],
            right_edges=edges_snapshot[1:]
        )
        self.vd.merge_steps.append(step1)
        
        # 找出對邊（斜邊）
        opposite_edge = edge_map.get((opposite_p1, opposite_p2))
        
        # 進行截斷
        for edge in edges:
            if edge == opposite_edge:
                # 對邊（斜邊）：使用直角特殊邏輯（與直角頂點異號）
                print(f"{'  '*depth}    處理對邊（斜邊）中垂線（與直角頂點異號）")
                self._truncate_edge_with_circumcenter_right_opposite(edge, center_vertex, right_vertex, depth)
            else:
                # 鄰邊：使用正常邏輯（保留異號）
                self._truncate_edge_with_circumcenter(edge, center_vertex, depth)
        
        # 步驟2: 顯示截斷後的中垂線（使用快照複製，避免後續修改影響）
        edges_snapshot_after = [e.copy_snapshot() for e in edges]
        step2 = MergeStep(
            step_id=len(self.vd.merge_steps),
            description=f"{'  '*depth}直角三角形：用外心截斷中垂線（斜邊與直角頂點異號）",
            left_sites=[site1],
            right_sites=[site2, site3],
            new_edges=set(edges_snapshot_after),
            left_edges=edges_snapshot_after[:1],
            right_edges=edges_snapshot_after[1:]
        )
        self.vd.merge_steps.append(step2)
    
    def _create_perpendicular_bisector(self, site1, site2, depth):
        """創建兩點之間的完整中垂線（延伸到邊界）"""
        edge = self.vd.create_edge(site1, site2)
        
        # 計算中點和方向
        mid_x, mid_y = edge.get_midpoint()
        
        dx = site2.x - site1.x
        dy = site2.y - site1.y
        
        # 垂直方向
        direction_x = -dy
        direction_y = dx
        
        length = math.sqrt(direction_x**2 + direction_y**2)
        if length > 1e-9:
            direction_x /= length
            direction_y /= length
        
        # 延伸到邊界
        x1, y1, x2, y2 = extend_line_to_boundary(mid_x, mid_y, direction_x, direction_y)
        
        # 創建端點
        start_vertex = self.vd.create_vertex(x1, y1, sites=[site1, site2])
        end_vertex = self.vd.create_vertex(x2, y2, sites=[site1, site2])
        
        edge.start = start_vertex
        edge.end = end_vertex
        
        return edge
    
    def export_to_text_file(self, filename="output.txt"):
        """
        將 Voronoi Diagram 結果輸出到文字檔案
        
        格式：
        - P x y：輸入點座標
        - E x1 y1 x2 y2：線段（中垂線和 hyperplane）
        
        排序規則：
        - 點：按 lexical order (x, y)
        - 線段：保證 x1≤x2 或 (x1=x2 且 y1≤y2)，然後按 (x1, y1, x2, y2) lexical order 排序
        """
        # 收集所有輸入點
        points = []
        for site in self.vd.sites:
            points.append((int(round(site.x)), int(round(site.y))))
        
        # 按 lexical order 排序點
        points.sort()
        
        # 收集所有線段（只包含有效的邊，不包含孤立邊）
        segments = []
        for edge in self.vd.edges:
            # 確保邊有兩個端點
            if edge.start is None or edge.end is None:
                continue
            
            # 使用與繪製時相同的裁剪算法
            clipped = clip_line_to_canvas(edge.start.x, edge.start.y, edge.end.x, edge.end.y)
            if clipped:
                x1, y1, x2, y2 = clipped
                # 四捨五入到整數
                x1, y1 = int(round(x1)), int(round(y1))
                x2, y2 = int(round(x2)), int(round(y2))
                
                # 確保 x1≤x2，或 x1=x2 且 y1≤y2
                if x1 > x2 or (x1 == x2 and y1 > y2):
                    x1, y1, x2, y2 = x2, y2, x1, y1
                
                segments.append((x1, y1, x2, y2))
        
        # 移除重複的線段
        segments = list(set(segments))
        
        # 按 lexical order 排序線段
        segments.sort()
        
        # 寫入檔案
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 寫入點
                for x, y in points:
                    f.write(f"P {x} {y}\n")
                
                # 寫入線段
                for x1, y1, x2, y2 in segments:
                    f.write(f"E {x1} {y1} {x2} {y2}\n")
            
            print(f"成功輸出到檔案: {filename}")
            print(f"  輸入點數: {len(points)}")
            print(f"  線段數: {len(segments)}")
            
            messagebox.showinfo("輸出成功", f"已將結果輸出到 {filename}\n\n輸入點數: {len(points)}\n線段數: {len(segments)}")
            
        except Exception as e:
            print(f"輸出檔案時發生錯誤: {e}")
            messagebox.showerror("輸出失敗", f"無法寫入檔案 {filename}\n\n錯誤: {e}")


# 主程式入口
if __name__ == "__main__":
    root = tk.Tk()
    app = VoronoiGUI(root)
    root.mainloop()