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
    def __init__(self, site1, site2, is_hyperplane=False):
        self.site1 = site1  # 平分的第一個點
        self.site2 = site2  # 平分的第二個點
        self.start_vertex = None
        self.end_vertex = None
        self.is_infinite = False
        self.is_hyperplane = is_hyperplane  # 標記是否為hyperplane（midAB線段）
        self.slope = self._calculate_slope()  # 中垂線的斜率
        self.midpoint = self._calculate_midpoint()  # 中垂線經過的中點
        
        # 新增：碰撞相關屬性
        self.is_cross = False  # 標記是否被hyperplane碰撞
        self.cross_point = None  # 記錄碰撞點
        self.intersected_by_hyperplane = None  # 記錄被哪條hyperplane碰撞
    
    # ...existing code...
    
    def set_cross_info(self, cross_point, hyperplane):
        """設置碰撞信息"""
        self.is_cross = True
        self.cross_point = cross_point
        self.intersected_by_hyperplane = hyperplane
    
    def get_point_value_in_hyperplane_equation(self, point, hyperplane):
        """計算點在hyperplane直線方程式中的值"""
        if hyperplane.slope == float('inf'):
            # 垂直線: x = c
            # 方程式可以寫成 x - c = 0
            c = hyperplane.midpoint.x
            return point.x - c
        else:
            # 一般直線: y = mx + b，重寫為 mx - y + b = 0
            m = hyperplane.slope
            b = hyperplane.midpoint.y - m * hyperplane.midpoint.x
            return m * point.x - point.y + b
    
    def _calculate_slope(self):
        """計算中垂線的斜率"""
        dx = self.site2.x - self.site1.x
        dy = self.site2.y - self.site1.y
        
        if dx == 0:
            # 原線段垂直，中垂線水平，斜率為 0
            return 0
        elif dy == 0:
            # 原線段水平，中垂線垂直，斜率為無限大
            return float('inf')
        else:
            # 中垂線斜率 = -(原線段斜率的倒數) = -dx/dy
            return -dx / dy
    
    def _calculate_midpoint(self):
        """計算兩點的中點"""
        mx = (self.site1.x + self.site2.x) / 2
        my = (self.site1.y + self.site2.y) / 2
        return Point(mx, my)

    def set_start_vertex(self, vertex):
        self.start_vertex = vertex
        vertex.add_edge(self)

    def set_end_vertex(self, vertex):
        self.end_vertex = vertex
        vertex.add_edge(self)

    def set_infinite(self):
        self.is_infinite = True
    
    def get_slope_info(self):
        """獲取斜率資訊"""
        if self.slope == float('inf'):
            return "垂直線（斜率無限大）"
        elif self.slope == 0:
            return "水平線（斜率為 0）"
        else:
            return f"斜率: {self.slope:.4f}"
    
    def get_bisected_points(self):
        """獲取被平分的兩個點"""
        return (self.site1, self.site2)
    
    def get_line_equation(self):
        """獲取中垂線方程式 y = mx + b 或 x = c"""
        if self.slope == float('inf'):
            # 垂直線: x = midpoint.x
            return f"x = {self.midpoint.x}"
        else:
            # y = mx + b，其中 b = midpoint.y - slope * midpoint.x
            b = self.midpoint.y - self.slope * self.midpoint.x
            if b >= 0:
                return f"y = {self.slope:.4f}x + {b:.4f}"
            else:
                return f"y = {self.slope:.4f}x - {abs(b):.4f}"
    
    def find_intersection(self, other_edge):
        """找到兩條中垂線的交點"""
        # 如果兩條線都是垂直線
        if self.slope == float('inf') and other_edge.slope == float('inf'):
            return None  # 平行線，無交點
        
        # 如果其中一條是垂直線
        if self.slope == float('inf'):
            x = self.midpoint.x
            # 計算 other_edge 在 x 處的 y 值
            b2 = other_edge.midpoint.y - other_edge.slope * other_edge.midpoint.x
            y = other_edge.slope * x + b2
            return Point(x, y)
        
        if other_edge.slope == float('inf'):
            x = other_edge.midpoint.x
            # 計算 self 在 x 處的 y 值
            b1 = self.midpoint.y - self.slope * self.midpoint.x
            y = self.slope * x + b1
            return Point(x, y)
        
        # 兩條線都不是垂直線
        # 計算 y = m1*x + b1 和 y = m2*x + b2 的交點
        b1 = self.midpoint.y - self.slope * self.midpoint.x
        b2 = other_edge.midpoint.y - other_edge.slope * other_edge.midpoint.x
        
        # 如果斜率相同，則平行
        if abs(self.slope - other_edge.slope) < 1e-10:
            return None
        
        # 求交點：m1*x + b1 = m2*x + b2 → x = (b2-b1)/(m1-m2)
        x = (b2 - b1) / (self.slope - other_edge.slope)
        y = self.slope * x + b1
        
        return Point(x, y)
    
    def is_point_between_vertices(self, point):
        """檢查點是否在線段的兩個端點之間"""
        if not self.start_vertex or not self.end_vertex:
            return False
        
        # 檢查點是否在線段的範圍內
        min_x = min(self.start_vertex.x, self.end_vertex.x)
        max_x = max(self.start_vertex.x, self.end_vertex.x)
        min_y = min(self.start_vertex.y, self.end_vertex.y)
        max_y = max(self.start_vertex.y, self.end_vertex.y)
        
        # 給一點容差以避免浮點數精度問題
        tolerance = 1e-6
        return (min_x - tolerance <= point.x <= max_x + tolerance and 
                min_y - tolerance <= point.y <= max_y + tolerance)


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

    #計算中垂線(不受畫框限制)
    @staticmethod
    def get_perpendicular_bisector_unlimited(p1, p2, extend_length=2000):
        """
        計算中垂線的兩個端點，不受畫框限制
        extend_length: 從中點向兩個方向延伸的長度
        """
        # 計算中垂線的中點
        mx = (p1.x + p2.x) / 2
        my = (p1.y + p2.y) / 2
        dx = p2.x - p1.x
        dy = p2.y - p1.y

        if dx == 0:
            # 垂直線的中垂線是水平線
            return (VoronoiVertex(mx - extend_length, my), VoronoiVertex(mx + extend_length, my))
        elif dy == 0:
            # 水平線的中垂線是垂直線
            return (VoronoiVertex(mx, my - extend_length), VoronoiVertex(mx, my + extend_length))
        else:
            # 計算中垂線的方向向量（垂直於原線段）
            slope = -dx / dy
            # 單位方向向量
            direction_x = 1
            direction_y = slope
            # 歸一化
            length = (direction_x**2 + direction_y**2) ** 0.5
            direction_x /= length
            direction_y /= length
            
            # 計算兩個端點：從中點向兩個方向延伸
            start_x = mx - direction_x * extend_length
            start_y = my - direction_y * extend_length
            end_x = mx + direction_x * extend_length
            end_y = my + direction_y * extend_length
            
            return (VoronoiVertex(start_x, start_y), VoronoiVertex(end_x, end_y))


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

    def extend(self,points):
        pass
    
    def remove_edge_extension_beyond_point(self, edge, cut_point):
        """移除邊在指定點之外的延伸部分"""
        if not edge.start_vertex or not edge.end_vertex:
            return
        
        # 計算哪個端點離 cut_point 更遠
        dist_to_start = ((cut_point.x - edge.start_vertex.x)**2 + 
                        (cut_point.y - edge.start_vertex.y)**2) ** 0.5
        dist_to_end = ((cut_point.x - edge.end_vertex.x)**2 + 
                      (cut_point.y - edge.end_vertex.y)**2) ** 0.5
        
        # 保留較近的端點，用 cut_point 替換較遠的端點
        if dist_to_start > dist_to_end:
            edge.start_vertex = VoronoiVertex(cut_point.x, cut_point.y)
        else:
            edge.end_vertex = VoronoiVertex(cut_point.x, cut_point.y)


