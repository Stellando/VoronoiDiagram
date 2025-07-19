import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

#資料結構部分
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class VoronoiVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edges = []  # 連接到這個 vertex 的中垂線列表

    def add_edge(self, edge):
        self.edges.append(edge)

class VoronoiEdge:
    def __init__(self, site1, site2):
        self.site1 = site1
        self.site2 = site2
        self.start_vertex = None
        self.end_vertex = None
        self.is_infinite = False

    def set_start_vertex(self, vertex):
        self.start_vertex = vertex
        vertex.add_edge(self)

    def set_end_vertex(self, vertex):
        self.end_vertex = vertex
        vertex.add_edge(self)

    def set_infinite(self):
        self.is_infinite = True


    #計算中垂線
    @staticmethod
    def get_perpendicular_bisector_on_canvas(p1, p2, canvas_width=600, canvas_height=600):
        # 計算中垂線的中點
        mx = (p1.x + p2.x) / 2
        my = (p1.y + p2.y) / 2
        dx = p2.x - p1.x
        dy = p2.y - p1.y

        if dx == 0:
            # 垂直線的中垂線是水平線
            return (VoronoiVertex(0, my), VoronoiVertex(canvas_width, my))
        elif dy == 0:
            # 水平線的中垂線是垂直線
            return (VoronoiVertex(mx, 0), VoronoiVertex(mx, canvas_height))
        else:
            slope = -dx / dy
            points_on_canvas = []
            # 與上邊界(y=0)和下邊界(y=canvas_height)求交
            x_top = mx + (0 - my) / slope
            x_bottom = mx + (canvas_height - my) / slope
            if 0 <= x_top <= canvas_width:
                points_on_canvas.append((x_top, 0))
            if 0 <= x_bottom <= canvas_width:
                points_on_canvas.append((x_bottom, canvas_height))
            # 與左邊界(x=0)和右邊界(x=canvas_width)求交
            y_left = my + slope * (0 - mx)
            y_right = my + slope * (canvas_width - mx)
            if 0 <= y_left <= canvas_height:
                points_on_canvas.append((0, y_left))
            if 0 <= y_right <= canvas_height:
                points_on_canvas.append((canvas_width, y_right))
            # 取兩個在畫布內的交點作為中垂線端點
            if len(points_on_canvas) >= 2:
                return (VoronoiVertex(*points_on_canvas[0]), VoronoiVertex(*points_on_canvas[1]))
            elif len(points_on_canvas) == 1:
                return (VoronoiVertex(mx, my), VoronoiVertex(*points_on_canvas[0]))
            else:
                return (VoronoiVertex(mx, my), VoronoiVertex(mx, my))

# 主資料結構
class VoronoiDiagram:
    def __init__(self):
        self.points = []          # 點的列表
        self.edges = []           # 中垂線的列表
        self.vertices = []        # Voronoi vertices 的列表
        self.point_to_edges = {}  # 點到中垂線的映射

    def add_point(self, point):
        self.points.append(point)
        self.point_to_edges[point] = []

    def add_edge(self, edge):
        self.edges.append(edge)
        # 更新點到中垂線的映射
        self.point_to_edges[edge.site1].append(edge)
        self.point_to_edges[edge.site2].append(edge)

    def add_vertex(self, vertex):
        self.vertices.append(vertex)


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
        if len(points) == 1:
            return vd  # 單點無需處理
        elif len(points) == 2:
            return self.build_voronoi_two_points(points)
        elif len(points) == 3:
            return self.build_voronoi_three_points(points)
        else:
            # Divide
            points.sort(key=lambda p: p.x)  # 按 x 座標排序
            mid = len(points) // 2
            left_points = points[:mid]
            right_points = points[mid:]
            
            # Conquer
            left_vd = self.build_voronoi(left_points)
            right_vd = self.build_voronoi(right_points)
            
            # Merge
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
        # 不共線，正常求三條中垂線
        vertex = self.calculate_circumcenter(p1, p2, p3)
        if vertex:
            # 計算三邊長
            def dist2(a, b):
                return (a.x - b.x)**2 + (a.y - b.y)**2
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
                    obtuse_idx = 0
                    obtuse_point = p1
                elif cosB < 0:
                    obtuse_idx = 1
                    obtuse_point = p2
                else:
                    obtuse_idx = 2
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
        merged_vd.points = left_vd  # 將左右點集合併
        merged_vd.points.extend(left_vd.points)
        merged_vd.points.extend(right_vd.points)
        
        # 合併邊和頂點（這裡僅為示例，實際需計算新的邊和頂點）
        merged_vd.edges.extend(left_vd.edges)
        merged_vd.edges.extend(right_vd.edges)
        merged_vd.vertices.extend(left_vd.vertices)
        merged_vd.vertices.extend(right_vd.vertices)
        
        # 簡化合併邏輯：找到左右子集之間的分界線並構建新的中垂線
        left_max_x = max(p.x for p in left_vd.points)
        right_min_x = min(p.x for p in right_vd.points)
        mid_x = (left_max_x + right_min_x) / 2
        
        # 這裡需要實現真正的合併鏈計算，暫時用簡單的分界線作為示例
        # 實際上需要追蹤左右 Voronoi Diagram 的邊界，構建新的邊和頂點
        
        return merged_vd
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
        self.canvas.delete("all")
        self.canvas.configure(bg="white")

root = tk.Tk()
app = VoronoiGUI(root)
root.mainloop()