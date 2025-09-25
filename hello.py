import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from datastructer import* 


# 主程式部分
class VoronoiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voronoi Diagram")
        self.canvas = tk.Canvas(root, width=600, height=600, bg="white")
        self.canvas.pack()
        self.points = []
        self.groups = []
        self.current_group = 0
        self.vd = VoronoiDiagram()  # 創建單一的 VoronoiDiagram 實例
        
        # 用於調試顯示的變量
        self.debug_left_hull = []
        self.debug_right_hull = []
        self.debug_A = None
        self.debug_B = None
        
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
        
        # 滑鼠點擊事件
        self.canvas.bind("<Button-1>", self.add_point)
    
    def add_point(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")
    
    #主演算法部分
    def run_voronoi(self):
        if not self.points:
            messagebox.showwarning("Warning", "No points to process")
            return
        
        # 清空之前的 Voronoi Diagram
        self.vd.edges.clear()
        self.vd.vertices.clear()
        self.vd.point_to_edges.clear()
        
        # 構建 Voronoi Diagram
        points = [Point(x, y) for x, y in self.points]  # 轉換為 Point 物件
        self.vd = self.build_voronoi(points)
        
        # 繪製結果
        self.draw_voronoi()

    # 建立Voronoi Diagram
    def build_voronoi(self, points):
        vd = VoronoiDiagram()
        vd.points = points  # 設置點集
        for point in points:
            vd.point_to_edges[point] = []  # 為每個點初始化空列表
        
        # 計算總共有多少點
        total_points = len(points)
        
        # 基礎情況：點數量 <= 3
        if total_points <= 3:
            if total_points == 1:
                return vd  # 單點無需處理
            elif total_points == 2:
                return self.build_voronoi_two_points(points)
            elif total_points == 3:
                return self.build_voronoi_three_points(points)
        else:
            # Divide：依照點的X座標排序
            sorted_points = sorted(points, key=lambda p: p.x)
            
            # 依照X座標切為左右數量一樣的兩半
            mid = total_points // 2
            left_points = sorted_points[:mid]      # 左半部分（X座標較小）
            right_points = sorted_points[mid:]     # 右半部分（X座標較大）
            
            # Conquer：遞迴處理左右兩部分
            left_vd = self.build_voronoi(left_points)
            right_vd = self.build_voronoi(right_points)
            
            # Merge：合併左右子問題的結果
            merged_vd = self.merge_voronoi(left_vd, right_vd)
            return merged_vd

    #兩個點的處理
    def build_voronoi_two_points(self, points):
        vd = VoronoiDiagram()
        vd.points = points
        for point in points:
            vd.point_to_edges[point] = []
        p1, p2 = points[0], points[1]
        # 共點則不做任何處理
        if p1.x == p2.x and p1.y == p2.y:
            return vd
        start, end = VoronoiEdge.get_perpendicular_bisector_on_canvas(p1, p2)
        edge = VoronoiEdge(p1, p2)
        edge.set_start_vertex(start)
        edge.set_end_vertex(end)
        vd.add_vertex(start)
        vd.add_vertex(end)
        vd.add_edge(edge)
        return vd

    #三個點的處理
    #處理鈍角和銳角三角形的情況
    def build_voronoi_three_points(self, points):
        vd = VoronoiDiagram()
        vd.points = points
        for point in points:
            vd.point_to_edges[point] = []
        p1, p2, p3 = points[0], points[1], points[2]
        # 判斷三點是否共線
        area = abs((p2.x - p1.x)*(p3.y - p1.y) - (p3.x - p1.x)*(p2.y - p1.y))
        if area == 0:
            # 三點共線，僅求最遠兩點以外的兩條中垂線
            d12 = (p1.x - p2.x)**2 + (p1.y - p2.y)**2
            d23 = (p2.x - p3.x)**2 + (p2.y - p3.y)**2
            d13 = (p1.x - p3.x)**2 + (p1.y - p3.y)**2
            # 找出最遠的兩點
            max_d = max(d12, d23, d13)
            pairs = [(p1, p2), (p2, p3), (p3, p1)]
            for idx, (a, b) in enumerate(pairs):
                d = (a.x - b.x)**2 + (a.y - b.y)**2
                if d != max_d:
                    start, end = VoronoiEdge.get_perpendicular_bisector_on_canvas(a, b)
                    edge = VoronoiEdge(a, b)
                    edge.set_start_vertex(start)
                    edge.set_end_vertex(end)
                    vd.add_vertex(start)
                    vd.add_vertex(end)
                    vd.add_edge(edge)
            return vd
        # 不共線，處理三條中垂線
        vertex = self.calculate_circumcenter(p1, p2, p3)
        
        # 檢查外心是否存在且在顯示範圍內
        circumcenter_valid = (vertex is not None and 
                             0 <= vertex.x <= 600 and 
                             0 <= vertex.y <= 600)
        
        # 計算三邊長，找出最遠的兩點
        def dist2(a, b):
            return (a.x - b.x)**2 + (a.y - b.y)**2
        
        d12 = dist2(p1, p2)
        d23 = dist2(p2, p3) 
        d13 = dist2(p1, p3)
        max_dist = max(d12, d23, d13)
        
        # 找出最遠的兩點
        if max_dist == d12:
            farthest_pair = (p1, p2)
        elif max_dist == d23:
            farthest_pair = (p2, p3)
        else:
            farthest_pair = (p1, p3)
        
        # 如果外心無效，只繪製兩兩接近的點，跳過最遠兩點
        if not circumcenter_valid:
            pairs = [(p1, p2), (p2, p3), (p3, p1)]
            for a, b in pairs:
                # 跳過最遠的兩點
                if (a, b) == farthest_pair or (b, a) == farthest_pair:
                    continue
                    
                start, end = VoronoiEdge.get_perpendicular_bisector_on_canvas(a, b)
                edge = VoronoiEdge(a, b)
                edge.set_start_vertex(start)
                edge.set_end_vertex(end)
                vd.add_vertex(start)
                vd.add_vertex(end)
                vd.add_edge(edge)
        else:
            # 外心有效，進行正常的三角形處理
            # 計算三邊長
            a2 = dist2(p2, p3)
            b2 = dist2(p1, p3)
            c2 = dist2(p1, p2)
            a = a2 ** 0.5
            b = b2 ** 0.5
            c = c2 ** 0.5

            # 計算三角形三個角的 cos 值
            # 角A在p1，角B在p2，角C在p3
            cosA = (b2 + c2 - a2) / (2 * b * c)
            cosB = (a2 + c2 - b2) / (2 * a * c)
            cosC = (a2 + b2 - c2) / (2 * a * b)

            if cosA < 0 or cosB < 0 or cosC < 0:
                # 情況1：鈍角三角形
                # 判斷哪個點為鈍角頂點
                if cosA < 0:
                    obtuse_point = p1
                elif cosB < 0:
                    obtuse_point = p2
                else:
                    obtuse_point = p3
                
                # 針對鈍角三角形做特殊處理
                vd.add_vertex(vertex)
                pairs = [(p1, p2), (p2, p3), (p3, p1)]
                points_list = [p1, p2, p3]
                for idx, (a, b) in enumerate(pairs):
                    start, end = VoronoiEdge.get_perpendicular_bisector_on_canvas(a, b)
                    third = points_list[(idx + 2) % 3]
                    # 計算單位向量
                    def unit_vector(p_from, p_to):
                        dx = p_to.x - p_from.x
                        dy = p_to.y - p_from.y
                        length = (dx**2 + dy**2) ** 0.5
                        if length == 0:
                            return 0, 0
                        return dx / length, dy / length
                    ux_s, uy_s = unit_vector(vertex, start)
                    VtoS = VoronoiVertex(vertex.x + ux_s, vertex.y + uy_s)
                    ux_e, uy_e = unit_vector(vertex, end)
                    VtoE = VoronoiVertex(vertex.x + ux_e, vertex.y + uy_e)
                    mx = (a.x + b.x) / 2
                    my = (a.y + b.y) / 2
                    dist_VtoS_m = (VtoS.x - mx)**2 +(VtoS.y - my)**2
                    dist_VtoE_m = (VtoE.x - mx)**2 + (VtoE.y - my)**2

                    #鈍角對面的中垂線需反向
                    if obtuse_point not in (a, b):
                        if dist_VtoS_m < dist_VtoE_m:
                            start, end = VtoS, end
                        else:
                            start, end = VtoE, start
                    #其餘兩條保持不變
                    else:
                        if dist_VtoS_m > dist_VtoE_m:
                            start, end = VtoS, end
                        else:
                            start, end = VtoE, start
                    edge = VoronoiEdge(a, b)
                    edge.set_start_vertex(start)
                    edge.set_end_vertex(end)
                    vd.add_vertex(start)
                    vd.add_vertex(end)
                    vd.add_edge(edge)
            else:
                # 情況2：銳角三角形，原本邏輯不變
                vd.add_vertex(vertex)
                for idx, (a, b) in enumerate([(p1, p2), (p2, p3), (p3, p1)]):
                    start, end = VoronoiEdge.get_perpendicular_bisector_on_canvas(a, b)
                    third = [p1, p2, p3][(idx + 2) % 3]
                    # 計算單位向量
                    def unit_vector(p_from, p_to):
                        dx = p_to.x - p_from.x
                        dy = p_to.y - p_from.y
                        length = (dx**2 + dy**2) ** 0.5
                        if length == 0:
                            return 0, 0
                        return dx / length, dy / length
                    ux_s, uy_s = unit_vector(vertex, start)
                    VtoS = VoronoiVertex(vertex.x + ux_s, vertex.y + uy_s)
                    ux_e, uy_e = unit_vector(vertex, end)
                    VtoE = VoronoiVertex(vertex.x + ux_e, vertex.y + uy_e)
                    dist_VtoS_third = (VtoS.x - third.x)**2 + (VtoS.y - third.y)**2
                    dist_VtoE_third = (VtoE.x - third.x)**2 + (VtoE.y - third.y)**2
                    if dist_VtoS_third < dist_VtoE_third:
                        new_start = vertex
                        new_end = end
                    else:
                        new_start = vertex
                        new_end = start
                    edge = VoronoiEdge(a, b)
                    edge.set_start_vertex(new_start)
                    edge.set_end_vertex(new_end)
                    vd.add_vertex(new_start)
                    vd.add_vertex(new_end)
                    vd.add_edge(edge)
        return vd
    

    # 判斷點c是否在a和b之間（線段內部）
    def is_between(a, b, c):
        
        cross = (c.x - a.x) * (b.x - a.x) + (c.y - a.y) * (b.y - a.y)
        if cross < 0:
            return False
        dist_ab = (b.x - a.x)**2 + (b.y - a.y)**2
        dist_ac = (c.x - a.x)**2 + (c.y - a.y)**2
        return dist_ac <= dist_ab
    

    # 計算三點的外心（中垂線交點）
    def calculate_circumcenter(self, p1, p2, p3):
        
        # 使用兩條中垂線的交點公式
        ax, ay = p1.x, p1.y
        bx, by = p2.x, p2.y
        cx, cy = p3.x, p3.y
        
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:  # 三點共線
            return None
        
        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
        
        return VoronoiVertex(ux, uy) 
    

    #合併左右子問題
    def merge_voronoi(self, left_vd, right_vd):
        merged_vd = VoronoiDiagram()
        
        # 合併點集
        merged_vd.points = left_vd.points + right_vd.points
        for point in merged_vd.points:
            merged_vd.point_to_edges[point] = []
        
        # 如果其中一個子問題為空，直接返回另一個
        if not left_vd.points:
            return right_vd
        if not right_vd.points:
            return left_vd
        
        # 計算左右分界線
        left_max_x = max(p.x for p in left_vd.points)
        right_min_x = min(p.x for p in right_vd.points)
        separator_x = (left_max_x + right_min_x) / 2
        
        # 1. A B分別為左右半邊最接近分隔線的兩點
        A = min(left_vd.points, key=lambda p: abs(p.x - separator_x))   # 左側最接近分隔線的點
        B = min(right_vd.points, key=lambda p: abs(p.x - separator_x))  # 右側最接近分隔線的點
        
        print(f"初始 A: ({A.x}, {A.y}), B: ({B.x}, {B.y})")
        
        # 獲取左右兩側的凸包（修正順序）
        left_hull = self.get_convex_hull_ordered(left_vd.points, False, A)  # 左側順時針，從A開始
        right_hull = self.get_convex_hull_ordered(right_vd.points, True, B)  # 右側逆時針，從B開始
        
        # 保存調試信息
        self.debug_left_hull = left_hull[:]
        self.debug_right_hull = right_hull[:]
        
        print(f"左側凸包 (順時針，從A開始):")
        for i, p in enumerate(left_hull):
            marker = " ← A" if p == A else ""
            print(f"  L{i}: ({p.x}, {p.y}){marker}")
        
        print(f"右側凸包 (逆時針，從B開始):")
        for i, p in enumerate(right_hull):
            marker = " ← B" if p == B else ""
            print(f"  R{i}: ({p.x}, {p.y}){marker}")
        
        # 2. 使用更精確的上切線搜索算法
        max_iterations = 20  # 防止無限循環
        for iteration in range(max_iterations):
            print(f"\n迭代 {iteration + 1}:")
            
            old_A, old_B = A, B
            improved = False
            
            # 左半區A點：沿逆時針移動來找到更高的上切線
            A_index = left_hull.index(A)
            next_A = left_hull[(A_index + 1) % len(left_hull)]  # 在順時針排列的凸包上逆時針移動（索引+1）
            
            # 使用向量旋轉方向判斷是否應該移動A
            if self.should_move_A(A, next_A, B):
                A = next_A
                improved = True
                print(f"A 逆時針移動到: ({A.x}, {A.y})")
            else:
                print(f"A 維持不變: ({A.x}, {A.y})")
            
            # 右半區B點：沿順時針移動來找到更高的上切線
            B_index = right_hull.index(B)
            next_B = right_hull[(B_index + 1) % len(right_hull)]  # 在逆時針排列的凸包上順時針移動（索引+1）
            
            # 使用向量旋轉方向判斷是否應該移動B
            if self.should_move_B(A, B, next_B):
                B = next_B
                improved = True
                print(f"B 順時針移動到: ({B.x}, {B.y})")
            else:
                print(f"B 維持不變: ({B.x}, {B.y})")
            
            # 檢查是否收斂（AB都不動）
            if not improved:
                print(f"\n收斂！最終 A: ({A.x}, {A.y}), B: ({B.x}, {B.y})")
                break
        
        # 保存最終的A和B用於調試顯示
        self.debug_A = A
        self.debug_B = B
        
        # 使用最終的A和B創建中垂線
        midAB_start, midAB_end = VoronoiEdge.get_perpendicular_bisector_on_canvas(A, B)
        
        # 按照Y值排序：Y小的設為起始點，Y大的設為結束點
        if midAB_start.y > midAB_end.y:
            midAB_start, midAB_end = midAB_end, midAB_start
            
        print(f"midAB 碰到圖形邊緣: 起始點(Y={midAB_start.y:.2f}): ({midAB_start.x:.2f}, {midAB_start.y:.2f})")
        print(f"                    結束點(Y={midAB_end.y:.2f}): ({midAB_end.x:.2f}, {midAB_end.y:.2f})")
        
        midAB = VoronoiEdge(A, B)
        midAB.set_start_vertex(midAB_start)
        midAB.set_end_vertex(midAB_end)
        
        # 檢查 midAB 與現有邊的第一個交點（從起始點開始）
        all_existing_edges = left_vd.edges + right_vd.edges
        first_collision = None
        closest_distance = float('inf')
        
        for existing_edge in all_existing_edges:
            intersection_point = midAB.find_intersection(existing_edge)
            if intersection_point:
                # 檢查交點是否在現有邊的線段範圍內
                if existing_edge.is_point_between_vertices(intersection_point):
                    # 計算從起始點到交點的距離
                    distance = ((intersection_point.x - midAB_start.x)**2 + 
                              (intersection_point.y - midAB_start.y)**2) ** 0.5
                    
                    # 找到最接近起始點的交點
                    if distance < closest_distance:
                        closest_distance = distance
                        bisected_points = existing_edge.get_bisected_points()
                        first_collision = {
                            'point': intersection_point,
                            'intersected_edge': existing_edge,
                            'bisected_points': bisected_points
                        }
        
        # 處理碰撞的迭代流程
        current_A = A
        current_B = B
        
        # 獲取初始的midAB邊緣交點，按Y值排序
        midAB_start, midAB_end = VoronoiEdge.get_perpendicular_bisector_on_canvas(current_A, current_B)
        if midAB_start.y > midAB_end.y:
            midAB_start, midAB_end = midAB_end, midAB_start
        
        current_cross = midAB_start  # 第一次從邊緣起始點開始
        
        max_iterations = 20  # 防止無限循環
        for iteration in range(max_iterations):
            print(f"\n=== midAB 迭代 {iteration + 1} ===")
            print(f"當前 A: ({current_A.x}, {current_A.y}), B: ({current_B.x}, {current_B.y})")
            print(f"起始點: ({current_cross.x:.2f}, {current_cross.y:.2f})")
            
            # 創建從current_cross開始的midAB
            if iteration == 0:
                current_midAB_start = midAB_start
                current_midAB_end = midAB_end
            else:
                # 從current_cross開始，使用上次計算的midAB_end方向
                current_midAB_start = current_cross
                current_midAB_end = midAB_end  # 使用前面計算好的正確方向端點
            
            # 確保midAB段是往Y較大方向：結束點Y > 起始點Y
            if current_midAB_end.y < current_midAB_start.y:
                print(f"midAB方向錯誤，需要反向：起始點Y({current_midAB_start.y:.2f}) > 結束點Y({current_midAB_end.y:.2f})")
                current_midAB_start, current_midAB_end = current_midAB_end, current_midAB_start
                print(f"已反向：起始點Y({current_midAB_start.y:.2f}) -> 結束點Y({current_midAB_end.y:.2f})")
            
            print(f"midAB 線段: 從 ({current_midAB_start.x:.2f}, {current_midAB_start.y:.2f}) 到 ({current_midAB_end.x:.2f}, {current_midAB_end.y:.2f})")
            print(f"  起始點Y: {current_midAB_start.y:.2f}, 結束點Y: {current_midAB_end.y:.2f} (結束點Y較大: {current_midAB_end.y > current_midAB_start.y})")
            
            # 創建當前的midAB線段
            current_midAB = VoronoiEdge(current_A, current_B)
            current_midAB.set_start_vertex(current_midAB_start)
            current_midAB.set_end_vertex(current_midAB_end)
            
            # 尋找第一個碰撞點
            collision = None
            closest_distance = float('inf')
            
            for existing_edge in all_existing_edges:
                intersection_point = current_midAB.find_intersection(existing_edge)
                if intersection_point:
                    if existing_edge.is_point_between_vertices(intersection_point):
                        distance = ((intersection_point.x - current_midAB_start.x)**2 + 
                                  (intersection_point.y - current_midAB_start.y)**2) ** 0.5
                        
                        if distance < closest_distance and distance > 1e-6:
                            closest_distance = distance
                            collision = {
                                'point': intersection_point,
                                'intersected_edge': existing_edge,
                                'bisected_points': existing_edge.get_bisected_points()
                            }
            
            # 處理碰撞
            if collision:
                new_cross = collision['point']
                intersected_edge = collision['intersected_edge']
                site1, site2 = collision['bisected_points']
                
                print(f"碰撞點: ({new_cross.x:.2f}, {new_cross.y:.2f})")
                print(f"被碰撞線段由點 ({site1.x}, {site1.y}) 和 ({site2.x}, {site2.y}) 產生")
                
                # 確保當前midAB段是往Y較大方向：從起始點到碰撞點
                # 檢查方向是否正確
                if current_midAB.start_vertex.y <= new_cross.y:
                    # 方向正確：起始點Y <= 碰撞點Y，保留起始點到碰撞點的部分
                    current_midAB.set_end_vertex(VoronoiVertex(new_cross.x, new_cross.y))
                    print(f"midAB段方向正確：從 ({current_midAB.start_vertex.x:.2f}, {current_midAB.start_vertex.y:.2f}) 到碰撞點 ({new_cross.x:.2f}, {new_cross.y:.2f})")
                else:
                    # 方向錯誤：起始點Y > 碰撞點Y，需要反向，從碰撞點到起始點
                    original_start = current_midAB.start_vertex
                    current_midAB.set_start_vertex(VoronoiVertex(new_cross.x, new_cross.y))
                    current_midAB.set_end_vertex(original_start)
                    print(f"midAB段方向修正：從碰撞點 ({new_cross.x:.2f}, {new_cross.y:.2f}) 到 ({original_start.x:.2f}, {original_start.y:.2f})")
                
                merged_vd.edges.append(current_midAB)
                
                # 處理被碰撞的邊
                self.truncate_intersected_edge(intersected_edge, new_cross, left_vd.points + right_vd.points, left_vd.points, right_vd.points)
                
                # 更新AB
                updated = False
                if current_A == site1 or current_A == site2:
                    current_A = site2 if current_A == site1 else site1
                    print(f"A 移動到: ({current_A.x}, {current_A.y})")
                    updated = True
                elif current_B == site1 or current_B == site2:
                    current_B = site2 if current_B == site1 else site1
                    print(f"B 移動到: ({current_B.x}, {current_B.y})")
                    updated = True
                
                if not updated:
                    print("A和B都不在被碰撞線段中，結束迭代")
                    break
                
                # 重新計算midAB邊緣交點（因為AB改變了）
                new_midAB_start, new_midAB_end = VoronoiEdge.get_perpendicular_bisector_on_canvas(current_A, current_B)
                # 確保Y小的為起始點，Y大的為結束點
                if new_midAB_start.y > new_midAB_end.y:
                    new_midAB_start, new_midAB_end = new_midAB_end, new_midAB_start
                
                print(f"重新計算的midAB邊緣交點: 起始Y={new_midAB_start.y:.2f}, 結束Y={new_midAB_end.y:.2f}")
                
                # 決定從碰撞點出發的正確方向
                # 計算從碰撞點到兩個端點的方向向量
                to_start_y = new_midAB_start.y - new_cross.y  # 到起始點的Y方向
                to_end_y = new_midAB_end.y - new_cross.y      # 到結束點的Y方向
                
                # 選擇往Y較大方向的端點作為目標
                if to_end_y > to_start_y:
                    # 朝向end方向（Y較大）
                    midAB_end = new_midAB_end
                    print(f"從碰撞點朝向Y較大的端點: ({new_midAB_end.x:.2f}, {new_midAB_end.y:.2f})")
                else:
                    # 朝向start方向（Y較大）
                    midAB_end = new_midAB_start
                    print(f"從碰撞點朝向Y較大的端點: ({new_midAB_start.x:.2f}, {new_midAB_start.y:.2f})")
                
                # 設置下一次起始點
                current_cross = VoronoiVertex(new_cross.x, new_cross.y)
                
            else:
                # 沒有碰撞，延伸midAB到Y較大的方向（往下）
                print("無碰撞，延伸midAB到Y較大方向")
                
                # 重新計算完整的midAB，確保方向正確
                temp_start, temp_end = VoronoiEdge.get_perpendicular_bisector_on_canvas(current_A, current_B)
                
                # 確保從current_cross出發，朝向Y較大的方向
                # 計算從current_cross到兩個端點的距離和方向
                to_temp_start_y = temp_start.y - current_cross.y
                to_temp_end_y = temp_end.y - current_cross.y
                
                # 選擇Y方向更大的端點作為目標方向
                if to_temp_end_y > to_temp_start_y:
                    target_end = temp_end
                    print(f"選擇端點: ({temp_end.x:.2f}, {temp_end.y:.2f}), Y方向: {to_temp_end_y:.2f}")
                else:
                    target_end = temp_start  
                    print(f"選擇端點: ({temp_start.x:.2f}, {temp_start.y:.2f}), Y方向: {to_temp_start_y:.2f}")
                
                # 如果目標端點的Y值仍然小於或等於起始點，需要延伸
                if target_end.y <= current_cross.y:
                    # 計算方向向量並延伸
                    direction_x = target_end.x - current_cross.x
                    direction_y = target_end.y - current_cross.y
                    
                    # 延伸到確保Y值更大
                    extend_factor = 2.0  # 延伸倍數
                    extended_end_x = current_cross.x + direction_x * extend_factor
                    extended_end_y = current_cross.y + abs(direction_y) * extend_factor  # 確保Y增加
                    
                    # 如果延伸到畫布外，限制在畫布內
                    if extended_end_y > 600:
                        factor = (600 - current_cross.y) / abs(direction_y * extend_factor)
                        extended_end_x = current_cross.x + direction_x * extend_factor * factor
                        extended_end_y = 600
                else:
                    extended_end_x = target_end.x
                    extended_end_y = target_end.y
                
                # 最終檢查：確保結束點Y值 > 開始點Y值
                if extended_end_y <= current_cross.y:
                    print(f"警告：結束點Y值({extended_end_y:.2f}) <= 開始點Y值({current_cross.y:.2f})，強制修正")
                    extended_end_y = current_cross.y + 50  # 至少增加50像素
                
                # 創建最終的midAB線段：保留cross往Y較大的部分，截掉往Y較小的部分
                final_midAB = VoronoiEdge(current_A, current_B)
                # cross作為起始點，延伸到Y較大的端點
                final_midAB.set_start_vertex(current_cross)
                final_midAB.set_end_vertex(VoronoiVertex(extended_end_x, extended_end_y))
                merged_vd.edges.append(final_midAB)
                
                print(f"最終midAB：保留cross往Y較大部分")
                print(f"  從cross ({current_cross.x:.2f}, {current_cross.y:.2f}) 到 ({extended_end_x:.2f}, {extended_end_y:.2f})")
                print(f"  Y方向檢查: 結束點Y({extended_end_y:.2f}) > 開始點Y({current_cross.y:.2f}) = {extended_end_y > current_cross.y}")
                print(f"  截掉了cross往Y較小的部分")
                break
        
        # 更新調試顯示的A和B
        self.debug_A = current_A
        self.debug_B = current_B
        
        

        # 合併結果
        merged_vd.edges.extend(left_vd.edges)
        merged_vd.edges.extend(right_vd.edges)
        # midAB 已經在上面的處理中加入，不需要重複添加
        
        merged_vd.vertices.extend(left_vd.vertices)
        merged_vd.vertices.extend(right_vd.vertices)
        # midAB 的端點也已經在上面處理中加入
        
        return merged_vd
    
    def get_convex_hull_ordered(self, points, counterclockwise=True, start_point=None):
        """獲取有序的凸包點，可指定起始點"""
        if len(points) < 3:
            return points
        
        # 使用 Graham scan 算法
        def cross_product(o, a, b):
            return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
        
        # 找到最下方的點（y最小，x最小）
        pivot = min(points, key=lambda p: (p.y, p.x))
        
        # 按極角排序
        import math
        def polar_angle(p):
            dx = p.x - pivot.x
            dy = p.y - pivot.y
            return math.atan2(dy, dx)
        
        sorted_points = sorted([p for p in points if p != pivot], key=polar_angle)
        hull = [pivot]
        
        for point in sorted_points:
            while len(hull) > 1 and cross_product(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)
        
        # 根據需要的順序調整
        if not counterclockwise:
            hull.reverse()
        
        # 如果指定了起始點，重新排列凸包使其從起始點開始
        if start_point and start_point in hull:
            start_index = hull.index(start_point)
            hull = hull[start_index:] + hull[:start_index]
        
        return hull
    
    def calculate_slope(self, p1, p2):
        """計算兩點連線的斜率"""
        if p2.x == p1.x:
            return float('inf')  # 垂直線
        return (p2.y - p1.y) / (p2.x - p1.x)
    
    def is_clockwise_rotation(self, old_slope, new_slope):
        """檢查是否為順時針旋轉（斜率增加）"""
        if old_slope == float('inf') and new_slope != float('inf'):
            return new_slope > 0
        if new_slope == float('inf') and old_slope != float('inf'):
            return old_slope < 0
        if old_slope == float('inf') and new_slope == float('inf'):
            return False
        return new_slope > old_slope
    
    def is_counterclockwise_rotation(self, old_slope, new_slope):
        """檢查是否為逆時針旋轉（斜率減少）"""
        if old_slope == float('inf') and new_slope != float('inf'):
            return new_slope < 0
        if new_slope == float('inf') and old_slope != float('inf'):
            return old_slope > 0
        if old_slope == float('inf') and new_slope == float('inf'):
            return False
        return new_slope < old_slope
    
    def is_valid_upper_tangent(self, left_point, right_point, hull_to_check):
        """
        檢查left_point到right_point的直線是否為有效的上切線
        使用向量旋轉方向來判斷，而不是叉積
        """
        # 這個函數現在不再使用，保留為備用
        return True
    
    def should_move_A(self, current_A, next_A, B):
        """
        判斷是否應該將A從current_A移動到next_A
        如果 BA × NEW_BA >= 0 則接受新的A
        """
        # 計算向量 BA (B -> current_A)
        BA = (current_A.x - B.x, current_A.y - B.y)
        # 計算向量 NEW_BA (B -> next_A)
        NEW_BA = (next_A.x - B.x, next_A.y - B.y)
        
        # 計算外積 BA × NEW_BA
        cross_product = BA[0] * NEW_BA[1] - BA[1] * NEW_BA[0]
        
        print(f"A移動判斷: BA向量({B.x},{B.y})->({current_A.x},{current_A.y}) = {BA}")
        print(f"          NEW_BA向量({B.x},{B.y})->({next_A.x},{next_A.y}) = {NEW_BA}")
        print(f"          外積 BA × NEW_BA = {cross_product}")
        
        if cross_product >= 0:
            print("外積 >= 0，接受新的A")
            return True
        else:
            print("外積 < 0，維持舊的A")
            return False
    
    def should_move_B(self, A, current_B, next_B):
        """
        判斷是否應該將B從current_B移動到next_B
        如果 NEW_AB × AB >= 0 則接受新的B
        """
        # 計算向量 AB (A -> current_B)
        AB = (current_B.x - A.x, current_B.y - A.y)
        # 計算向量 NEW_AB (A -> next_B)
        NEW_AB = (next_B.x - A.x, next_B.y - A.y)
        
        # 計算外積 NEW_AB × AB
        cross_product = NEW_AB[0] * AB[1] - NEW_AB[1] * AB[0]
        
        print(f"B移動判斷: AB向量({A.x},{A.y})->({current_B.x},{current_B.y}) = {AB}")
        print(f"          NEW_AB向量({A.x},{A.y})->({next_B.x},{next_B.y}) = {NEW_AB}")
        print(f"          外積 NEW_AB × AB = {cross_product}")
        
        if cross_product >= 0:
            print("外積 >= 0，接受新的B")
            return True
        else:
            print("外積 < 0，維持舊的B")
            return False
    
    def is_tangent_improving_left(self, current_A, next_A, B, right_hull):
        """
        檢查左側點從current_A移到next_A是否改善上切線
        對於上切線，右側凸包的所有其他點都應該在切線的下方或右側
        """
        # 檢查right_hull中的點是否都在next_A-B線段的下方
        for point in right_hull:
            if point == B:
                continue
                
            # 計算叉積：向量(next_A -> B) × 向量(next_A -> point)
            # 如果結果 < 0，表示point在next_A-B線段的下方（右側），這是我們要的
            # 如果結果 > 0，表示point在next_A-B線段的上方（左側），不符合上切線要求
            cross = self.cross_product(next_A, B, point)
            
            # 對於上切線，所有右側凸包的點都應該在切線下方
            if cross > 0:  # 點在線段上方，不是有效的上切線
                return False
                
        return True
    
    def is_tangent_improving_right(self, A, current_B, next_B, left_hull):
        """
        檢查右側點從current_B移到next_B是否改善上切線
        對於上切線，左側凸包的所有其他點都應該在切線的下方或左側
        """
        # 檢查left_hull中的點是否都在A-next_B線段的下方
        for point in left_hull:
            if point == A:
                continue
                
            # 計算叉積：向量(A -> next_B) × 向量(A -> point)  
            # 如果結果 > 0，表示point在A-next_B線段的下方（左側），這是我們要的
            # 如果結果 < 0，表示point在A-next_B線段的上方（右側），不符合上切線要求
            cross = self.cross_product(A, next_B, point)
            
            # 對於上切線，所有左側凸包的點都應該在切線下方
            if cross < 0:  # 點在線段上方，不是有效的上切線
                return False
                
        return True
    
    def cross_product(self, p1, p2, p3):
        """計算向量(p1->p2) × (p1->p3)的叉積"""
        return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
    
    def truncate_intersected_edge(self, intersected_edge, cross_point, all_points, left_points=None, right_points=None):
        """截斷被碰撞的邊，根據是否為鈍角三角形採用不同邏輯"""
        bisected_points = intersected_edge.get_bisected_points()
        edge_site1, edge_site2 = bisected_points
        
        # 找到與這條邊相關的第三個點來計算外心
        circumcenter = None
        third_point = None
        
        for point in all_points:
            if point != edge_site1 and point != edge_site2:
                # 嘗試計算三點的外心
                potential_circumcenter = self.calculate_circumcenter(edge_site1, edge_site2, point)
                if potential_circumcenter:
                    # 檢查這個外心是否就是被碰撞邊的起點或終點
                    start_dist = ((potential_circumcenter.x - intersected_edge.start_vertex.x)**2 + 
                                (potential_circumcenter.y - intersected_edge.start_vertex.y)**2) ** 0.5
                    end_dist = ((potential_circumcenter.x - intersected_edge.end_vertex.x)**2 + 
                              (potential_circumcenter.y - intersected_edge.end_vertex.y)**2) ** 0.5
                    
                    # 如果外心接近其中一個端點（容差5像素），則找到正確的外心
                    if start_dist < 5 or end_dist < 5:
                        circumcenter = potential_circumcenter
                        third_point = point
                        break
        
        if circumcenter and third_point:
            print(f"找到外心: ({circumcenter.x:.2f}, {circumcenter.y:.2f})，第三點: ({third_point.x}, {third_point.y})")
            
            # 判斷是否為鈍角三角形
            is_obtuse = self.is_obtuse_triangle(edge_site1, edge_site2, third_point)
            obtuse_vertex = None
            
            if is_obtuse:
                obtuse_vertex = self.get_obtuse_vertex(edge_site1, edge_site2, third_point)
                print(f"發現鈍角三角形，鈍角頂點: ({obtuse_vertex.x}, {obtuse_vertex.y})")
                
                # 檢查被碰撞的邊是否包含鈍角頂點
                contains_obtuse_vertex = (obtuse_vertex == edge_site1 or obtuse_vertex == edge_site2)
                
                if contains_obtuse_vertex:
                    print(f"被碰撞邊包含鈍角頂點({obtuse_vertex.x}, {obtuse_vertex.y})，根據左右半邊決定保留方向")
                    
                    # 判斷被碰撞邊屬於左半邊還是右半邊
                    is_left_edge = False
                    if left_points and right_points:
                        # 檢查被碰撞邊的兩個點是否都在左半邊
                        if edge_site1 in left_points and edge_site2 in left_points:
                            is_left_edge = True
                            print("被碰撞邊屬於左半邊圖形")
                        elif edge_site1 in right_points and edge_site2 in right_points:
                            is_left_edge = False
                            print("被碰撞邊屬於右半邊圖形")
                        else:
                            print("被碰撞邊跨越左右半邊，使用默認邏輯")
                    
                    # 根據左右半邊決定保留方向
                    start_x = intersected_edge.start_vertex.x
                    end_x = intersected_edge.end_vertex.x
                    
                    if is_left_edge:
                        # 左半邊：保留cross到X較小的那邊
                        if start_x < end_x:
                            # start端X較小，保留cross到start
                            intersected_edge.set_end_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                            print(f"左半邊：保留cross到X較小端 ({start_x:.2f}, start)")
                        else:
                            # end端X較小，保留cross到end
                            intersected_edge.set_start_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                            print(f"左半邊：保留cross到X較小端 ({end_x:.2f}, end)")
                    else:
                        # 右半邊：保留cross到X較大的那邊
                        if start_x > end_x:
                            # start端X較大，保留cross到start
                            intersected_edge.set_end_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                            print(f"右半邊：保留cross到X較大端 ({start_x:.2f}, start)")
                        else:
                            # end端X較大，保留cross到end
                            intersected_edge.set_start_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                            print(f"右半邊：保留cross到X較大端 ({end_x:.2f}, end)")
                    
                    return
                else:
                    print("被碰撞邊是鈍角對面的邊，保留cross到其他線的交點（使用正常邏輯）")
            
            # 正常情況（銳角三角形或鈍角三角形的非對面邊）：保留外心到cross的部分
            print("使用正常邏輯：保留外心到cross的部分")
            circumcenter_to_start_dist = ((circumcenter.x - intersected_edge.start_vertex.x)**2 + 
                                        (circumcenter.y - intersected_edge.start_vertex.y)**2) ** 0.5
            circumcenter_to_end_dist = ((circumcenter.x - intersected_edge.end_vertex.x)**2 + 
                                      (circumcenter.y - intersected_edge.end_vertex.y)**2) ** 0.5
            
            # 找到距離外心較近的端點，該端點就是外心的位置
            if circumcenter_to_start_dist < circumcenter_to_end_dist:
                # 外心在 start 端，保留從外心（start）到 cross
                intersected_edge.set_end_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                print(f"被碰撞邊截斷：保留從外心到 cross ({cross_point.x:.2f}, {cross_point.y:.2f})")
            else:
                # 外心在 end 端，保留從外心（end）到 cross
                intersected_edge.set_start_vertex(VoronoiVertex(cross_point.x, cross_point.y))
                print(f"被碰撞邊截斷：保留從外心到 cross ({cross_point.x:.2f}, {cross_point.y:.2f})")
        else:
            print("警告：找不到外心，跳過被碰撞邊的截斷")
    
    def is_obtuse_triangle(self, p1, p2, p3):
        """判斷三角形是否為鈍角三角形"""
        # 計算三邊長的平方
        a2 = (p2.x - p3.x)**2 + (p2.y - p3.y)**2  # p1 對面的邊
        b2 = (p1.x - p3.x)**2 + (p1.y - p3.y)**2  # p2 對面的邊  
        c2 = (p1.x - p2.x)**2 + (p1.y - p2.y)**2  # p3 對面的邊
        
        # 計算三角形三個角的餘弦值
        # 角A在p1，角B在p2，角C在p3
        cosA = (b2 + c2 - a2) / (2 * (b2 * c2) ** 0.5)
        cosB = (a2 + c2 - b2) / (2 * (a2 * c2) ** 0.5)  
        cosC = (a2 + b2 - c2) / (2 * (a2 * b2) ** 0.5)
        
        # 如果任何一個餘弦值小於0，則對應角為鈍角
        return cosA < 0 or cosB < 0 or cosC < 0
    
    def get_obtuse_vertex(self, p1, p2, p3):
        """找出鈍角三角形的鈍角頂點"""
        # 計算三邊長的平方
        a2 = (p2.x - p3.x)**2 + (p2.y - p3.y)**2  # p1 對面的邊
        b2 = (p1.x - p3.x)**2 + (p1.y - p3.y)**2  # p2 對面的邊  
        c2 = (p1.x - p2.x)**2 + (p1.y - p2.y)**2  # p3 對面的邊
        
        # 計算三角形三個角的餘弦值
        cosA = (b2 + c2 - a2) / (2 * (b2 * c2) ** 0.5)
        cosB = (a2 + c2 - b2) / (2 * (a2 * c2) ** 0.5)  
        cosC = (a2 + b2 - c2) / (2 * (a2 * b2) ** 0.5)
        
        # 返回餘弦值小於0的頂點（鈍角頂點）
        if cosA < 0:
            return p1
        elif cosB < 0:
            return p2
        elif cosC < 0:
            return p3
        else:
            return None  # 不是鈍角三角形
    
    def truncate_obtuse_opposite_edge(self, intersected_edge, cross_point, circumcenter):
        """截斷鈍角對面的邊：消除外心到cross的部分，保留cross到另一端的部分"""
        circumcenter_to_start_dist = ((circumcenter.x - intersected_edge.start_vertex.x)**2 + 
                                    (circumcenter.y - intersected_edge.start_vertex.y)**2) ** 0.5
        circumcenter_to_end_dist = ((circumcenter.x - intersected_edge.end_vertex.x)**2 + 
                                  (circumcenter.y - intersected_edge.end_vertex.y)**2) ** 0.5
        
        # 找到距離外心較近的端點，該端點就是外心的位置
        if circumcenter_to_start_dist < circumcenter_to_end_dist:
            # 外心在 start 端，消除從外心（start）到 cross，保留 cross 到 end
            intersected_edge.set_start_vertex(VoronoiVertex(cross_point.x, cross_point.y))
            print(f"鈍角對面邊截斷：消除外心到cross，保留cross到另一端 ({intersected_edge.end_vertex.x:.2f}, {intersected_edge.end_vertex.y:.2f})")
        else:
            # 外心在 end 端，消除從外心（end）到 cross，保留 start 到 cross
            intersected_edge.set_end_vertex(VoronoiVertex(cross_point.x, cross_point.y))
            print(f"鈍角對面邊截斷：消除外心到cross，保留另一端到cross ({intersected_edge.start_vertex.x:.2f}, {intersected_edge.start_vertex.y:.2f})")
    
    
    def cross_product(self, p1, p2, p3):
        """計算向量(p1->p2) × (p1->p3)的叉積"""
        return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
    
    #繪製部分
    def draw_voronoi(self):
        self.canvas.delete("all")  # 清空畫布
        self.canvas.configure(bg="white")
        
        # 繪製點
        for x, y in self.points:
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")
        
        # 繪製頂點
        for vertex in self.vd.vertices:
            self.canvas.create_oval(vertex.x-3, vertex.y-3, vertex.x+3, vertex.y+3, fill="red")
        
        # 繪製邊
        for edge in self.vd.edges:
            if edge.is_infinite:
                # 對於無限邊，計算與畫布邊界的交點（簡化處理）
                if edge.start_vertex:
                    x1, y1 = edge.start_vertex.x, edge.start_vertex.y
                    # 假設沿著中垂線方向延伸到邊界，這裡需要根據 site1 和 site2 計算方向
                    self.canvas.create_line(x1, y1, x1, 0, fill="blue")  # 示例，實際需計算
            elif edge.start_vertex and edge.end_vertex:
                self.canvas.create_line(edge.start_vertex.x, edge.start_vertex.y,
                                    edge.end_vertex.x, edge.end_vertex.y, fill="blue")
        
        # 繪製調試信息：左側凸包（順時針，紅色）
        if self.debug_left_hull:
            for i, point in enumerate(self.debug_left_hull):
                # 繪製凸包點（紅色圓圈）
                self.canvas.create_oval(point.x-5, point.y-5, point.x+5, point.y+5, 
                                      outline="red", width=2, fill="")
                # 標記順序號
                self.canvas.create_text(point.x+10, point.y-10, text=f"L{i}", fill="red", font=("Arial", 8))
                # 繪製凸包邊
                next_point = self.debug_left_hull[(i+1) % len(self.debug_left_hull)]
                self.canvas.create_line(point.x, point.y, next_point.x, next_point.y, 
                                      fill="red", width=2, dash=(5, 5))
        
        # 繪製調試信息：右側凸包（逆時針，綠色）
        if self.debug_right_hull:
            for i, point in enumerate(self.debug_right_hull):
                # 繪製凸包點（綠色圓圈）
                self.canvas.create_oval(point.x-5, point.y-5, point.x+5, point.y+5, 
                                      outline="green", width=2, fill="")
                # 標記順序號
                self.canvas.create_text(point.x+10, point.y+10, text=f"R{i}", fill="green", font=("Arial", 8))
                # 繪製凸包邊
                next_point = self.debug_right_hull[(i+1) % len(self.debug_right_hull)]
                self.canvas.create_line(point.x, point.y, next_point.x, next_point.y, 
                                      fill="green", width=2, dash=(5, 5))
        
        # 繪製A和B點（特別標記）
        if self.debug_A:
            self.canvas.create_oval(self.debug_A.x-8, self.debug_A.y-8, 
                                  self.debug_A.x+8, self.debug_A.y+8, 
                                  outline="purple", width=3, fill="yellow")
            self.canvas.create_text(self.debug_A.x, self.debug_A.y-15, text="A", 
                                  fill="purple", font=("Arial", 12, "bold"))
        
        if self.debug_B:
            self.canvas.create_oval(self.debug_B.x-8, self.debug_B.y-8, 
                                  self.debug_B.x+8, self.debug_B.y+8, 
                                  outline="purple", width=3, fill="yellow")
            self.canvas.create_text(self.debug_B.x, self.debug_B.y-15, text="B", 
                                  fill="purple", font=("Arial", 12, "bold"))
        
        # 繪製AB連線（上切線）
        if self.debug_A and self.debug_B:
            self.canvas.create_line(self.debug_A.x, self.debug_A.y, 
                                  self.debug_B.x, self.debug_B.y, 
                                  fill="purple", width=3)

    #照步驟執行   
    def step_voronoi(self):
        # 執行一步 merge，顯示左右子問題
        pass
    

    #讀檔
    def load_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.groups = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line=="0":
                break  # 如果遇到 "0" 則停止讀取
            if not line or line.startswith("#"):
                i += 1
                continue
            try:
                count = int(line)
                i += 1
            except ValueError:
                messagebox.showwarning("Warning", "Invalid point count at line {i+1}")
                i += 1
                continue
            
            group = []
            for _ in range(count):
                if i >= len(lines):
                    messagebox.showwarning("Warning", f"File ended prematurely, expected {count} points")
                    break
                parts = lines[i].strip().split()
                if len(parts) == 2:
                    try:
                        x, y = int(parts[0]), int(parts[1])
                        if 0 <= x <= 600 and 0 <= y <= 600:  # 檢查座標是否在畫布範圍內
                            group.append((x, y))
                        else:
                            messagebox.showwarning("Warning", f"Point ({parts[0]}, {parts[1]}) at line {i+1} out of canvas bounds")
                    except ValueError:
                        messagebox.showwarning("Warning", f"Invalid coordinates at line {i+1}")
                i += 1
            if group:  # 僅加入非空的 group
                self.groups.append(group)
            else:
                messagebox.showwarning("Warning", f"Empty group skipped at line {i-count}")
        
        if not self.groups:
            messagebox.showerror("Error", "No valid groups loaded from file")
            self.points = []
            self.current_group = 0
            return
        
        self.current_group = 0
        self.show_group()

    def show_group(self):
        self.clear_points()
        #print(f"Current group: {self.current_group}, Total groups: {len(self.groups)}")  # debug
        if 0 <= self.current_group < len(self.groups):
            self.points = self.groups[self.current_group][:]  # 複製列表以避免意外修改
            print(f"Points in current group: {self.points}")  # debug
            for x, y in self.points:
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")
                self.vd.add_point(Point(x, y))  # 添加到 self.vd
        else:
            #print("Invalid group index or no groups available.")
            self.points = []
            messagebox.showinfo("Info", "No points to display in current group")

    def next_group(self):
        if self.current_group + 1 < len(self.groups):
            self.current_group += 1
            self.show_group()
        else:
            messagebox.showinfo("Info", "No more groups to display")

    def prev_group(self):
        if self.current_group > 0:
            self.current_group -= 1
            self.show_group()
        else:
            messagebox.showinfo("Info", "Already at the first group")

    def clear_points(self):
        self.vd.points.clear()       # 清空點
        self.vd.edges.clear()        # 清空邊
        self.vd.vertices.clear()     # 清空頂點
        self.vd.point_to_edges.clear()  # 清空點到邊的映射
        self.points.clear()
        # 清空調試信息
        self.debug_left_hull.clear()
        self.debug_right_hull.clear()
        self.debug_A = None
        self.debug_B = None
        self.canvas.delete("all")
        self.canvas.configure(bg="white")

root = tk.Tk()
app = VoronoiGUI(root)
root.mainloop()